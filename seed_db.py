import random
from datetime import datetime, timedelta
from app import create_app
from models import db
from models.user import User
from models.ride import Ride
from models.fuel import FuelSettings
from werkzeug.security import generate_password_hash

app = create_app()

def seed_database():
    with app.app_context():
        print("Dropping all tables to rebuild schema...")
        db.drop_all()
        db.create_all()
        
        print("Seeding Fuel Settings...")
        fuel = FuelSettings(current_price=96.50, last_updated=datetime.utcnow() - timedelta(days=5))
        db.session.add(fuel)
        
        print("Creating dummy users...")
        users = []
        
        # Admin User
        admin_user = User(
            name='Platform Admin',
            email='admin@university.edu',
            phone='555-0000',
            gender='Other',
            student_id='ADMIN_001',
            password_hash=generate_password_hash('password123', method='pbkdf2:sha256'),
            is_admin=True
        )
        db.session.add(admin_user)
        
        # Normal Users
        for i in range(1, 4):
            user = User(
                name=f'Demo Student {i}',
                email=f'demo{i}@university.edu',
                phone=f'555-010{i}',
                gender='Male' if i != 2 else 'Female',
                student_id=f'DEMO{i}000',
                password_hash=generate_password_hash('password123', method='pbkdf2:sha256')
            )
            db.session.add(user)
            users.append(user)
            
        db.session.commit()
        
        print("Creating dummy college daily commutes...")
        localities = ['Aliganj', 'Gomti Nagar', 'Indira Nagar', 'Hazratganj', 'Mahanagar', 'Kapurthala']
        
        # 10 Rides
        for i in range(10):
            locality = random.choice(localities)
            ride_type = random.choice(['to_college', 'from_college'])
            
            if ride_type == 'to_college':
                src = locality
                dest = "Ramswaroop College"
            else:
                src = "Ramswaroop College"
                dest = locality
            
            # Times between 1 to 48 hours from now
            hours_ahead = random.randint(1, 48)
            ride_time = datetime.utcnow() + timedelta(hours=hours_ahead)
            
            is_recurring = random.choice([True, False])
            
            ride = Ride(
                driver_id=random.choice(users).id,
                source=src,
                destination=dest,
                date_time=ride_time,
                seats_total=3,
                seats_available=random.randint(1, 3),
                vehicle_type='Car (Sedan)',
                ride_type=ride_type,
                is_recurring=is_recurring,
                recurrence_days='Mon-Fri' if is_recurring else None,
                cost_per_seat=random.randint(15, 60),
                is_female_only=False
            )
            db.session.add(ride)
            
        db.session.commit()
        print("Successfully rebuilt DB, initialized the fuel pool with INR, and seeded 10 college commute rides!")

if __name__ == '__main__':
    seed_database()
