
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, BooleanField, IntegerField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, NumberRange
from models import User # to check for existing usernames

from datetime import datetime, date

class LoginForm(FlaskForm):
    """Form for all users to login."""
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', 
                             validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    """Form for Patients to register."""
    name = StringField('Full Name', 
                       validators=[DataRequired(), Length(min=2, max=100)])
    contact = StringField('Contact', 
                          validators=[DataRequired()])
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', 
                             validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Custom validator to check if username already exists."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose another.')





class EditPatientForm(FlaskForm):
    """Form for Admin to edit an existing Patient."""
    name = StringField('Full Name', 
                       validators=[DataRequired(), Length(min=2, max=100)])
    contact = StringField('Contact', 
                          validators=[DataRequired()])
    submit = SubmitField('Update Patient')



class BookAppointmentForm(FlaskForm):
    """Form for Patient to book an appointment."""
    # Using StringField for simplicity, as requested.
    # We can ask for "YYYY-MM-DD HH:MM" format.
    appointment_date = StringField('Appointment Date (e.g., YYYY-MM-DD HH:MM)', 
                                   validators=[DataRequired()])
    submit = SubmitField('Book Appointment')

class UpdateTreatmentForm(FlaskForm):
    """Form for Doctor to add treatment notes."""
    visit_type = StringField("Visit Type", default="Regular Checkup", validators=[DataRequired(), Length(min=4, max=150)])
    test_done = StringField("Test Done", default="-", validators=[DataRequired(), Length(min=1, max=150)])


    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    prescription = TextAreaField('Prescription', validators=[DataRequired()])
    submit = SubmitField('Save Treatment')




# Doctor Forms ------------

class AddDoctorForm(FlaskForm):
    """Form for Admin to add a new Doctor."""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    # username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    # password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    specialization = StringField('Specialization', validators=[DataRequired(), Length(min=4, max=150)])
    experience =  IntegerField('Experience', validators=[DataRequired(), NumberRange(min=0)])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    qualifications = StringField('Qualifications', validators=[DataRequired(), Length(min=4, max=150)])
    submit = SubmitField('Add Doctor')

    def validate_username(self, username):
        """Check if username already exists."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')
    
    def validate_dob(self, dob):
        today = date.today()
        eighteen_years_ago = today.replace(year=today.year - 18)


        if dob.data > today:
            raise ValidationError("The event date cannot be in the future!")
        if dob.data > eighteen_years_ago:
            raise ValidationError("Doctor must be 18 years old!")


class EditDoctorForm(FlaskForm):
    """Form for Admin to edit an existing Doctor."""
    name = StringField('Full Name', 
                       validators=[DataRequired(), Length(min=2, max=100)])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Doctor')

class UpdateAvailabilityForm(FlaskForm):
    """
    A form with 14 checkboxes for the next 7 days, 2 slots per day.
    We use 'day0_am', 'day0_pm' as field names.
    """
    day0_am = BooleanField('8am - 12pm')
    day0_pm = BooleanField('4pm - 9pm')
    
    day1_am = BooleanField('8am - 12pm')
    day1_pm = BooleanField('4pm - 9pm')
    
    day2_am = BooleanField('8am - 12pm')
    day2_pm = BooleanField('4pm - 9pm')
    
    day3_am = BooleanField('8am - 12pm')
    day3_pm = BooleanField('4pm - 9pm')
    
    day4_am = BooleanField('8am - 12pm')
    day4_pm = BooleanField('4pm - 9pm')
    
    day5_am = BooleanField('8am - 12pm')
    day5_pm = BooleanField('4pm - 9pm')
    
    day6_am = BooleanField('8am - 12pm')
    day6_pm = BooleanField('4pm - 9pm')
    
    submit = SubmitField('Update Availability')



# PATIENT DASHBOARD -----------------------------------------------------------
class UpdatePatientProfileForm(FlaskForm):
    """Form for Patient to update their own profile."""
    name = StringField('Full Name', 
                       validators=[DataRequired(), Length(min=2, max=100)])
    contact = StringField('Contact', 
                          validators=[DataRequired()])
    submit = SubmitField('Update Profile')


class SearchDoctorForm(FlaskForm):
    """Simple search form."""
    query = StringField('Search by Name or Specialization', 
                        validators=[DataRequired()])
    submit = SubmitField('Search')


class BookAppointmentForm(FlaskForm):
    """
    Form for Patient to book an appointment.
    The choices will be populated dynamically from the route.
    """
    # This value will be something like "2025-11-12 am"
    appointment_slot = SelectField('Select an Available Slot', 
                                   validators=[DataRequired()])
    submit = SubmitField('Book Appointment')


# rohan.330
# Wyz7hLLvUQ