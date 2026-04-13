import sys
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from models import db
from models.user import User
from models.ride import Ride, RideParticipant, RideHistory
from models.fuel import FuelSettings
from models.chat import Message

def seed_data():
    app = create_app()
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        # 1. Create Sample Users
        print("Creating sample users...")
        pass_hash = generate_password_hash('password123', method='pbkdf2:sha256')
        
        users = [
            User(name='Rahul Sharma', email='rahul@srmcem.ac.in', phone='9876543210', gender='Male', student_id='SRM001', password_hash=pass_hash),
            User(name='Priya Verma', email='priya@srmcem.ac.in', phone='9876543211', gender='Female', student_id='SRM002', password_hash=pass_hash),
            User(name='Aman Gupta', email='aman@srmcem.ac.in', phone='9876543212', gender='Male', student_id='SRM003', password_hash=pass_hash),
            User(name='Neha Singh', email='neha@srmcem.ac.in', phone='9876543213', gender='Female', student_id='SRM004', password_hash=pass_hash, is_admin=True)
        ]
        for u in users:
            db.session.add(u)
        db.session.commit()

        # 2. Create Fuel Settings
        print("Creating fuel settings...")
        fuel = FuelSettings(current_price=96.72)
        db.session.add(fuel)
        db.session.commit()

        # 3. Create Sample Rides
        print("Creating sample rides...")
        now = datetime.utcnow()
        
        rides = [
            # Ride 1: To College from Gomti Nagar (Bike)
            Ride(driver_id=users[0].id, source='Gomti Nagar', destination='Ramswaroop College', 
                 date_time=now + timedelta(hours=2), seats_total=1, seats_available=0, 
                 vehicle_type='Bike (Splendor)', ride_type='to_college', cost_per_seat=25.0,
                 pickup_name='Mithai Wala Chauraha', pickup_lat='26.8467', pickup_lng='80.9462'),
            
            # Ride 2: From College to Indira Nagar (Car)
            Ride(driver_id=users[2].id, source='Ramswaroop College', destination='Indira Nagar', 
                 date_time=now + timedelta(hours=5), seats_total=4, seats_available=2, 
                 vehicle_type='Car (Swift)', ride_type='from_college', cost_per_seat=45.0,
                 pickup_name='College Main Gate', pickup_lat='26.8912', pickup_lng='81.0654'),
            
            # Ride 3: To College from Aliganj (Car)
            Ride(driver_id=users[3].id, source='Aliganj', destination='Ramswaroop College', 
                 date_time=now + timedelta(days=1, hours=1), seats_total=4, seats_available=4, 
                 vehicle_type='Car (i20)', ride_type='to_college', cost_per_seat=60.0,
                 pickup_name='Engineering College Chauraha', pickup_lat='26.9123', pickup_lng='80.9432'),
            
            # Ride 4: From College to Hazratganj (Bike)
            Ride(driver_id=users[1].id, source='Ramswaroop College', destination='Hazratganj', 
                 date_time=now + timedelta(days=1, hours=4), seats_total=1, seats_available=1, 
                 vehicle_type='Bike (Activa)', ride_type='from_college', cost_per_seat=35.0,
                 pickup_name='Canteen Area', pickup_lat='26.8910', pickup_lng='81.0650'),
            
            # Ride 5: To College from Bhootnath (Car) - Recurring
            Ride(driver_id=users[0].id, source='Bhootnath', destination='Ramswaroop College', 
                 date_time=now + timedelta(days=2, hours=1), seats_total=3, seats_available=3, 
                 vehicle_type='Car (City)', ride_type='to_college', is_recurring=True, recurrence_days='Mon-Fri', 
                 cost_per_seat=50.0, pickup_name='Bhootnath Market', pickup_lat='26.8812', pickup_lng='80.9912')
        ]
        
        for r in rides:
            db.session.add(r)
        db.session.commit()

        # 4. Create Participants
        print("Adding participants...")
        # Priya joined Rahul's Ride 1
        p1 = RideParticipant(ride_id=rides[0].id, user_id=users[1].id, status='accepted')
        # Rahul joined Aman's Ride 2
        p2 = RideParticipant(ride_id=rides[1].id, user_id=users[0].id, status='accepted')
        # Neha joined Aman's Ride 2
        p3 = RideParticipant(ride_id=rides[1].id, user_id=users[3].id, status='accepted')
        
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        # 5. Create Sample Chat Messages
        print("Adding sample messages...")
        m1 = Message(ride_id=rides[1].id, sender_id=users[2].id, message_text="Hey guys, wait for me at the gate at 4:30 PM.")
        m2 = Message(ride_id=rides[1].id, sender_id=users[0].id, message_text="Sure Aman, I'll be there on time.")
        db.session.add_all([m1, m2])
        db.session.commit()

        # 6. Create one COMPLETED Ride for Savings Display
        print("Creating a completed ride and history...")
        completed_ride = Ride(driver_id=users[2].id, source='Aliganj', destination='Ramswaroop College', 
                              date_time=now - timedelta(days=1), seats_total=4, seats_available=0, 
                              vehicle_type='Car (Swift)', ride_type='to_college', status='completed',
                              cost_per_seat=50.0, pickup_name='Aliganj Sector H')
        db.session.add(completed_ride)
        db.session.commit()
        
        # History for Rahul (who was a passenger)
        h1 = RideHistory(user_id=users[0].id, ride_id=completed_ride.id, distance=18.5, 
                         solo_cost=150.0, shared_cost=50.0, savings=100.0, date=now - timedelta(days=1))
        # History for Aman (who was the driver)
        h2 = RideHistory(user_id=users[2].id, ride_id=completed_ride.id, distance=18.5, 
                         solo_cost=150.0, shared_cost=50.0, savings=100.0, date=now - timedelta(days=1))
        
        db.session.add_all([h1, h2])
        db.session.commit()

        print("\n--- Sample Data Seeded Successfully! ---")
        print(f"Sample Users (Password for all: password123):")
        for u in users:
            print(f" - {u.name} ({u.email})")

if __name__ == "__main__":
    seed_data()
