from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db
from models.ride import Ride, RideParticipant, RideHistory
from models.chat import Message
from models.circle import RideCircle
from datetime import datetime
import os
import json
try:
    import google.generativeai as genai
except ImportError:
    genai = None

ride_bp = Blueprint('ride', __name__)

@ride_bp.route('/dashboard')
@login_required
def dashboard():
    offered_rides = Ride.query.filter_by(driver_id=current_user.id).order_by(Ride.date_time.asc()).all()
    
    joined_participations = RideParticipant.query.filter_by(user_id=current_user.id, status='accepted').all()
    joined_rides = [p.ride for p in joined_participations]
    
    available_rides = Ride.query.filter(
        Ride.driver_id != current_user.id,
        Ride.seats_available > 0,
        Ride.date_time > datetime.utcnow()
    ).order_by(Ride.date_time.asc()).limit(6).all()
    
    # FinTech Savings Calculation
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    all_histories = RideHistory.query.filter_by(user_id=current_user.id).all()
    
    monthly_histories = [h for h in all_histories if h.date.month == current_month and h.date.year == current_year]
    
    monthly_savings = sum(h.savings for h in monthly_histories)
    lifetime_savings = sum(h.savings for h in all_histories)
    lifetime_rides = len(all_histories)
    
    monthly_cost = sum(h.shared_cost for h in monthly_histories)
    monthly_solo = sum(h.solo_cost for h in monthly_histories)
    
    avg_cost = sum(h.shared_cost for h in all_histories) / lifetime_rides if lifetime_rides > 0 else 0
    
    fintech_stats = {
        'monthly_savings': monthly_savings,
        'lifetime_savings': lifetime_savings,
        'lifetime_rides': lifetime_rides,
        'avg_cost': avg_cost,
        'monthly_solo': monthly_solo,
        'monthly_cost': monthly_cost
    }
    
    # Calculate locality insights (how many students nearby)
    # Mock data for UI demonstration based on user requirement
    locality_insight = "Aliganj (3 students nearby)"
    
    return render_template('dashboard.html', 
                         offered_rides=offered_rides, 
                         joined_rides=joined_rides,
                         available_rides=available_rides,
                         locality_insight=locality_insight,
                         fintech_stats=fintech_stats)

