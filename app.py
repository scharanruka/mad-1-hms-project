from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Department, Doctor, Patient, Appointment, Treatment

# Forms
from forms import LoginForm, RegistrationForm, AddDoctorForm, BookAppointmentForm, UpdateTreatmentForm

import os

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'

db.init_app(app)

def create_db_and_admin():
    with app.app_context():
        db.create_all()
        # Create admin user ------------------
        if not User.query.filter_by(username='admin').first():
                    print("Admin user not found, creating one...")
                    # Hash the admin's password
                    hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
                    
                    # Create the new admin user object
                    admin_user = User(
                        username='admin', 
                        password=hashed_password, 
                        role='admin'
                    )
                    
                    # Add to the session and commit
                    db.session.add(admin_user)
                    print("Admin user created.")
        else:
            print("Admin user already exists.")
        #------------------
        # --- Create Default Departments ---
        if not Department.query.first():
            print("No departments found, creating defaults...")
            default_depts = ['Cardiology', 'Neurology', 'Oncology', 'Orthopedics', 'Pediatrics']
            
            for dept_name in default_depts:
                new_dept = Department(name=dept_name)
                db.session.add(new_dept)
                
            print(f"Created {len(default_depts)} departments.")
        else:
            print("Departments already exist.")

        # Commit all changes to the database
        db.session.commit()
        print("Database setup complete.")




# ROUTES ------------------------------------
@app.route('/')
def index():
    # Render the new homepage
    return render_template('index.html')



# AUTH ROUTES -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles login for all user roles using Flask-WTF."""
    form = LoginForm() # Create an instance of the form

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
            # We don't redirect here, we let the page re-render
            # to show the flash message.

    # Pass the form to the template
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    # --- Auth check ---
    if 'user_id' not in session:
        flash('You are not logged in.')
        return redirect(url_for('login'))

    """Logs the user out by clearing the session."""
    session.pop('user_id', None)
    session.pop('role', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles Patient Registration using Flask-WTF."""
    form = RegistrationForm() # Create an instance of the form

    # Check if the form was submitted and all validators passed
    if form.validate_on_submit():
        
        # Get data from the form object (form.field.data)
        name = form.name.data
        contact = form.contact.data
        username = form.username.data
        password = form.password.data

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create the User
        new_user = User(
            username=username, 
            password=hashed_password, 
            role='patient'
        )
        db.session.add(new_user)
        db.session.commit() 

        # Create the associated Patient profile
        new_patient = Patient(
            name=name, 
            contact=contact, 
            user_id=new_user.id
        )
        db.session.add(new_patient)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    # If form is not valid (or it's a GET request), render the template
    # The form object will pass any validation errors to the template
    return render_template('register.html', form=form)
#-------------------------------------------------------------------


# Dashboard Routes -------------------------
@app.route('/dashboard')
def dashboard():
    """
    Central dashboard. Redirects user to their
    role-specific dashboard.
    """
    # Auth check ---
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))
    role = session.get('role')
    # ----
    
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    elif role == 'patient':
        return redirect(url_for('patient_dashboard'))
    else:
        # return redirect(url_for('logout'))
        return redirect(url_for('index'))

# Role-specific dashboards
@app.route('/admin/dashboard')
def admin_dashboard():
    # --- SIMPLE AUTH CHECK ---
    # 1. Check if logged in
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))

    # 2. Check for correct role
    if session.get('role') != 'admin':
        flash('You do not have permission to access this page.')
        # Send them back to their own dashboard
        return redirect(url_for('dashboard'))
    # --- END OF CHECK ---
    return render_template('admin_dashboard.html')

@app.route('/doctor/dashboard')
def doctor_dashboard():
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))

    if session.get('role') != 'doctor':
        flash('You do not have permission to access this page.')
        return redirect(url_for('dashboard'))
    # --- END OF CHECK ---

    return render_template('doctor_dashboard.html')

@app.route('/patient/dashboard')
def patient_dashboard():
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))

    if session.get('role') != 'patient':
        flash('You do not have permission to access this page.')
        return redirect(url_for('dashboard'))
    # --- END OF CHECK ---
    return render_template('patient_dashboard.html')








# --- Main run block ---
if __name__ == '__main__':
    app.run(debug=True)