from flask_security import UserMixin, RoleMixin
import  os, sys, uuid
from core.database import db
from datetime import datetime, UTC

# Association table
# Primary key on user_id ensures one role per user.
user_roles = db.Table(
    'user_roles',
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.id'),
        primary_key=True
    ),
    db.Column(
        'role_id',
        db.Integer,
        db.ForeignKey('roles.id'),
        nullable=False
    )
)

courses_examiners = db.Table(
    'courses_examiners',
    db.Column(
        'course_id',
        db.Integer,
        db.ForeignKey('courses.id'),
        primary_key=True
    ),
    db.Column(
        'examiner_id',
        db.Integer,
        db.ForeignKey('examiner_profiles.id'),
        primary_key=True
    )
)

class User(db.Model, UserMixin): 
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending', server_default='pending')
    active = db.Column(db.Boolean(), default=True)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False, default=lambda:str(uuid.uuid4()))

    roles = db.relationship(
        'Role',
        secondary=user_roles,
        backref=db.backref('users', lazy='dynamic')
    )

class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable = False)
    description = db.Column(db.String(255))

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(255), nullable = False)
    program = db.Column(db.String(255), nullable = False)
    semester = db.Column(db.String(20), nullable = False)
    year_of_study = db.Column(db.Integer, nullable = False)

    user = db.relationship(
    'User',
    backref=db.backref('student_profile', uselist=False)
    )

     
      

class ExaminerProfile(db.Model): 
    __tablename__ = 'examiner_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    department = db.Column(db.String(255), nullable = False)
    designation = db.Column(db.String(255), nullable = False) 

    courses = db.relationship(
    'Course',
    secondary=courses_examiners,
    backref=db.backref('examiners', lazy='dynamic')
)
    user = db.relationship(
    'User',
    backref=db.backref('examiner_profile', uselist=False)
)

class Course(db.Model): 
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    credits = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(255), nullable=False)
    program = db.Column(db.String(255), nullable=False)

    semester = db.Column(db.String(20), nullable=False)
    year_of_study = db.Column(db.Integer, nullable=False)