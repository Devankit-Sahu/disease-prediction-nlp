from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.Enum('user', 'doctor', name='user_roles'), nullable=False, default='user')
    speciality = db.Column(db.String(150), nullable=True)
    available_time = db.Column(db.String(), nullable=True)

    def __init__(self,email,name,password,role):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.role = role

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)
    

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(150), nullable=False)
    time = db.Column(db.String(150), nullable=False)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', name='appointment_status'), nullable=False, default='pending')
    user = db.relationship('User', foreign_keys=[user_id], backref='user_appointments')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_appointments')

    def __init__(self, user_id, doctor_id, date, time):
        self.user_id = user_id
        self.doctor_id = doctor_id
        self.date = date
        self.time = time
    

    

        
