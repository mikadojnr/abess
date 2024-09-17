from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, jsonify
from app import db
from app.forms import RegistrationForm, LoginForm, ArtistProfileForm, OrganizerProfileForm, EventForm, BookingRequestForm, BookingResponseForm, AddTicketForm, PurchaseTicketForm
from app.models import Notification, User, Artist, Organizer, Customer, Event, BookingRequest, Ticket,TicketPurchase
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from app.utils import optimize_booking_schedule


from urllib.parse import urlsplit

app = Blueprint('app', __name__)


@app.before_request
def check_artist_profile_completion():
    if current_user.is_authenticated and current_user.role == 'Artist':
        artist = Artist.query.filter_by(user_id=current_user.id).first()
        if not artist or not artist.name:  # Check if artist profile is incomplete
            if request.endpoint not in ['app.update_artist', 'app.logout']:  # Avoid redirect loops
                return redirect(url_for('app.update_artist'))
            
            
         

@app.route('/')
def index():
    if current_user.is_authenticated:
        print(current_user.email)
    return render_template('home.html', title="Home")

@app.route("/event/<int:event_id>")
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    return render_template('event_details.html', event=event, title='Event Details')


# Authentication Management
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('app.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Create profile based on role
        if form.role.data == 'Artist':
            artist = Artist(user_id=user.id)
            db.session.add(artist)
        elif form.role.data == 'Organizer':
            organizer = Organizer(user_id=user.id)
            db.session.add(organizer)
        elif form.role.data == 'Customer':
            customer = Customer(user_id=user.id)
            db.session.add(customer)

        db.session.commit()
        flash('Congratulations, you are now registered!', 'success')
        return redirect(url_for('app.login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('app.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('app.login'))
        
        login_user(user)
        
        flash('You are logged in', 'success')
        
        if user.role == 'Organizer':
            return redirect(url_for('app.organizer_dashboard'))
        
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('app.index')
        
        
        return redirect(next_page)
    
    # Capture the `next` parameter if it exists
    next_page = request.args.get('next')
    return render_template('login.html', title='Sign In', form=form, next=next_page)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('app.index'))


# Artist Management Routes

# Artist Profile Route
@app.route('/artist/profile', methods=['GET', 'POST'])
@login_required
def artist_profile():
    if current_user.role != 'Artist':
        return redirect(url_for('app.index'))

    artist = Artist.query.filter_by(user_id=current_user.id).first_or_404()
    pending_requests = BookingRequest.query.filter_by(artist_id=artist.id, status='Pending').all()
    
    form = BookingResponseForm()
    
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')
        
        if request_id and action:
            booking_request = BookingRequest.query.filter_by(id=request_id).first_or_404()

            if action == 'accept':
                try:
                    booking_request.status = 'Accepted'
        
                    db.session.commit()  # Commit change to booking status
                    booking_request.event.update_status_based_on_responses()  # Update the event's overall status
                    message = f'{booking_request.artist.name} has accepted your booking request for {booking_request.event.title}.'
                    try:
                        notification = Notification(recipient_id=booking_request.organizer_id, message=message)
                        db.session.add(notification)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()  # Rollback session on error
                        flash('Unable to send notification at this moment', 'warning')
                        print(f"Error sending notification: {e}")

                except Exception as e: 
                    db.session.rollback()
                    flash('Unable to process your response at this moment', 'warning')
                    print(f"Error Accepting response: {e}")
                    
                else:
                    flash(f'Booking request for {booking_request.event.title} has been accepted.', 'success')
            
            elif action == 'decline':
                flash('Not yet implemented', 'info')
                # try:
                #     booking_request.reject()
                # except:
                #     flash('There was an error processing your request', 'warning')
                # else:
                #     flash(f'Booking request for {booking_request.event.title} has been declined.', 'danger')

            return redirect(url_for('app.artist_profile'))
        else:
            flash('Unable to Perform Action', 'warning')
    return render_template('artist/profile.html', artist=artist, pending_requests=pending_requests, form=form, title='Artist Profile')

@app.route('/artist/profile/update', methods=['GET', 'POST'])
@login_required
def update_artist():
    if current_user.role != 'Artist':
        return redirect(url_for('app.index'))  # Redirect non-artists

    # Check if artist profile exists
    artist = Artist.query.filter_by(user_id=current_user.id).first()

    # If no artist record exists, create one
    if not artist:
        artist = Artist(user_id=current_user.id)
        db.session.add(artist)
        db.session.commit()

    form = ArtistProfileForm(obj=artist)  # Pre-fill form with artist's data

    if form.validate_on_submit():
        
        # Handle profile photo upload
        if form.photo.data:
            # Check if an old photo exists and delete it
            if artist.photo:
                old_photo_path = os.path.join(current_app.root_path, 'static/profile_photos', artist.photo)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)  # Delete the old photo

            # Save the new photo
            filename = secure_filename(form.photo.data.filename)
            filepath = os.path.join(current_app.root_path, 'static/profile_photos', filename)
            form.photo.data.save(filepath)
            artist.photo = filename
        
        # Update artist record with form data
        artist.name = form.name.data
        artist.gender = form.gender.data
        artist.portfolio = form.portfolio.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data  # Assuming genres are comma-separated
        artist.facebook_link = form.facebook_link.data
        artist.website_link = form.website_link.data
        # artist.availability = form.availability.data

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('app.artist_profile'))

    return render_template('artist/update_artist.html', title='Update Profile', form=form, artist=artist)


