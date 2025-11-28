from flask import request
from flask_restful import Resource, Api
from datetime import date, datetime 

from models import db, Doctor, Patient, Appointment 

# BASIC API TO ONLY GET DOCTORS, PATIENTS AND APPOINTMENT DATA -------

# Converts a single SQLAlchemy object to a dictionary dynamically
def serialize_object(obj):
    if obj is None:
        return None
    
    # Use table.columns to dynamically get all column names and values
    fields = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        
        # Datetime conversion
        if isinstance(value, (date, datetime)):
            fields[column.name] = value.isoformat()
        else:
            fields[column.name] = value
    
    return fields

# Converts a list of SQLAlchemy objects to a list of dictionaries
def serialize_list(query_result):
    return [serialize_object(obj) for obj in query_result]

# ---

class DoctorList(Resource):
    def get(self):
        doctors = Doctor.query.all()
        return serialize_list(doctors)

class DoctorDetail(Resource):
    def get(self, id):
        # Get a doctor by ID api/doctors/<id>
        doctor = Doctor.query.get(id)
        if not doctor:
            return {'message': 'Doctor not found'}, 404
        return serialize_object(doctor)


#----
class PatientList(Resource):
    def get(self):
        patients = Patient.query.all()
        return serialize_list(patients)


class PatientDetail(Resource):
    def get(self, id):
        # Get patient by ID
        patient = Patient.query.get(id)
        if not patient:
            return {'message': 'Patient not found'}, 404
        return serialize_object(patient)

# ----
class AppointmentList(Resource):
    def get(self):
        appts = Appointment.query.all()
        return serialize_list(appts)


class AppointmentDetail(Resource):
    def get(self, id):
        appt = Appointment.query.get(id)
        if not appt:
            return {'message': 'Appointment not found'}, 404
        return serialize_object(appt)


def setup_api_routes(app):
    """Initializes Flask-RESTful and adds resources under /api."""
    api = Api(app, prefix='/api')

    # Doctor Endpoints
    api.add_resource(DoctorList, '/doctors/')
    api.add_resource(DoctorDetail, '/doctors/<int:id>')

    # Patient Endpoints
    api.add_resource(PatientList, '/patients/')
    api.add_resource(PatientDetail, '/patients/<int:id>')

    # Appointment Endpoints
    api.add_resource(AppointmentList, '/appointments/')
    api.add_resource(AppointmentDetail, '/appointments/<int:id>')
