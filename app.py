from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Department, Doctor, Patient, Appointment, Treatment

# Forms
from forms import (LoginForm, RegistrationForm, AddDoctorForm,
 BookAppointmentForm, UpdateTreatmentForm, EditPatientForm, EditDoctorForm)

import os

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
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
                        role='admin',
                        status='active'
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

    # Get stats for the dashboard
    doctor_count = Doctor.query.count()
    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()

    # Get lists for management
    # doctors = Doctor.query.all()
    doctors = db.session.query(Doctor, User).join(User, Doctor.user_id == User.id).all()
    # patients = Patient.query.all()
    patients = db.session.query(Patient, User).join(User, Patient.user_id == User.id).all()
    appointments = Appointment.query.all()
    departments = Department.query.all()

    form = AddDoctorForm()
    form.department.choices = [(d.id, d.name) for d in departments]

    return render_template(
        'admin_dashboard.html',
        doctor_count=doctor_count,
        patient_count=patient_count,
        appointment_count=appointment_count,
        doctors=doctors, # (Doctor, User)
        patients=patients, # (Patient, User)
        appointments=appointments,
        form=form  # pass the form to the template
    )

@app.route('/admin/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    doctor = Doctor.query.get_or_404(doctor_id)
    # `obj=doctor` pre-populates the form with the doctor's current data
    form = EditDoctorForm(obj=doctor)
    
    # Populate department choices
    form.department.choices = [(d.id, d.name) for d in Department.query.all()]
    
    if form.validate_on_submit():
        # Update the doctor's data
        doctor.name = form.name.data
        doctor.department_id = form.department.data
        db.session.commit()
        flash('Doctor details updated successfully.')
        return redirect(url_for('admin_dashboard'))

    # On a GET request, pre-select the doctor's current department
    if request.method == 'GET':
        form.department.data = doctor.department_id

    return render_template('edit_doctor.html', form=form, doctor=doctor)


@app.route('/admin/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    patient = Patient.query.get_or_404(patient_id)
    # `obj=patient` pre-populates the form
    form = EditPatientForm(obj=patient)
    
    if form.validate_on_submit():
        patient.name = form.name.data
        patient.contact = form.contact.data
        db.session.commit()
        flash('Patient details updated successfully.')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_patient.html', form=form, patient=patient)


@app.route('/admin/toggle_blacklist/<int:user_id>')
def toggle_blacklist(user_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    user = User.query.get_or_404(user_id)

    # Prevent admin from blacklisting themselves or other admins
    if user.role == 'admin':
        flash('You cannot blacklist an admin account.')
        return redirect(url_for('admin_dashboard'))
    
    # Toggle the status
    if user.status == 'active':
        user.status = 'blacklisted'
        flash(f'User {user.username} has been blacklisted.')
    else:
        user.status = 'active'
        flash(f'User {user.username} has been activated.')
        
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


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


# 2. --- ADD THE 'ADD_DOCTOR' ROUTE ---

@app.route('/admin/add_doctor', methods=['POST'])
def add_doctor():
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('dashboard'))
    # --- END OF CHECK ---

    form = AddDoctorForm()
    
    # We must populate choices *again* here, in case validation fails
    # and we need to re-render the dashboard.
    departments = Department.query.all()
    form.department.choices = [(d.id, d.name) for d in departments]

    if form.validate_on_submit():
        # Get data from the form
        name = form.name.data
        username = form.username.data
        password = form.password.data
        dept_id = form.department.data

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another.')
            return redirect(url_for('admin_dashboard'))

        # Create the new User for the doctor
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            username=username,
            password=hashed_password,
            role='doctor'
        )
        db.session.add(new_user)
        db.session.commit() # Commit to get the new_user.id

        # Create the associated Doctor profile
        new_doctor = Doctor(
            name=name,
            department_id=dept_id,
            user_id=new_user.id
        )
        db.session.add(new_doctor)
        db.session.commit()

        flash(f'Doctor {name} added successfully.')
    else:
        # If validation fails, flash the errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}')
    
    return redirect(url_for('admin_dashboard'))


# 3. --- ADD THE 'REMOVE_USER' ROUTE ---

@app.route('/admin/remove_user/<int:user_id>')
def remove_user(user_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('dashboard'))
    # --- END OF CHECK ---

    # Find the user to delete
    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        flash('User not found.')
        return redirect(url_for('admin_dashboard'))

    # Prevent admin from deleting themselves
    if user_to_delete.id == session.get('user_id'):
        flash('You cannot remove your own admin account.')
        return redirect(url_for('admin_dashboard'))

    # Manually delete the associated profile (Doctor or Patient)
    # This is necessary because we removed db.relationship
    if user_to_delete.role == 'doctor':
        doctor_profile = Doctor.query.filter_by(user_id=user_id).first()
        if doctor_profile:
            # You might want to handle appointments first, e.g.,
            # Appointment.query.filter_by(doctor_id=doctor_profile.id).delete()
            db.session.delete(doctor_profile)
    
    elif user_to_delete.role == 'patient':
        patient_profile = Patient.query.filter_by(user_id=user_id).first()
        if patient_profile:
            # Appointment.query.filter_by(patient_id=patient_profile.id).delete()
            db.session.delete(patient_profile)
    
    # Now delete the User
    db.session.delete(user_to_delete)
    db.session.commit()

    flash(f'User {user_to_delete.username} has been removed.')
    return redirect(url_for('admin_dashboard'))

# 4. --- ADD THE 'ADMIN_SEARCH' ROUTE ---

@app.route('/admin/search')
def admin_search():
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('dashboard'))
    # --- END OF CHECK ---

    # Get the search query from the URL (e.g., /admin/search?query=test)
    query = request.args.get('query')

    if not query:
        flash('Please enter a search term.')
        return redirect(url_for('admin_dashboard'))

    # Search for patients and doctors using .contains() for partial matching
    patients = Patient.query.filter(Patient.name.contains(query)).all()
    doctors = Doctor.query.filter(Doctor.name.contains(query)).all()

    return render_template(
        'search_results.html', 
        patients=patients, 
        doctors=doctors, 
        query=query
    )



# --- Main run block ---
if __name__ == '__main__':
    app.run(debug=True)