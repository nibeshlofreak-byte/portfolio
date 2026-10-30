from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(50), default='professor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies = db.Column(db.String(250), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    github_url = db.Column(db.String(500), nullable=True)
    
    # Relationship to evaluations
    evaluations = db.relationship('Evaluation', backref='project', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Project {self.id} {self.title}>"

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    evaluator_name = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=10)
    status = db.Column(db.String(50), nullable=False, default='Approved')  # Approved, Outstanding, In Review
    architecture_feedback = db.Column(db.Text, nullable=True)
    code_quality_feedback = db.Column(db.Text, nullable=True)
    general_comments = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Evaluation Project={self.project_id} Score={self.score}>"

DEFAULT_PROJECTS = [
    {
        "id": 1,
        "title": "PharmaPOS – Multi-Branch POS & FEFO Analytics",
        "description": "Enterprise Pharmacy Point-of-Sale (POS) and inventory management system built with Python. Features multi-branch synchronization, strict FEFO (First Expired, First Out) batch deduction, bcrypt RBAC security, real-time KPI metrics with interactive Matplotlib charts, and thermal ticket printing.",
        "technologies": "Python, Tkinter, Matplotlib, SQLite, MySQL, Bcrypt, FEFO Algorithm",
        "image_url": "/static/img/pharmacy_pos.png",
        "github_url": "https://github.com/nibeshlofreak-byte/portfolio/tree/main/projects/pharmacy-pos"
    },
    {
        "id": 2,
        "title": "FormIA – AI-Powered Smart Form & Local LLM Assistant",
        "description": "Intelligent web platform integrating dynamic multi-attribute form validation with on-device private AI (Ollama + Qwen2.5). Generates synthetic testing profiles on-demand with Faker and features a conversational assistant for profile inquiries and data analytics.",
        "technologies": "Python, Flask, Ollama, Qwen2.5, MySQL, SQL Server, Faker, JavaScript",
        "image_url": "/static/img/formia_ai.svg",
        "github_url": "https://github.com/nibeshlofreak-byte/portfolio/tree/main/projects/formia-ai-form"
    },
    {
        "id": 3,
        "title": "Lotus – Gaming & eSports Tournament Platform",
        "description": "Cross-platform desktop and mobile eSports platform built using Python and Flet (Flutter rendering engine). Supports custom tournament bracket creation, live streaming viewer simulation, gamer community hubs, and dual online FastAPI / offline cryptographic authentication.",
        "technologies": "Python, Flet, FastAPI, Uvicorn, MySQL, Pydantic, HTTPX, Cryptography",
        "image_url": "/static/img/lotus_esports.png",
        "github_url": "https://github.com/nibeshlofreak-byte/portfolio/tree/main/projects/lotus-esports"
    }
]

def seed_database():
    """Seeds default projects and a default professor account if missing."""
    # Seed projects
    if Project.query.count() == 0:
        for p in DEFAULT_PROJECTS:
            project = Project(
                id=p["id"],
                title=p["title"],
                description=p["description"],
                technologies=p["technologies"],
                image_url=p["image_url"],
                github_url=p["github_url"]
            )
            db.session.add(project)
        db.session.commit()

    # Seed default professor user
    if User.query.filter_by(username='professor').first() is None:
        prof = User(
            username='professor',
            email='evaluator@tsds.edu',
            full_name='Prof. Academic Evaluator',
            role='professor'
        )
        prof.set_password('prof2026')
        db.session.add(prof)
        db.session.commit()

    # Seed sample evaluation if none exists
    if Evaluation.query.count() == 0:
        first_proj = Project.query.first()
        if first_proj:
            sample_eval = Evaluation(
                project_id=first_proj.id,
                evaluator_name="Prof. Academic Evaluator",
                score=10,
                status="Outstanding",
                architecture_feedback="Excellent multi-branch separation and clear layered architecture (UI, Services, DB).",
                code_quality_feedback="Clean Python code structure with robust FEFO inventory algorithm implementation.",
                general_comments="High-standard practical project demonstrating real-world technical and domain competency."
            )
            db.session.add(sample_eval)
            db.session.commit()
