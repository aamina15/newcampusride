from datetime import datetime
from models import db

class FuelSettings(db.Model):
    __tablename__ = 'fuel_settings'
    id = db.Column(db.Integer, primary_key=True)
    current_price = db.Column(db.Float, nullable=False, default=96.0) # INR per litre
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
