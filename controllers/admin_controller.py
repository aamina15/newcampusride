from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.fuel import FuelSettings
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'error')
        return redirect(url_for('ride.dashboard'))

@admin_bp.route('/dashboard', methods=['GET'])
def dashboard():
    fuel_settings = FuelSettings.query.first()
    return render_template('admin/dashboard.html', fuel_settings=fuel_settings)

@admin_bp.route('/update_fuel', methods=['POST'])
def update_fuel():
    price = request.form.get('price', type=float)
    if price is None or price <= 0:
        flash('Invalid fuel price.', 'error')
        return redirect(url_for('admin.dashboard'))
        
    fuel_settings = FuelSettings.query.first()
    if not fuel_settings:
        fuel_settings = FuelSettings(current_price=price)
        db.session.add(fuel_settings)
    else:
        fuel_settings.current_price = price
        fuel_settings.last_updated = datetime.utcnow()
        
    db.session.commit()
    flash('Fuel price updated successfully.', 'success')
    return redirect(url_for('admin.dashboard'))
