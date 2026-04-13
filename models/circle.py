from datetime import datetime
from models import db
import string
import random

def generate_invite_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

class RideCircle(db.Model):
    __tablename__ = 'ride_circles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invite_code = db.Column(db.String(20), unique=True, default=generate_invite_code)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('CircleMember', backref='circle', lazy=True, cascade="all, delete-orphan")
    rides = db.relationship('Ride', backref='circle', lazy=True)

class CircleMember(db.Model):
    __tablename__ = 'circle_members'
    id = db.Column(db.Integer, primary_key=True)
    circle_id = db.Column(db.Integer, db.ForeignKey('ride_circles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='circle_memberships')
