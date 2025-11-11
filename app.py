from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Department, Doctor, Patient, Appointment, Treatment

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