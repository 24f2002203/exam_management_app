from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_security import current_user, hash_password, roles_required

from core.database import db
from core.models import (
    Booking, Course, Examination, ExaminationSlot, Role, StudentProfile, User,
)
from .forms import ActionForm, CancelForm, StudentRegisterForm

blueprint = Blueprint('student', __name__, url_prefix='/student')

EXAM_TYPES = [ 'Viva', 'Practical', 'Project']



def booking_is_open(exam):
    """Booking is open when the exam is scheduled and we are inside the booking window."""
    now = datetime.now()
    return (exam.status == 'Scheduled'
            and exam.booking_starts_at <= now <= exam.booking_ends_at)


def active_booking(student, exam_id):
    """The student's current 'Booked' booking for an exam, if any."""
    return (Booking.query
            .join(ExaminationSlot)
            .filter(Booking.student_id == student.id,
                    Booking.status == 'Booked',
                    ExaminationSlot.exam_id == exam_id)
            .first())




@blueprint.route('/dashboard')
@roles_required('student')
def dashboard():
    student = current_user.student_profile
    booked_count = Booking.query.filter_by(student_id=student.id, status='Booked').count()
    return render_template('student/dashboard.html', student=student, booked_count=booked_count)


@blueprint.route('/examinations')
@roles_required('student')
def examinations():
    now = datetime.now()
    q = request.args.get('q', '').strip()
    exam_type = request.args.get('exam_type', '')

    # Available = scheduled and currently inside the booking window
    query = (Examination.query
             .join(Course)
             .filter(Examination.status == 'Scheduled',
                     Examination.booking_starts_at <= now,
                     Examination.booking_ends_at >= now))

    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Examination.exam_name.ilike(like),
                                    Course.course_name.ilike(like),
                                    Course.course_code.ilike(like)))
    if exam_type:
        query = query.filter(Examination.exam_type == exam_type)

    exams = query.order_by(Examination.exam_date).all()
    return render_template('student/examinations.html', exams=exams, q=q,
                           exam_type=exam_type, exam_types=EXAM_TYPES)


@blueprint.route('/examinations/<int:exam_id>')
@roles_required('student')
def exam_detail(exam_id):
    exam = db.get_or_404(Examination, exam_id)
    student = current_user.student_profile

    slots = (ExaminationSlot.query
             .filter(ExaminationSlot.exam_id == exam.id,
                     ExaminationSlot.status == 'Scheduled',
                     ExaminationSlot.available_seats > 0)
             .order_by(ExaminationSlot.slot_date, ExaminationSlot.start_time)
             .all())

    return render_template('student/exam_detail.html', exam=exam, slots=slots,
                           is_open=booking_is_open(exam),
                           my_booking=active_booking(student, exam.id),
                           form=ActionForm())



@blueprint.route('/book/<int:slot_id>', methods=['POST'])
@roles_required('student')
def book(slot_id):
    slot = db.get_or_404(ExaminationSlot, slot_id)
    exam = slot.exam
    student = current_user.student_profile
    back = redirect(url_for('student.exam_detail', exam_id=exam.id))

    if not ActionForm().validate_on_submit():
        flash('Invalid request. Please try again.')
        return back
    if not booking_is_open(exam):
        flash('Booking is not open for this examination.')
        return back
    if slot.status != 'Scheduled' or slot.available_seats < 1:
        flash('This slot is no longer available.')
        return back
    if active_booking(student, exam.id):
        flash('You already have a booking for this examination.')
        return back

    booking = Booking.query.filter_by(student_id=student.id, slot_id=slot.slot_id).first()
    if booking is None:
        booking = Booking(student_id=student.id, slot_id=slot.slot_id)
        db.session.add(booking)

    booking.status = 'Booked'
    booking.booked_at = datetime.now()
    booking.cancelled_at = None
    booking.cancellation_reason = None
    slot.available_seats -= 1

    db.session.commit()
    flash('Slot booked successfully.')
    return redirect(url_for('student.bookings'))


@blueprint.route('/cancel/<int:booking_id>', methods=['POST'])
@roles_required('student')
def cancel(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    if booking.student_id != current_user.student_profile.id:
        abort(404)

    form = CancelForm()
    back = redirect(url_for('student.bookings'))

    if not form.validate_on_submit():
        flash('Invalid request. Please try again.')
    elif booking.status != 'Booked':
        flash('Only active bookings can be cancelled.')
    elif datetime.now() > booking.slot.exam.booking_ends_at:
        flash('The booking deadline has passed, so this booking can no longer be cancelled.')
    else:
        booking.status = 'Cancelled'
        booking.cancelled_at = datetime.now()
        booking.cancellation_reason = form.reason.data
        booking.slot.available_seats += 1
        db.session.commit()
        flash('Booking cancelled.')

    return back

@blueprint.route('/bookings')
@roles_required('student')
def bookings():
    student = current_user.student_profile
    my_bookings = (Booking.query
                   .filter_by(student_id=student.id)
                   .order_by(Booking.booked_at.desc())
                   .all())
    return render_template('student/bookings.html', bookings=my_bookings,
                           now=datetime.now(), form=CancelForm())


@blueprint.route('/history')
@roles_required('student')
def history():
    student = current_user.student_profile
    past = (Booking.query
            .filter(Booking.student_id == student.id,
                    Booking.status.in_(['Completed', 'Cancelled']))
            .order_by(Booking.booked_at.desc())
            .all())
    return render_template('student/history.html', bookings=past)


@blueprint.route('/results')
@roles_required('student')
def results():
    student = current_user.student_profile
    rows = []
    for booking in Booking.query.filter_by(student_id=student.id).all():
        exam = booking.slot.exam
        if not exam.results_published:
            continue
        for evaluation in booking.evaluations:
            if evaluation.status == 'Completed':
                rows.append((exam, evaluation))
    return render_template('student/results.html', rows=rows)