# Organizer and Event Management Routes
@app.route('/organizer/dashboard')
@login_required
def organizer_dashboard():
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))  # Only organizers can view this page
    
    return render_template('organizer/organizer_dashboard.html', title="Dashboard")

@app.route('/profile/organizer', methods=['GET', 'POST'])
@login_required
def organizer_profile():
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))  # Only organizers can view this page
    
    organizer = Organizer.query.filter_by(user_id=current_user.id).first()
    
    # If no organizer record exists, create one
    if not organizer:
        organizer = Organizer(user_id=current_user.id)
        db.session.add(organizer)
        db.session.commit()

    
    form = OrganizerProfileForm(obj=organizer)  # Pre-populate form with existing data

    if form.validate_on_submit():
        # Handle profile photo upload
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)
            filepath = os.path.join(current_app.root_path, 'static/profile_photos', filename)
            form.photo.data.save(filepath)
            organizer.photo = filename

        # Update other fields
        organizer.name = form.name.data
        organizer.company_name = form.company_name.data
        organizer.phone = form.phone.data
        organizer.city = form.city.data
        organizer.state = form.state.data
        organizer.facebook_link = form.facebook_link.data
        organizer.website_link = form.website_link.data
        organizer.portfolio = form.portfolio.data

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('app.organizer_profile'))
    
    return render_template('organizer/organizer_profile.html', form=form, organizer=organizer, title='Organizer Profile')

@app.route("/organizer/events", methods=['GET', 'POST'])
@login_required
def organizer_events():
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))  # Only organizers can view this page

    page = request.args.get('page', 1, type=int)
    events = Event.query.filter_by(organizer_id=current_user.organizer.id).paginate(page=page, per_page=10)
    
     # Handle POST requests (Status change or event deletion)
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        action = request.form.get('action', 'change_status')
        new_status = request.form.get('status')
        
        # print(f"Received POST: event_id={event_id}, action={action}, status={new_status}")

        # Ensure we got the event_id and status from the form
        if not event_id:
            flash('Event ID not provided', 'danger')
            return redirect(url_for('app.organizer_events'))

        event = Event.query.get_or_404(event_id)

        if action == 'delete':
            # Delete event and its photo
            if event.photo:
                photo_path = os.path.join(current_app.root_path, 'static/uploads/events', event.photo)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            
            db.session.delete(event)
            db.session.commit()
            flash('Event deleted successfully!', 'success')

        elif action == 'change_status':
            # Update event status
            if new_status in ['Pending', 'Scheduled', 'Cancelled']:
                event.status = new_status
                db.session.commit()
                flash('Event status updated successfully!', 'success')
            else:
                flash('Invalid status provided.', 'danger')

        return redirect(url_for('app.organizer_events'))
        
        
    return render_template('organizer/organizer_events.html', events=events, title='Events')
    

@app.route('/organizer/event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))  # Only organizers can view this page
    
    form = EventForm()
    
    if form.validate_on_submit():
        
        photo_filename = None
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_path = os.path.join(current_app.root_path, 'static/uploads/events', photo_filename)
            form.photo.data.save(photo_path)
            
         # Fetch the organizer associated with the current user
        organizer = current_user.organizer  # This assumes the user has an 'organizer' relationship
            
        event = Event(
            title=form.title.data,
            description=form.description.data,
            start_date=form.start_date.data,
            start_time=form.start_time.data,
            venue=form.venue.data,
            city=form.city.data,
            state=form.state.data,
            photo=photo_filename,
            organizer_id=organizer.id  # Set the event's organizer ID based on current_user's organizer profile
        )
        
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('app.organizer_events'))
    
    if request.path == url_for('app.create_event'):
        form.submit.label.text = 'Create Event'
    else:
        form.submit.label.text = 'Update Event'
    
    return render_template('organizer/event_form.html', form=form, title="Events")

