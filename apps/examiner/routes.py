from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_security import auth_required, current_user, roles_required

from core.database import db
from core.models import (
    Booking, Evaluation, EvaluationScores, Examination,
    ExaminationRubrics, ExaminationSlot,
)

blueprint = Blueprint('examiner', __name__, url_prefix='/examiner')

def slot_change_error(slot):
    """Returns a message if the slot can't be edited or deleted, otherwise None."""
    if datetime.now() >= slot.exam.booking_starts_at:
        return 'Slots can only be changed before booking starts.'
    for booking in slot.bookings:
        if booking.status == 'Booked':
            return 'This slot already has bookings.'
    return None

@blueprint.route('/dashboard')
def dashboard():
    """Exams of the courses assigned to this examiner."""
    course_ids = [course.id for course in current_user.examiner_profile.courses]
    exams = (Examination.query
             .filter(Examination.course_id.in_(course_ids))
             .order_by(Examination.exam_date)
             .all())
    return render_template('examiner/dashboard.html', exams=exams)

@blueprint.route('/exams/<int:exam_id>')
def exam_detail(exam_id):
    """One exam: my slots, the students booked in each, and links to evaluate them."""
    exam = db.get_or_404(Examination, exam_id)
    profile = current_user.examiner_profile

    if exam.course not in profile.courses:
        abort(403)

    slots = (ExaminationSlot.query
             .filter_by(exam_id=exam.id, examiner_id=profile.id)
             .order_by(ExaminationSlot.slot_date, ExaminationSlot.start_time)
             .all())

    now = datetime.now()
    can_create = exam.slot_creation_starts_at <= now <= exam.slot_creation_ends_at

    return render_template('examiner/exam_detail.html', exam=exam, slots=slots,
                           can_create=can_create, change_error=slot_change_error)