from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_security import current_user, hash_password, roles_required

from core.database import db
from core.models import (
    Booking
)


blueprint = Blueprint('student', __name__, url_prefix='/student')

EXAM_TYPES = [ 'Viva', 'Practical', 'Project']

@blueprint.route('/dashboard')
@roles_required('student')
def dashboard():
    student = current_user.student_profile
    booked_count = Booking.query.filter_by(student_id=student.id, status='Booked').count()
    return render_template('student/dashboard.html', student=student, booked_count=booked_count)