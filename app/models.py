from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Table name in plural

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(500))
    role = db.Column(db.String(20))  # Choices: 'Artist', 'Organizer', 'Customer'

    # Relationship to Organizer, Customer, and Artist
    organizer = db.relationship('Organizer', backref='user', uselist=False)
    artist = db.relationship('Artist', backref='user', uselist=False)
    customer = db.relationship('Customer', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Artist(db.Model):
    __tablename__ = 'artists'  # Table name in plural

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    availability = db.Column(db.String(256))  # JSON serialized availability
    gender = db.Column(db.String(8))
    portfolio = db.Column(db.String(256))
    photo = db.Column(db.String(256))
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))

    # Define the relationship with BookingRequest
    # booking_requests = db.relationship('BookingRequest', backref='artist_profile', lazy=True)


class Organizer(db.Model):
    __tablename__ = 'organizers'  # Table name in plural

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    company_name = db.Column(db.String(256))
    phone = db.Column(db.String(120))
    gender = db.Column(db.String(8))
    photo = db.Column(db.String(256))
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    portfolio = db.Column(db.String(256))
    
    # events = db.relationship('Event', backref='organizer_profile', lazy=True)


class Customer(db.Model):
    __tablename__ = 'customers'  # Table name in plural

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    gender = db.Column(db.String(8))


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String(256))
    title = db.Column(db.String(256))
    venue = db.Column(db.String(256))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Event status will be updated dynamically
    organizer_id = db.Column(db.Integer, db.ForeignKey('organizers.id'))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now())

    # booking_requests = db.relationship('BookingRequest', backref='event', lazy=True)

    def update_status_based_on_responses(self):
        accepted = len([req for req in self.booking_requests if req.status == 'Accepted'])
        total_requests = len(self.booking_requests)
        important_declined = any(req.status == 'Rejected' and req.important for req in self.booking_requests)

        if important_declined:
            self.status = 'Cancelled'
        elif accepted == total_requests:
            self.status = 'Confirmed'
        elif accepted > 0:
            self.status = 'Partially Confirmed'
        else:
            self.status = 'Pending'
        
        db.session.commit()
        send_notification(self.organizer_id, f'The status of your event "{self.title}" has been updated to: {self.status}.')


class BookingRequest(db.Model):
    __tablename__ = 'booking_requests'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('organizers.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')  # Pending, Accepted, Rejected
    message = db.Column(db.Text, nullable=True)
    important = db.Column(db.Boolean, default=False)  # If rejecting this request is critical
    created_at = db.Column(db.DateTime, default=datetime.now)

    artist = db.relationship('Artist', backref='booking_requests', lazy=True)
    event = db.relationship('Event', backref='booking_requests', lazy=True)
    organizer = db.relationship('Organizer', backref='booking_requests', lazy=True)

    def accept(self):
        """Accepts the booking request and updates event status."""
        self.status = 'Accepted'
        
        db.session.commit()  # Commit change to booking status
        self.event.update_status_based_on_responses()  # Update the event's overall status
        send_notification(self.organizer_id, f'{self.artist.name} has accepted your booking request for {self.event.title}.')
    
    def reject(self):
        self.status = 'Declined'
       
        if self.important:  
            self.event.status = 'Cancelled'
        db.session.commit()
        self.event.update_status_based_on_responses()
        send_notification(self.organizer_id, f'{self.artist.name} has declined your booking request for {self.event.title}.')



class Notification(db.Model):
    __tablename__ = 'notifications'  # Table name in plural

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now())
    read = db.Column(db.Boolean, default=False)
    
    

    def mark_as_read(self):
        self.read = True
        db.session.commit()

def send_notification(recipient_id, message):
    try:
        notification = Notification(recipient_id=recipient_id, message=message)
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        db.session.rollback()  # Rollback session on error
        print(f"Error sending notification: {e}")


class Ticket(db.Model):
    __tablename__ = 'tickets'  # Table name in plural

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    category = db.Column(db.String(64))  # VIP, General, Free, etc.
    price = db.Column(db.Float, nullable=False)
    benefits = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False)  # Number of tickets available

    @property
    def sold_out(self):
        sold_tickets = len(self.purchases)
        return sold_tickets >= self.quantity


class TicketPurchase(db.Model):
    __tablename__ = 'ticket_purchases'  # Table name in plural

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    purchased_at = db.Column(db.DateTime, default=datetime.now())

