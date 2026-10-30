import os
from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Database configuration – supports MySQL or SQLite fallback
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

# Check if valid MySQL credentials are provided (ignoring placeholder values)
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

from models import db, Project, DEFAULT_PROJECTS, seed_projects
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/projects')
def projects():
    # Retrieve all projects ordered by id, with fallback
    try:
        all_projects = Project.query.order_by(Project.id).all()
        if not all_projects:
            seed_projects()
            all_projects = Project.query.order_by(Project.id).all()
    except Exception:
        all_projects = DEFAULT_PROJECTS

    return render_template('projects.html', projects=all_projects)

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Static files route
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    # Initialize tables and seed default projects if needed
    with app.app_context():
        try:
            db.create_all()
            seed_projects()
        except Exception as e:
            print(f"Database initialization notice: {e}")
            
    app.run(debug=True, host='0.0.0.0', port=5000)
