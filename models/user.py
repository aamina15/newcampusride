from datetime import datetime
from flask_login import UserMixin
from models import db, login_manager

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    rides_offered = db.relationship('Ride', backref='driver', lazy=True)
    circles_created = db.relationship('RideCircle', backref='creator', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
