from flask import Flask, render_template
from config import Config
from models import db, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Import blueprints (to be created)
    from controllers.auth_controller import auth_bp
    from controllers.ride_controller import ride_bp
    from controllers.circle_controller import circle_bp
    from controllers.admin_controller import admin_bp
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ride_bp, url_prefix='/rides')
    app.register_blueprint(circle_bp, url_prefix='/circles')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.context_processor
    def inject_fuel_settings():
        from models.fuel import FuelSettings
        from datetime import datetime
        fuel_settings = FuelSettings.query.first()
        return dict(fuel_settings=fuel_settings, now=datetime.utcnow())

    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('ride.dashboard'))
        return render_template('index.html')

    with app.app_context():
        # Import models so SQLAlchemy knows about them
        from models.user import User
        from models.ride import Ride, RideParticipant, RideHistory
        from models.circle import RideCircle, CircleMember
        from models.chat import Message
        from models.fuel import FuelSettings
        
        # Create tables if they don't exist
        db.create_all()

    @app.route('/seed-data')
    def trigger_seed():
        # Temporary developer route for demo convenience
        from seed_all import seed_data
        try:
            seed_data()
            return "Database seeded successfully with sample CampusRide data! Go to /auth/login"
        except Exception as e:
            return f"Seeding failed: {str(e)}"

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
