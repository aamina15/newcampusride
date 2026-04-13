from datetime import datetime
from models import db

class Ride(db.Model):
    __tablename__ = 'rides'
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    seats_total = db.Column(db.Integer, nullable=False)
    seats_available = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    ride_type = db.Column(db.String(20), nullable=False, default='to_college') # 'to_college', 'from_college'
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_days = db.Column(db.String(50), nullable=True) # e.g. "Mon-Fri"
    cost_per_seat = db.Column(db.Float, nullable=True) # Can be calculated or manual
    circle_id = db.Column(db.Integer, db.ForeignKey('ride_circles.id'), nullable=True)
    is_female_only = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='upcoming') # upcoming, completed, cancelled
    pickup_name = db.Column(db.String(255), nullable=True)
    pickup_lat = db.Column(db.String(50), nullable=True)
    pickup_lng = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    participants = db.relationship('RideParticipant', backref='ride', lazy=True, cascade="all, delete-orphan")
    messages = db.relationship('Message', backref='ride', lazy=True, cascade="all, delete-orphan")

class RideParticipant(db.Model):
    __tablename__ = 'ride_participants'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, accepted, declined
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='ride_participations')

class RideHistory(db.Model):
    __tablename__ = 'ride_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    distance = db.Column(db.Float, nullable=False, default=15.0) # default demo dist
    solo_cost = db.Column(db.Float, nullable=False)
    shared_cost = db.Column(db.Float, nullable=False)
    savings = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='ride_histories')
    ride = db.relationship('Ride', backref='history_records')
