from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies = db.Column(db.String(250), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    github_url = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<Project {self.id} {self.title}>"

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

def seed_projects():
    """Seeds default projects if the database table is empty."""
    if Project.query.count() == 0:
        for p in DEFAULT_PROJECTS:
            project = Project(
                title=p["title"],
                description=p["description"],
                technologies=p["technologies"],
                image_url=p["image_url"],
                github_url=p["github_url"]
            )
            db.session.add(project)
        db.session.commit()