@app.route("/organizer/event/update/<int:event_id>", methods=['GET', 'POST'])
@login_required
def update_event(event_id):
    # Ensure only users with role 'Organizer' can update an event
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))
    
    # Fetch the event, ensuring it exists
    event = Event.query.get_or_404(event_id)
    
    # Ensure that the current user is the organizer of the event
    if current_user.organizer.id != event.organizer_id:
        flash('You are not authorized to update this event.', 'danger')
        return redirect(url_for('app.index'))
    
    
    form = EventForm(obj=event)
    
    if form.validate_on_submit():    
        # Update event details
        event.title = form.title.data
        event.description = form.description.data
        event.start_date = form.start_date.data
        event.start_time = form.start_time.data
        event.venue = form.venue.data
        event.city = form.city.data
        event.state = form.state.data
        
        
        # Handle event photo updates
        if form.photo.data:
            # If an existing photo exists, remove it
            if event.photo:
                old_photo_path = os.path.join(current_app.root_path, 'static/uploads/events', event.photo)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)  # Delete the old photo
            
            # Save the new photo
            photo_filename = secure_filename(form.photo.data.filename)
            photo_path = os.path.join(current_app.root_path, 'static/uploads/events', photo_filename)
            form.photo.data.save(photo_path)
            event.photo = photo_filename
            
            
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('app.organizer_events'))
    
    return render_template('organizer/event_form.html', form=form, event=event, title="Events")


# Event Scheduling Optimization Route
@app.route('/organizer/optimize_schedule', methods=['GET', 'POST'])
@login_required
def optimize_schedule():
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))

    events = Event.query.filter_by(organizer_id=current_user.organizer.id).all()
    available_artists = Artist.query.all()

    # Use the helper function to optimize scheduling
    optimized_schedule = optimize_booking_schedule(available_artists, events)
    
    # Display the optimized artist-event pairs
    return render_template('organizer/optimized_schedule.html', schedule=optimized_schedule)



# Organizer Booking Route (Updated for Optimization)
@app.route("/organizer/send_booking_request/<int:event_id>", methods=['GET', 'POST'])
@login_required
def send_booking_request(event_id):
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))

    event = Event.query.get_or_404(event_id)
    form = BookingRequestForm()


    available_artists = Artist.query.filter(
        ~Artist.booking_requests.any(BookingRequest.event.has(start_date=event.start_date))
    ).all()

    form.artists.choices = [(artist.id, artist.name) for artist in available_artists]
    form.important_artists.choices = [(artist.id, artist.name) for artist in available_artists]

    if form.validate_on_submit():
        important_declines = False

        for artist_id in form.artists.data:
            artist = Artist.query.get(artist_id)

            booking_request = BookingRequest(
                event_id=event.id,
                artist_id=artist.id,
                organizer_id=current_user.organizer.id,
                status='Pending',
                message=f'Invitation to perform for event: {event.title}.',
                important=True if artist_id in form.important_artists.data else False
            )
            db.session.add(booking_request)
        db.session.commit()
        flash(f'Booking request sent successfully.', 'success')
        return redirect(url_for('app.organizer_events'))

    return render_template('organizer/send_booking_request.html', form=form, event=event, title="Send Booking")


@app.route('/organizer/event/<int:event_id>/add_ticket', methods=['GET', 'POST'])
@login_required
def add_ticket(event_id):
    
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))

    
    event = Event.query.get_or_404(event_id)
    form = AddTicketForm()

    if form.validate_on_submit():
        new_ticket = Ticket(
            event_id=event.id,
            category=form.category.data,
            price=form.price.data,
            benefits=form.benefits.data,
            quantity=form.quantity.data
        )
        db.session.add(new_ticket)
        db.session.commit()
        flash('Ticket added successfully!', 'success')
        return redirect(url_for('app.organizer_dashboard'))

    return render_template('organizer/add_ticket.html', form=form, event=event)


@app.route('/event/<int:event_id>/purchase_ticket', methods=['GET', 'POST'])
@login_required
def purchase_ticket(event_id):
    event = Event.query.get_or_404(event_id)
    form = PurchaseTicketForm()

    available_tickets = Ticket.query.filter_by(event_id=event.id).all()
    form.ticket_id.choices = [(ticket.id, f"{ticket.category} - ${ticket.price}") for ticket in available_tickets]

    if form.validate_on_submit():
        ticket = Ticket.query.get_or_404(form.ticket_id.data)
        purchase = TicketPurchase(ticket_id=ticket.id, user_id=current_user.id)
        db.session.add(purchase)
        db.session.commit()
        flash('Ticket purchased successfully!', 'success')
        return redirect(url_for('app.view_event', event_id=event.id))

    return render_template('event/purchase_ticket.html', form=form, event=event)

@app.route("/organizer/bookings")
@login_required
def organizer_bookings():
    
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))
    
    page = request.args.get('page', 1, type=int)
    bookings = BookingRequest.query.filter_by(organizer_id=current_user.organizer.id).paginate(page=page, per_page=10)

    
    return render_template('organizer/bookings.html', bookings=bookings, title="Bookings")


@app.route('/organizer/notifications')
@login_required
def organizer_notifications():
    
    if current_user.role != 'Organizer':
        return redirect(url_for('app.index'))
    
    notifications = Notification.query.filter_by(recipient_id=current_user.id).all()
    return render_template('/organizer/notifications.html', notifications=notifications, title="Notifications")


@app.route('/organizer/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_as_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    if notification.recipient_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    notification.mark_as_read()
    
    return jsonify({"success": True})