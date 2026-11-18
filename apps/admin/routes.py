from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app as app 
from core.models import User, Course, Examination, ExaminerProfile, StudentProfile, ExaminationSlot, ExaminationRubrics, Booking


blueprint = Blueprint(
    'admin', 
    __name__, 
    url_prefix='/admin',
    template_folder='templates/admin',
)
@blueprint.route('/dashboard')
def dashboard():
    stats = {
        'courses': Course.query.count(),
        'examinations': Examination.query.count(),
        'examiners': ExaminerProfile.query.count(),
        'students': StudentProfile.query.count(),
        'slots': ExaminationSlot.query.count(),
        'bookings': Booking.query.filter_by(status='Booked').count(),
        'pending': User.query.filter_by(status='pending').count(),
    }
    open_exams = Examination.query.filter(or_(
        Examination.slot_creation_open.is_(True),
        Examination.booking_open.is_(True))).all()
    return render_template('admin/dashboard.html', stats=stats, open_exams=open_exams)