from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.circle import RideCircle, CircleMember

circle_bp = Blueprint('circle', __name__)

@circle_bp.route('/')
@login_required
def list():
    memberships = current_user.circle_memberships
    my_circles = [m.circle for m in memberships]
    return render_template('circles/list.html', circles=my_circles)

@circle_bp.route('/create', methods=['POST'])
@login_required
def create():
    name = request.form.get('name')
    if not name:
        flash('Circle name is required.', 'error')
        return redirect(url_for('circle.list'))
        
    new_circle = RideCircle(name=name, creator_id=current_user.id)
    db.session.add(new_circle)
    db.session.flush() # To get the new_circle.id
    
    # Add creator as a member
    membership = CircleMember(circle_id=new_circle.id, user_id=current_user.id)
    db.session.add(membership)
    db.session.commit()
    
    flash(f'Successfully created {name}! Invite friends using code: {new_circle.invite_code}', 'success')
    return redirect(url_for('circle.list'))

@circle_bp.route('/join', methods=['POST'])
@login_required
def join():
    code = request.form.get('invite_code')
    if not code:
        flash('Invite code is required.', 'error')
        return redirect(url_for('circle.list'))
        
    circle = RideCircle.query.filter_by(invite_code=code).first()
    if not circle:
        flash('Invalid invite code.', 'error')
        return redirect(url_for('circle.list'))
        
    existing = CircleMember.query.filter_by(circle_id=circle.id, user_id=current_user.id).first()
    if existing:
        flash('You are already a member of this circle.', 'warning')
        return redirect(url_for('circle.list'))
        
    membership = CircleMember(circle_id=circle.id, user_id=current_user.id)
    db.session.add(membership)
    db.session.commit()
    
    flash(f'Successfully joined {circle.name}!', 'success')
    return redirect(url_for('circle.list'))

@circle_bp.route('/<int:circle_id>')
@login_required
def details(circle_id):
    circle = RideCircle.query.get_or_404(circle_id)
    
    # Check membership
    is_member = any(m.user_id == current_user.id for m in circle.members)
    if not is_member:
        flash('You do not have access to this circle.', 'error')
        return redirect(url_for('circle.list'))
        
    # Get upcoming rides for this circle
    from models.ride import Ride
    from datetime import datetime
    circle_rides = Ride.query.filter(
        Ride.circle_id == circle.id,
        Ride.date_time > datetime.utcnow(),
        Ride.seats_available > 0
    ).order_by(Ride.date_time.asc()).all()
    
    return render_template('circles/details.html', circle=circle, rides=circle_rides)
