from models import db, User, Department
from app import app

from werkzeug.security import generate_password_hash

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
            default_depts = {
    'Cardiology': "This department specializes in the diagnosis and treatment of conditions affecting the **heart** and **blood vessels**, such as heart attacks and arrhythmias. They manage patient care using advanced monitoring and surgical procedures.",
    'Neurology': "Focused on disorders of the **nervous system**, including the brain, spinal cord, and nerves. Neurologists diagnose and treat conditions like strokes, epilepsy, Parkinson's disease, and multiple sclerosis.",
    'Oncology': "The Oncology department provides care for patients diagnosed with **cancer**. Services include diagnosis, chemotherapy, radiation therapy, and ongoing palliative care for tumor management.",
    'Orthopedics': "Specializes in the prevention, diagnosis, and treatment of **musculoskeletal** system injuries and diseases. This covers bones, joints, ligaments, tendons, and muscles, often involving surgical repair or replacement.",
    'Pediatrics': "Dedicated to providing medical care for **infants, children, and adolescents**. Pediatricians manage their unique health, growth, and development needs, from routine check-ups to complex illnesses."
}
            
            for dept_name in default_depts:
                new_dept = Department(name=dept_name, details=default_depts[dept_name])
                db.session.add(new_dept)
                
            print(f"Created {len(default_depts)} departments.")
        else:
            print("Departments already exist.")

        # Commit all changes to the database
        db.session.commit()
        print("Database setup complete.")

if __name__ == "__main__":
    create_db_and_admin()