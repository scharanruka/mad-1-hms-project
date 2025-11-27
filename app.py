from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Department, Doctor, Patient, Appointment, Treatment

# Forms
from forms import (LoginForm, RegistrationForm, AddDoctorForm,
 BookAppointmentForm, UpdateTreatmentForm, EditPatientForm, EditDoctorForm,
 UpdateTreatmentForm, UpdateAvailabilityForm, UpdatePatientProfileForm, SearchDoctorForm)

import os

from api import setup_api_routes

import json
from datetime import date, timedelta
from sqlalchemy import or_

# Helper functions
from helpers import generate_random_password, generate_username

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'

db.init_app(app)
setup_api_routes(app)


# ROUTES ------------------------------------
@app.route('/')
def index():
    return render_template('index.html')



# AUTH ROUTES -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm() 

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            if user.status == "blacklisted":
                flash("Your account has been blacklisted!")
                return redirect(url_for('login')) 

            session['user_id'] = user.id
            session['role'] = user.role
            
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')

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


    return render_template('register.html', form=form)
#-------------------------------------------------------------------


# Dashboard Routes -------------------------
#Using role based auth to restrisct and protect sessions
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
    patients = db.session.query(Patient, User).join(User, Patient.user_id == User.id).all()
    appointments = Appointment.query.filter_by(status="Booked").all()
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
    form.department.choices = [(d.id, str(d.name).capitalize()) for d in Department.query.all()]
    
    if form.validate_on_submit():
        # Update the doctor's data
        doctor.name = form.name.data
        doctor.department_id = form.department.data
        db.session.commit()
        flash('Doctor details updated successfully.')
        return redirect(url_for('admin_dashboard'))


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
    if 'user_id' not in session or session.get('role') != 'doctor':
        flash('Please log in as a doctor.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    # Get the logged-in doctor
    doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
    if not doctor:
        flash('Doctor profile not found.')
        return redirect(url_for('logout'))


    upcoming_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id, 
        status='Booked'
    ).all()
    

    upcoming_app_data = []
    for appt in upcoming_appointments:
        patient = Patient.query.get(appt.patient_id)
        upcoming_app_data.append({
            'appointment': appt,
            'patient_name': patient.name if patient else 'Unknown'
        })

 
    all_appts = Appointment.query.filter_by(doctor_id=doctor.id).all()
    patient_ids = {a.patient_id for a in all_appts} # Use a set for unique IDs
    assigned_patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()

    return render_template(
        'doctor_dashboard.html',
        doctor=doctor,
        upcoming_app_data=upcoming_app_data,
        assigned_patients=assigned_patients
    )


