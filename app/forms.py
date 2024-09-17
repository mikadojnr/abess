from flask import request, url_for
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, FloatField, IntegerField, PasswordField, SubmitField, SelectField, TextAreaField, FileField, SelectMultipleField, DateField, TimeField
from wtforms.validators import NumberRange, DataRequired, Email, EqualTo, ValidationError, Length, URL, Optional
from app.models import User
import re
from app.enums import Genre, State
from flask_wtf.file import FileAllowed
from datetime import datetime

from wtforms.widgets import RadioInput, ListWidget

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('', 'Choose a role'), ('Artist', 'Artist'), ('Organizer', 'Organizer'), ('Customer', 'Customer')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already exist.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email address already in use.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')
    

def is_valid_phone(number):
    regex = re.compile('^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$')
    return regex.match(number)


class ArtistProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=120)])
    gender = SelectField('Gender', choices=[('', 'Select an option'), ('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired(message="Please select a gender.")])
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', validators=[DataRequired()], choices = State.choices() )
    phone = StringField('Phone')
    facebook_link = StringField('Facebook Link', validators=[URL()])
    website_link = StringField('Website Link', validators=[URL()])
    genres = SelectMultipleField('Genres', validators=[DataRequired()], choices = Genre.choices() )
    availability = StringField('Availability')
    portfolio = TextAreaField('Portfolio', validators=[Length(max=256)])
    photo = FileField('Upload Profile Photo')
    submit = SubmitField('Update Profile')
    

class OrganizerProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=256)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=120)])
    city = StringField('City', validators=[DataRequired(), Length(max=120)])
    state = SelectField('State', validators=[DataRequired()], choices = State.choices() )
    facebook_link = StringField('Facebook Profile Link', validators=[Optional(), Length(max=120)])
    website_link = StringField('Website Link', validators=[Optional(), Length(max=120)])
    photo = FileField('Profile Photo', validators=[Optional()])  # Allows photo upload
    portfolio = TextAreaField('Portfolio', validators=[Length(max=256)])
    gender = SelectField('Gender', choices=[('', 'Select an option'), ('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired(message="Please select a gender.")])
    submit = SubmitField('Update Profile')


class CustomerProfileForm(FlaskForm):
    name = StringField('Name')
    city = StringField('City')
    state = StringField('State')
    phone = StringField('Phone')
    gender = StringField('Gender')
    submit = SubmitField('Save Changes')
    
class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired(), Length(max=256)])
    description = TextAreaField('Event Description', validators=[DataRequired()])
    start_date = DateField('Event Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = TimeField('Event Time', format='%H:%M', validators=[DataRequired()])
    venue = StringField('Venue', validators=[DataRequired(), Length(max=256)])
    city = StringField('City', validators=[DataRequired(), Length(max=120)])
    state = SelectField('State', validators=[DataRequired()], choices = State.choices() )
    photo = FileField('Event Flyer', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])  # Limit to image files
    submit = SubmitField()
    
# Form for sending booking requests
class BookingRequestForm(FlaskForm):
    artists = SelectMultipleField('Artists', coerce=int, validators=[DataRequired()])
    important_artists = SelectMultipleField('Important Artists', coerce=int, validators=[Optional()])
    submit = SubmitField('Send Booking Request')

# Form for adding tickets to an event
class AddTicketForm(FlaskForm):
    category = StringField('Category', validators=[DataRequired()])
    price = FloatField('Price', validators=[NumberRange(min=0, message='Price must be positive')])
    benefits = TextAreaField('Benefits', validators=[Optional()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1, message='At least one ticket is required')])
    submit = SubmitField('Add Ticket')

# Form for purchasing tickets
class PurchaseTicketForm(FlaskForm):
    ticket_id = SelectField('Select Ticket', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Purchase Ticket')

# Form for responding to a booking request
class BookingResponseForm(FlaskForm):
  
    accept = SubmitField('Accept')
    decline = SubmitField('Decline')