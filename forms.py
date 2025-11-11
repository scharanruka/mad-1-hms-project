
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User # to check for existing usernames

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

# --- FORMS FOR FUTURE MILESTONES ---
# We can define them now since we're here.

class AddDoctorForm(FlaskForm):
    """Form for Admin to add a new Doctor."""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    # We will populate the 'choices' for this field in our route
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Doctor')

    def validate_username(self, username):
        """Check if username already exists."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

class EditDoctorForm(FlaskForm):
    """Form for Admin to edit an existing Doctor."""
    name = StringField('Full Name', 
                       validators=[DataRequired(), Length(min=2, max=100)])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Doctor')

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
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    prescription = TextAreaField('Prescription', validators=[DataRequired()])
    submit = SubmitField('Save Treatment')