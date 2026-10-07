from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import datetime

db = SQLAlchemy()

subject_professor = db.Table('subject_professor',
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True),
    db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_professor = db.Column(db.Boolean, default=False)
    is_student = db.Column(db.Boolean, default=False)
    # student/professor one-to-one relationships
    student = db.relationship('Student', backref='user', uselist=False)
    professor = db.relationship('Professor', backref='user', uselist=False)

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def role(self):
        if self.is_admin:
            return 'admin'
        elif self.is_professor:
            return 'professor'
        elif self.is_student:
            return 'student'
        return 'user'

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    rfid_tag = db.Column(db.String(50), unique=True, nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    suffix = db.Column(db.String(10), nullable=True)
    parent_contact = db.Column(db.String(20), nullable=False)
    enrollment_status = db.Column(db.String(20), nullable=False)
    face_images = db.Column(db.Text, nullable=True)
    face_encoding = db.Column(db.PickleType, nullable=True)
    # Attendance relationship (one-to-many)
    attendances = db.relationship('Attendance', backref='student', lazy=True)

    def __repr__(self):
        return f"<Student {self.student_id} - {self.last_name}, {self.first_name}>"

class Professor(db.Model):
    __tablename__ = 'professor'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    suffix = db.Column(db.String(10))
    # Relationship to subjects
    subjects = db.relationship('Subject', backref='professor_obj', lazy=True)

    def __repr__(self):
        return f"<Professor {self.last_name}, {self.first_name}>"

class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=True)
    attendances = db.relationship('Attendance', backref='subject', lazy=True)
    
    def __repr__(self):
        return f"<Subject {self.name}>"

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    timestamp = db.Column(db.DateTime)
    status = db.Column(db.String(20))
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)

    def __repr__(self):
        return f"<Attendance Student={self.student_id} Time={self.timestamp} Status={self.status}>"