@app.route('/doctor/availability', methods=['GET', 'POST'])
def doctor_availability():
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'doctor':
        flash('Please log in as a doctor.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
    form = UpdateAvailabilityForm()

    # Generate the next 7 days
    today = date.today()
    # 'YYYY-MM-DD' format
    days = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    if form.validate_on_submit(): # This is a POST request
        availability_data = {}
        for i, day_key in enumerate(days):
            slots = []
            if form[f'day{i}_am'].data:
                slots.append('am')
            if form[f'day{i}_pm'].data:
                slots.append('pm')
            
            if slots: # Only add to dict if one or more slots are checked
                availability_data[day_key] = slots
        
        # Convert dict to JSON string and save to doctor
        doctor.availability = json.dumps(availability_data)
        db.session.commit()
        flash('Availability updated successfully.')
        return redirect(url_for('doctor_dashboard'))

    # This is a GET request, so we pre-load the form
    current_availability = json.loads(doctor.availability or '{}')
    for i, day_key in enumerate(days):
        if day_key in current_availability:
            if 'am' in current_availability[day_key]:
                form[f'day{i}_am'].data = True
            if 'pm' in current_availability[day_key]:
                form[f'day{i}_pm'].data = True

    return render_template('doctor_availability.html', form=form, days=days)



@app.route('/doctor/cancel_appointment/<int:app_id>')
def cancel_appointment(app_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'doctor':
        flash('Please log in as a doctor.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
    appointment = Appointment.query.get_or_404(app_id)

    # Check that this doctor owns this appointment
    if appointment.doctor_id != doctor.id:
        flash('You do not have permission to modify this appointment.')
        return redirect(url_for('doctor_dashboard'))

    appointment.status = 'Cancelled'
    db.session.commit()
    flash('Appointment has been cancelled.')
    return redirect(url_for('doctor_dashboard'))



@app.route('/doctor/update_treatment/<int:app_id>', methods=['GET', 'POST'])
def update_treatment(app_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'doctor':
        flash('Please log in as a doctor.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
    appointment = Appointment.query.get_or_404(app_id)
    department = Department.query.filter_by(id=doctor.department_id).first()
    patient = Patient.query.get(appointment.patient_id)

    
    # Check ownership
    if appointment.doctor_id != doctor.id:
        flash('You do not have permission.')
        return redirect(url_for('doctor_dashboard'))

    form = UpdateTreatmentForm()

    if form.validate_on_submit(): # POST request
        # Check if treatment already exists
        existing_treatment = Treatment.query.filter_by(appointment_id=app_id).first()
        if existing_treatment:
            # Update existing
            existing_treatment.diagnosis = form.diagnosis.data
            existing_treatment.prescription = form.prescription.data
        else:

            # Create new
            new_treatment = Treatment(
                appointment_id=app_id,
                diagnosis=form.diagnosis.data,
                prescription=form.prescription.data,
                visit_type=form.visit_type.data,
                test_done=form.test_done.data
            )
            db.session.add(new_treatment)
        
        # Mark appointment as completed
        appointment.status = 'Completed'
        db.session.commit()
        flash('Treatment saved and appointment marked as completed.')
        return redirect(url_for('doctor_dashboard'))

    # GET request
    return render_template(
        'update_treatment.html', 
        form=form, 
        appointment=appointment,
        patient=patient,
        department=department
    )



@app.route('/patient_history/<int:patient_id>')
def patient_history(patient_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') not in ('doctor', 'admin', 'patient'):
        flash('Unauthorized access')
        return redirect(url_for('login'))

    # Patient checking his own history
    if session.get('role') == 'patient':
        try:
            current_user_id = int(session.get('user_id'))
            patient = Patient.query.filter_by(id=patient_id).first()
            if not patient or patient.user_id != current_user_id:
                raise ValueError
            
        except:
            flash('Unauthorized access')
            return redirect(url_for('login'))

    # --- END OF CHECK ---

    patient = Patient.query.get_or_404(patient_id)
    doctor = Doctor.query.filter_by(user_id=session['user_id']).first()

    # Get all appointments for this patient (all doctors)
    all_appts = Appointment.query.filter_by(
        patient_id=patient.id,
        status="Completed"
    ).all()

    print(all_appts)

    # Get the treatment for each appointment
    history = []
    for appt in all_appts:
        treatment = Treatment.query.filter_by(appointment_id=appt.id).first()
        doctor_treated = Doctor.query.filter_by(id=appt.doctor_id).first()
        history.append({
            'appointment': appt,
            'treatment': treatment,  # This will be None if not completed
            'doctor': doctor_treated
        })

    return render_template(
        'patient_history.html', 
        patient=patient, 
        history=history
    )
# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
# PATIENT DASHBOARD ----------

@app.route('/patient/dashboard', methods=['GET', 'POST'])
def patient_dashboard():
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'patient':
        flash('Please log in as a patient.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    patient = Patient.query.filter_by(user_id=session['user_id']).first()
    departments = Department.query.all()


    # --- Get Upcoming Appointments ---
    upcoming_appts_query = db.session.query(Appointment, Doctor).join(
        Doctor, Appointment.doctor_id == Doctor.id
    ).filter(
        Appointment.patient_id == patient.id,
        Appointment.status == 'Booked'
    ).all()

    # --- Get Past Appointments ---
    past_appts_query = db.session.query(Appointment, Doctor).join(
        Doctor, Appointment.doctor_id == Doctor.id
    ).filter(
        Appointment.patient_id == patient.id,
        or_(Appointment.status == 'Completed', Appointment.status == 'Cancelled')
    ).all()
    
    # Get treatment info for completed appointments
    past_app_data = []
    for appt, doctor in past_appts_query:
        treatment = None
        if appt.status == 'Completed':
            treatment = Treatment.query.filter_by(appointment_id=appt.id).first()
        past_app_data.append({
            'appointment': appt,
            'doctor_name': doctor.name,
            'treatment': treatment
        })


    return render_template(
        'patient_dashboard.html', 
        patient=patient,
        departments=departments,
        upcoming_appts=upcoming_appts_query, 
        past_app_data=past_app_data 
    )



@app.route('/patient/profile', methods=['GET', 'POST'])
def patient_profile():
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'patient':
        flash('Please log in as a patient.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    patient = Patient.query.filter_by(user_id=session['user_id']).first()
    # `obj=patient` pre-populates the form with the patient's current data
    form = UpdatePatientProfileForm(obj=patient)

    if form.validate_on_submit():
        patient.name = form.name.data
        patient.contact = form.contact.data
        db.session.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('patient_profile'))

    return render_template('patient_profile.html', form=form, patient=patient)



@app.route('/patient/search')
def patient_search_doctors():
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'patient':
        flash('Please log in as a patient.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    query = request.args.get('query')
    if not query:
        return redirect(url_for('patient_dashboard'))

    # Search in both Doctor name and Department name
    # We join Doctor with Department to get the department's name
    search_results = db.session.query(Doctor, Department).join(
        Department, Doctor.department_id == Department.id
    ).filter(
        or_(
            Doctor.name.contains(query),
            Department.name.contains(query)
        )
    ).all() # This gives a list of (Doctor, Department) tuples

    return render_template('search_doctors.html', results=search_results, query=query)


@app.route('/patient/book/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'patient':
        flash('Please log in as a patient.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    doctor = Doctor.query.get_or_404(doctor_id)
    form = BookAppointmentForm()


    # Load the doctor's availability from the JSON string
    avail_dict = json.loads(doctor.availability or '{}')
    
    # Get existing appointments for this doctor to check for conflicts
    existing_appts = Appointment.query.filter_by(doctor_id=doctor.id).all()
    booked_slots = {f"{appt.appointment_date}" for appt in existing_appts}

    slot_choices = []
    today = date.today()
    for i in range(7): # For the next 7 days
        day = today + timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        
        if day_str in avail_dict:
            # Check AM slot
            if 'am' in avail_dict[day_str]:
                slot_id = f"{day_str} am" # e.g., "2025-11-12 am"
                if slot_id not in booked_slots:
                    label = f"{day_str} (Morning: 8am-12pm)"
                    slot_choices.append((slot_id, label))
            # Check PM slot
            if 'pm' in avail_dict[day_str]:
                slot_id = f"{day_str} pm" # e.g., "2025-11-12 pm"
                if slot_id not in booked_slots:
                    label = f"{day_str} (Evening: 4pm-9pm)"
                    slot_choices.append((slot_id, label))
    
    form.appointment_slot.choices = slot_choices

    if form.validate_on_submit():
        selected_slot = form.appointment_slot.data
        patient = Patient.query.filter_by(user_id=session['user_id']).first()

        # Final check just in case
        if selected_slot in booked_slots:
            flash('This slot was just booked. Please select another.')
            return redirect(url_for('book_appointment', doctor_id=doctor_id))

        # Create the new appointment
        new_appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=selected_slot,
            status='Booked'
        )
        db.session.add(new_appt)
        db.session.commit()

        flash('Appointment booked successfully!')
        return redirect(url_for('patient_dashboard'))

    return render_template(
        'book_appointment.html', 
        form=form, 
        doctor=doctor,
        has_slots=(len(slot_choices) > 0)
    )



@app.route('/patient/cancel/<int:app_id>')
def patient_cancel_appointment(app_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'patient':
        flash('Please log in as a patient.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    patient = Patient.query.filter_by(user_id=session['user_id']).first()
    appointment = Appointment.query.get_or_404(app_id)

    # Check that this patient owns this appointment
    if appointment.patient_id != patient.id:
        flash('You do not have permission to cancel this appointment.')
        return redirect(url_for('patient_dashboard'))

    # Only 'Booked' appointments can be cancelled
    if appointment.status == 'Booked':
        appointment.status = 'Cancelled'
        db.session.commit()
        flash('Appointment cancelled successfully.')
    else:
        flash('This appointment cannot be cancelled.')

    return redirect(url_for('patient_dashboard'))



@app.route('/patient/reschedule/<int:app_id>', methods=['GET', 'POST'])
def patient_reschedule_appointment(app_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'patient':
        flash('Please log in as a patient.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    patient = Patient.query.filter_by(user_id=session['user_id']).first()
    appointment = Appointment.query.get_or_404(app_id)
    doctor = Doctor.query.get(appointment.doctor_id)

    # Check ownership and status
    if appointment.patient_id != patient.id or appointment.status != 'Booked':
        flash('This appointment cannot be rescheduled.')
        return redirect(url_for('patient_dashboard'))
    
    # We can reuse the BookAppointmentForm
    form = BookAppointmentForm()
    form.submit.label.text = 'Reschedule' # Change button text

    # --- Generate available slots (same logic as booking) ---
    avail_dict = json.loads(doctor.availability or '{}')
    existing_appts = Appointment.query.filter_by(doctor_id=doctor.id).all()
    
    booked_slots = {
        f"{appt.appointment_date}" for appt in existing_appts 
        if appt.id != appointment.id # Allow picking the same slot
    }
    
    slot_choices = []
    today = date.today()
    for i in range(7):
        day = today + timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        if day_str in avail_dict:
            if 'am' in avail_dict[day_str]:
                slot_id = f"{day_str} am"
                if slot_id not in booked_slots:
                    label = f"{day_str} (Morning: 8am-12pm)"
                    slot_choices.append((slot_id, label))
            if 'pm' in avail_dict[day_str]:
                slot_id = f"{day_str} pm"
                if slot_id not in booked_slots:
                    label = f"{day_str} (Evening: 4pm-9pm)"
                    slot_choices.append((slot_id, label))
    
    form.appointment_slot.choices = slot_choices

    if form.validate_on_submit():
        new_slot = form.appointment_slot.data
        
        # Update the appointment
        appointment.appointment_date = new_slot
        db.session.commit()
        
        flash('Appointment rescheduled successfully!')
        return redirect(url_for('patient_dashboard'))

    return render_template(
        'reschedule_appointment.html',
        form=form,
        doctor=doctor,
        appointment=appointment,
        has_slots=(len(slot_choices) > 0)
    )




@app.route('/admin/add_doctor', methods=['GET','POST'])
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
    

    departments = Department.query.all()
    form.department.choices = [(d.id, str(d.name).capitalize()) for d in departments]

    if form.validate_on_submit():
        # Get data from the form
        name = form.name.data
        # username = form.username.data
        # password = form.password.data
        dept_id = form.department.data
        specialization = form.specialization.data
        experience = form.experience.data
        dob = form.dob.data
        qualifications = form.qualifications.data

        gen_username=  generate_username(name)
        gen_password= generate_random_password()


        # Create the new User for the doctor
        hashed_password = generate_password_hash(gen_password, method='pbkdf2:sha256')

        new_user = User(
            username=gen_username,
            password=hashed_password,
            role='doctor'
            
        )
        db.session.add(new_user)
        db.session.commit() # Commit to get the new_user.id

        # Create the associated Doctor profile
        new_doctor = Doctor(
            name=name,
            department_id=dept_id,
            user_id=new_user.id,
            dob=dob,
            specialization=specialization,
            experience=experience,
            qualifications=qualifications
        )
        db.session.add(new_doctor)
        db.session.commit()

        return render_template(
                    'doctor_credentials_success.html', 
                    name=name,
                    username=gen_username,
                    password=gen_password
                )
    else:
        # Errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}')
    
    return render_template('create_doctor.html', form=form)



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



@app.route('/admin/view_treatment/<int:app_id>')
def admin_view_treatment(app_id):
    # --- SIMPLE AUTH CHECK ---
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission.')
        return redirect(url_for('login'))
    # --- END OF CHECK ---

    # Get all details for this one appointment
    appointment = Appointment.query.get_or_404(app_id)
    patient = Patient.query.get(appointment.patient_id)
    doctor = Doctor.query.get(appointment.doctor_id)
    treatment = Treatment.query.filter_by(appointment_id=app_id).first()

    # treatment will be None if the status isn't 'Completed'
    
    return render_template(
        'admin_view_treatment.html',
        appointment=appointment,
        patient=patient,
        doctor=doctor,
        treatment=treatment
    )



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


    query = request.args.get('query')

    if not query:
        flash('Please enter a search term.')
        return redirect(url_for('admin_dashboard'))

    # Search for patients and doctors using .contains() for partial matching
    patients = Patient.query.filter(Patient.name.contains(query)).all()
    doctors = Doctor.query.filter(Doctor.name.contains(query)).all()
    departments = Department.query.filter(Department.name.contains(query)).all()


    return render_template(
        'search_results.html', 
        patients=patients, 
        doctors=doctors, 
        departments=departments,
        query=query
    )

# DEPARTMENT DETAILS ----------
@app.route('/departments/<string:department_name>')
def department_details(department_name):
    dept = Department.query.filter_by(name=department_name).first_or_404()
    doctors = Doctor.query.filter_by(department_id=dept.id).all()
    
    return render_template('department_details.html', department=dept, doctors=doctors)

@app.route('/doctor/profile/<int:doctor_id>')
def doctor_public_profile(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    department = Department.query.filter_by(id=doctor.department_id).first()
    
    return render_template('doctor_details.html', doctor=doctor, department=department)


# --- Main run block ---
if __name__ == '__main__':
    app.run(debug=True)