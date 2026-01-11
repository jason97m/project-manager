from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# Association tables for many-to-many relationships
program_contacts = db.Table('program_contacts',
    db.Column('program_id', db.Integer, db.ForeignKey('program.id'), primary_key=True),
    db.Column('contact_id', db.Integer, db.ForeignKey('contact.id'), primary_key=True)
)

project_contacts = db.Table('project_contacts',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('contact_id', db.Integer, db.ForeignKey('contact.id'), primary_key=True)
)

task_contacts = db.Table('task_contacts',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('contact_id', db.Integer, db.ForeignKey('contact.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    programs = db.relationship('Program', backref='owner', lazy=True, cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='owner', lazy=True, cascade='all, delete-orphan')
    contacts = db.relationship('Contact', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Contact(db.Model):
    """Contact/People model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Contact {self.name}>'


class Program(db.Model):
    """Program model - top level container"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Planning')  # Planning, Active, Completed, On Hold
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='program', lazy=True, cascade='all, delete-orphan')
    materials = db.relationship('Material', backref='program', lazy=True, cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='program', lazy=True, cascade='all, delete-orphan')
    assigned_contacts = db.relationship('Contact', secondary=program_contacts, backref='programs')
    
    def __repr__(self):
        return f'<Program {self.name}>'


class Project(db.Model):
    """Project model - can be standalone or part of a program"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=True)  # NULL if standalone
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Planning')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    materials = db.relationship('Material', backref='project', lazy=True, cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='project', lazy=True, cascade='all, delete-orphan')
    assigned_contacts = db.relationship('Contact', secondary=project_contacts, backref='projects')
    
    def __repr__(self):
        return f'<Project {self.name}>'


class Task(db.Model):
    """Task model - subtasks within projects"""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Not Started')  # Not Started, In Progress, Completed, Blocked
    priority = db.Column(db.String(20), default='Medium')  # Low, Medium, High, Critical
    completion_percentage = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('Material', backref='task', lazy=True, cascade='all, delete-orphan')
    assigned_contacts = db.relationship('Contact', secondary=task_contacts, backref='tasks')
    
    def __repr__(self):
        return f'<Task {self.name}>'


class Milestone(db.Model):
    """Milestone model - can be attached to programs or projects"""
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    target_date = db.Column(db.Date, nullable=False)
    achieved = db.Column(db.Boolean, default=False)
    achieved_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Milestone {self.name}>'


class Material(db.Model):
    """Material model - can be attached to programs, projects, or tasks"""
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Float, default=1.0)
    unit = db.Column(db.String(50))  # e.g., "units", "kg", "hours"
    cost_per_unit = db.Column(db.Float)
    supplier = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def total_cost(self):
        if self.cost_per_unit and self.quantity:
            return self.cost_per_unit * self.quantity
        return 0.0
    
    def __repr__(self):
        return f'<Material {self.name}>'
