import os
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, 
    url_for, session, flash, send_from_directory
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', 'cosmic_portfolio_evaluation_key_2026')

# Database configuration – supports MySQL or SQLite fallback
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

if (DB_USER and DB_PASSWORD and DB_NAME and 
    DB_USER not in ('tu_usuario', 'your_user') and 
    DB_PASSWORD not in ('tu_contraseña', 'your_password')):
    # MySQL connection URL
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
else:
    # SQLite fallback for seamless local execution
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, Project, Evaluation, DEFAULT_PROJECTS, seed_database
db.init_app(app)

# Inject authentication status into all templates
@app.context_processor
def inject_auth():
    return {
        'is_logged_in': 'user_id' in session,
        'current_user_name': session.get('full_name') or session.get('username'),
        'current_user_role': session.get('role')
    }

# Decorator to protect professor / evaluator routes
def professor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in with academic credentials to access the Evaluator Portal.', 'info')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/projects')
def projects():
    try:
        all_projects = Project.query.order_by(Project.id).all()
        if not all_projects:
            seed_database()
            all_projects = Project.query.order_by(Project.id).all()
    except Exception:
        all_projects = DEFAULT_PROJECTS

    return render_template('projects.html', projects=all_projects)

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ==========================================
# TEACHER / EVALUATOR AUTHENTICATION ROUTES
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('evaluator_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter((User.username == username) | (User.email == username)).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name or user.username
            session['role'] = user.role
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            next_page = request.args.get('next') or url_for('evaluator_dashboard')
            return redirect(next_page)
        else:
            flash('Invalid username or password. Please verify the credentials.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been securely signed out.', 'info')
    return redirect(url_for('index'))

# ==========================================
# PROFESSOR EVALUATION DASHBOARD
# ==========================================

@app.route('/evaluator')
@professor_required
def evaluator_dashboard():
    all_projects = Project.query.order_by(Project.id).all()
    all_evaluations = Evaluation.query.order_by(Evaluation.created_at.desc()).all()
    
    # Calculate statistics
    total_evals = len(all_evaluations)
    avg_score = round(sum(e.score for e in all_evaluations) / total_evals, 1) if total_evals > 0 else 0

    return render_template(
        'evaluator.html',
        projects=all_projects,
        evaluations=all_evaluations,
        total_evals=total_evals,
        avg_score=avg_score
    )

@app.route('/evaluator/submit/<int:project_id>', methods=['POST'])
@professor_required
def submit_evaluation(project_id):
    project = Project.query.get_or_404(project_id)
    
    score = request.form.get('score', type=int) or 10
    status = request.form.get('status', 'Approved')
    architecture_feedback = request.form.get('architecture_feedback', '').strip()
    code_quality_feedback = request.form.get('code_quality_feedback', '').strip()
    general_comments = request.form.get('general_comments', '').strip()

    if not general_comments:
        flash('Please include general feedback or evaluation remarks.', 'warning')
        return redirect(url_for('evaluator_dashboard'))

    evaluator_name = session.get('full_name') or session.get('username') or 'Academic Evaluator'

    evaluation = Evaluation(
        project_id=project.id,
        evaluator_name=evaluator_name,
        score=score,
        status=status,
        architecture_feedback=architecture_feedback,
        code_quality_feedback=code_quality_feedback,
        general_comments=general_comments
    )
    db.session.add(evaluation)
    db.session.commit()

    flash(f'Evaluation submitted successfully for "{project.title}".', 'success')
    return redirect(url_for('evaluator_dashboard'))

@app.route('/evaluator/delete/<int:evaluation_id>', methods=['POST'])
@professor_required
def delete_evaluation(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    db.session.delete(evaluation)
    db.session.commit()
    flash('Evaluation record removed.', 'info')
    return redirect(url_for('evaluator_dashboard'))

# Static files route
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            seed_database()
        except Exception as e:
            print(f"Database initialization notice: {e}")
            
    app.run(debug=True, host='0.0.0.0', port=5000)
