from flask_sqlalchemy import SQLAlchemy

# db will be initialized in app.py

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