@ride_bp.route('/offer', methods=['GET', 'POST'])
@login_required
def offer():
    user_circles = [cm.circle for cm in current_user.circle_memberships]
    
    if request.method == 'POST':
        ride_type = request.form.get('ride_type')
        locality = request.form.get('locality')
        
        # Enforce Ramswaroop College
        if ride_type == 'to_college':
            source = locality
            destination = "Ramswaroop College"
        else:
            source = "Ramswaroop College"
            destination = locality
 
        ride_date = request.form.get('ride_date')
        ride_time = request.form.get('ride_time')
        date_time_str = f"{ride_date} {ride_time}" if ride_date and ride_time else ""
        seats_total = int(request.form.get('seats'))
        vehicle_type = request.form.get('vehicle_type')
        
        # Enforce realistic passenger bounds
        if 'Bike' in vehicle_type and seats_total > 1:
            flash('Bikes cannot take more than 1 additional passenger.', 'error')
            return redirect(url_for('ride.offer'))
        if 'Car' in vehicle_type and seats_total > 4:
            flash('Cars cannot take more than 4 additional passengers.', 'error')
            return redirect(url_for('ride.offer'))
            
        cost = request.form.get('cost_per_seat')
        cost_per_seat = float(cost) if cost else 0.0
        
        if cost_per_seat < 10:
            flash('Calculated cost cannot fall underneath the minimum threshold of ₹10.', 'error')
            return redirect(url_for('ride.offer'))
            
        circle_id = request.form.get('circle_id')
        is_female_only = True if request.form.get('female_only') else False
        
        is_recurring = True if request.form.get('is_recurring') else False
        recurrence_days = "Mon-Fri" if is_recurring else None
        
        pickup_name = request.form.get('pickup_name')
        pickup_lat = request.form.get('pickup_lat')
        pickup_lng = request.form.get('pickup_lng')
        
        try:
            # Handle standard browser datetime-local format (YYYY-MM-DDTHH:MM)
            # and common variations (with space instead of T, etc.)
            dt = None
            date_time_str = date_time_str.replace('T', ' ') if date_time_str else ''
            
            for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(date_time_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not dt:
                flash('Please enter a valid date and time (ensure both fields are filled).', 'error')
                return redirect(url_for('ride.offer'))
            
            new_ride = Ride(
                driver_id=current_user.id,
                source=source,
                destination=destination,
                date_time=dt,
                seats_total=seats_total,
                seats_available=seats_total,
                vehicle_type=vehicle_type,
                ride_type=ride_type,
                is_recurring=is_recurring,
                recurrence_days=recurrence_days,
                cost_per_seat=cost_per_seat,
                circle_id=circle_id if circle_id else None,
                is_female_only=is_female_only,
                pickup_name=pickup_name,
                pickup_lat=pickup_lat,
                pickup_lng=pickup_lng
            )
            db.session.add(new_ride)
            db.session.commit()
            flash('College commute published successfully!', 'success')
            return redirect(url_for('ride.dashboard'))
            
        except Exception as e:
            print(f"Ride creation error: {e}")
            flash('An error occurred while creating the ride. Please check all fields.', 'error')
            
    return render_template('rides/offer.html', circles=user_circles, maps_api_key=current_app.config.get('GOOGLE_MAPS_API_KEY'))

@ride_bp.route('/find', methods=['GET', 'POST'])
@login_required
def find():
    query = Ride.query.filter(
        Ride.seats_available > 0,
        Ride.driver_id != current_user.id,
        Ride.date_time > datetime.utcnow()
    )
    
    if request.method == 'POST':
        ride_type = request.form.get('ride_type')
        time_filter = request.form.get('time_filter')
        locality = request.form.get('locality')
        
        if ride_type:
            query = query.filter_by(ride_type=ride_type)
            
        if locality:
            # We strictly search the locality endpoint
            if ride_type == 'to_college':
                query = query.filter(Ride.source.ilike(f'%{locality}%'))
            elif ride_type == 'from_college':
                query = query.filter(Ride.destination.ilike(f'%{locality}%'))
            else:
                # Fallback generic filter just in case
                query = query.filter((Ride.source.ilike(f'%{locality}%')) | (Ride.destination.ilike(f'%{locality}%')))
                
        # Handle time filter natively mimicking morning/evening
        if time_filter == 'morning':
            query = query.filter(db.extract('hour', Ride.date_time) < 12)
        elif time_filter == 'evening':
            query = query.filter(db.extract('hour', Ride.date_time) >= 12)
            
    if current_user.gender != 'Female':
        query = query.filter(Ride.is_female_only == False)
        
    rides = query.order_by(Ride.date_time.asc()).all()
        
    return render_template('rides/find.html', rides=rides)

@ride_bp.route('/ai-match', methods=['POST'])
@login_required
def ai_match():
    # Configure Gemini with key from config if present
    api_key = current_app.config.get('GOOGLE_API_KEY')
    if genai and api_key:
        genai.configure(api_key=api_key)

    user_text = request.form.get('description', '')
    if not user_text:
        flash('Please provide a description.', 'error')
        return redirect(url_for('ride.find'))
        
    extracted = {
        'ride_type': None,
        'locality': None,
        'time_filter': None
    }
    
    # Try using Gemini API if configured
    if genai and api_key:
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = f"""
            You are a helpful travel assistant for a college ride-sharing app. 
            Extract travel details from this user query: "{user_text}".

            Output ONLY valid JSON and nothing else, with exactly these three keys:
            1. "ride_type": must be exactly "to_college" (if destination is college), "from_college" (if source is college), or null if unclear. 
            2. "locality": the name of the residential area mentioned. 
               IMPORTANT: If the user misspells a locality name, CORRECT it to the standard Lucknow locality name (e.g., "mushipuliys" -> "Munshipulia", "gomti ngr" -> "Gomti Nagar").
            3. "time_filter": "morning" for times before 12 PM (AM), "evening" for times after 12 PM (PM), or null.

            Return JSON:
            """
            response = model.generate_content(prompt)
            # Robust JSON cleaning
            text_result = response.text.replace('```json', '').replace('```', '').split('{', 1)[-1].rsplit('}', 1)[0]
            text_result = '{' + text_result + '}'
            params = json.loads(text_result)
            extracted.update(params)
        except Exception as e:
            # Fallback will kick in below if extraction is empty
            print("Gemini API Error (Model 2.0-Flash):", e)
            pass

    # Keyword based fallback if API didn't provide results or failed
    t_lower = user_text.lower()
    if not extracted['ride_type']:
        if 'to college' in t_lower or 'go to' in t_lower:
            extracted['ride_type'] = 'to_college'
        elif 'from college' in t_lower or 'leave' in t_lower:
            extracted['ride_type'] = 'from_college'
            
    if not extracted['time_filter']:
        if 'morning' in t_lower or 'am' in t_lower:
            extracted['time_filter'] = 'morning'
        elif 'evening' in t_lower or 'pm' in t_lower:
            extracted['time_filter'] = 'evening'
            
    if not extracted['locality']:
        common_localities = ['gomti nagar', 'indira nagar', 'hazratganj', 'aliganj', 'bhootnath']
        for loc in common_localities:
            if loc in t_lower:
                extracted['locality'] = loc
                break

    flash(f'AI Extracted: {extracted["ride_type"] or "Any direction"}, {extracted["time_filter"] or "Any time"}, Locality: {extracted["locality"] or "Any"}', 'info')
    
    # Build query
    query = Ride.query.filter(
        Ride.seats_available > 0,
        Ride.driver_id != current_user.id,
        Ride.date_time > datetime.utcnow()
    )
    
    if extracted['ride_type']:
        query = query.filter_by(ride_type=extracted['ride_type'])
    if extracted['locality']:
        if extracted['ride_type'] == 'to_college':
            query = query.filter(Ride.source.ilike(f'%{extracted["locality"]}%'))
        else:
            query = query.filter(Ride.destination.ilike(f'%{extracted["locality"]}%'))
    if extracted['time_filter'] == 'morning':
        query = query.filter(db.extract('hour', Ride.date_time) < 12)
    elif extracted['time_filter'] == 'evening':
        query = query.filter(db.extract('hour', Ride.date_time) >= 12)
        
    if current_user.gender != 'Female':
        query = query.filter(Ride.is_female_only == False)
        
    rides = query.order_by(Ride.date_time.asc()).all()
    
    return render_template('rides/find.html', rides=rides, ai_matched=True)

@ride_bp.route('/join/<int:ride_id>', methods=['POST'])
@login_required
def join(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    
    if ride.seats_available <= 0:
        flash('Sorry, this ride is full.', 'error')
        return redirect(url_for('ride.find'))
        
    if ride.driver_id == current_user.id:
        flash('You cannot join your own ride.', 'error')
        return redirect(url_for('ride.find'))
        
    existing = RideParticipant.query.filter_by(ride_id=ride.id, user_id=current_user.id).first()
    if existing:
        flash('You have already joined or requested this ride.', 'warning')
        return redirect(url_for('ride.dashboard'))
        
    participant = RideParticipant(ride_id=ride.id, user_id=current_user.id, status='accepted')
    ride.seats_available -= 1
    
    db.session.add(participant)
    db.session.commit()
    
    flash('Successfully joined the commute!', 'success')
    return redirect(url_for('ride.details', ride_id=ride.id))

@ride_bp.route('/<int:ride_id>')
@login_required
def details(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    is_driver = current_user.id == ride.driver_id
    is_participant = any(p.user_id == current_user.id and p.status == 'accepted' for p in ride.participants)
    
    if not (is_driver or is_participant):
        flash('You do not have access to this commute.', 'error')
        return redirect(url_for('ride.dashboard'))
        
    return render_template('rides/details.html', ride=ride, is_driver=is_driver)

@ride_bp.route('/complete/<int:ride_id>', methods=['POST'])
@login_required
def complete_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    
    if ride.driver_id != current_user.id:
        flash('Only the driver can complete the commute.', 'error')
        return redirect(url_for('ride.dashboard'))
        
    if ride.status == 'completed':
        flash('This commute is already completed.', 'warning')
        return redirect(url_for('ride.dashboard'))
        
    # Mark as completed
    ride.status = 'completed'
    
    # Calculate savings for each accepted passenger
    # MVP assumption: ~15km average trip to Ramswaroop
    distance = 15.0
    solo_cost = distance * 8.0 # Rs 8 per km avg auto/cab fare
    shared_cost = ride.cost_per_seat or 0.0
    savings = max(0, solo_cost - shared_cost)
    
    for participant in ride.participants:
        if participant.status == 'accepted':
            history = RideHistory(
                user_id=participant.user_id,
                ride_id=ride.id,
                distance=distance,
                solo_cost=solo_cost,
                shared_cost=shared_cost,
                savings=savings
            )
            db.session.add(history)
            
    # Also log savings for driver (e.g. they save by splitting fuel, but simple formula here)
    driver_savings = sum([shared_cost for p in ride.participants if p.status == 'accepted'])
    if driver_savings > 0:
        driver_history = RideHistory(
            user_id=ride.driver_id,
            ride_id=ride.id,
            distance=distance,
            solo_cost=distance * 3, # petrol cost
            shared_cost=(distance * 3) - driver_savings,
            savings=driver_savings
        )
        db.session.add(driver_history)

    db.session.commit()
    flash('Commute marked as completed! Savings added to dashboard.', 'success')
    return redirect(url_for('ride.dashboard'))

@ride_bp.route('/<int:ride_id>/messages')
@login_required
def get_messages(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    is_driver = current_user.id == ride.driver_id
    is_participant = any(p.user_id == current_user.id and p.status == 'accepted' for p in ride.participants)
    
    if not (is_driver or is_participant):
        return {"error": "Unauthorized"}, 403
        
    messages = Message.query.filter_by(ride_id=ride_id).order_by(Message.created_at.asc()).all()
    return {
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.sender.name,
                "text": m.message_text,
                "timestamp": m.created_at.strftime('%I:%M %p')
            } for m in messages
        ]
    }

@ride_bp.route('/<int:ride_id>/send-message', methods=['POST'])
@login_required
def send_message(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    is_driver = current_user.id == ride.driver_id
    is_participant = any(p.user_id == current_user.id and p.status == 'accepted' for p in ride.participants)
    
    if not (is_driver or is_participant):
        return {"error": "Unauthorized"}, 403
        
    text = request.form.get('message_text') or request.json.get('message_text')
    if not text:
        return {"error": "Message text is required"}, 400
        
    new_msg = Message(ride_id=ride_id, sender_id=current_user.id, message_text=text)
    db.session.add(new_msg)
    db.session.commit()
    
    return {"status": "success"}
