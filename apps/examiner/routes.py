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



def read_slot_form(exam, ignore_slot_id=0):
    """Reads and checks the slot form. Returns (data, error). One of them is None."""
    try:
        slot_date = datetime.strptime(request.form['slot_date'], '%Y-%m-%d')
        start = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end = datetime.strptime(request.form['end_time'], '%H:%M').time()
        seats = int(request.form['seats'])
    except (KeyError, ValueError):
        return None, 'Please fill in all fields correctly.'

    if end <= start:
        return None, 'End time must be after start time.'
    if not 1 <= seats <= exam.max_students:
        return None, f'Seats must be between 1 and {exam.max_students}.'

    # Does it overlap another slot of this examiner on the same day?
    overlap = ExaminationSlot.query.filter(
        ExaminationSlot.examiner_id == current_user.examiner_profile.id,
        ExaminationSlot.status == 'Scheduled',
        ExaminationSlot.slot_date == slot_date,
        ExaminationSlot.start_time < end,
        ExaminationSlot.end_time > start,
        ExaminationSlot.slot_id != ignore_slot_id,
    ).first()
    if overlap:
        return None, 'This overlaps one of your other slots.'

    data = {
        'slot_date': slot_date,
        'start_time': start,
        'end_time': end,
        'available_seats': seats,
    }
    return data, None

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


@blueprint.route('/exams/<int:exam_id>/slots/new', methods=['GET', 'POST'])
def create_slot(exam_id):
    exam = db.get_or_404(Examination, exam_id)
    profile = current_user.examiner_profile
    back = url_for('examiner.exam_detail', exam_id=exam.id)

    if exam.course not in profile.courses:
        abort(403)

    now = datetime.now()
    if not exam.slot_creation_starts_at <= now <= exam.slot_creation_ends_at:
        flash('Slot creation is not open for this examination.', 'danger')
        return redirect(back)

    if request.method == 'POST':
        data, error = read_slot_form(exam)
        if error:
            flash(error, 'danger')
        else:
            db.session.add(ExaminationSlot(exam_id=exam.id, examiner_id=profile.id, **data))
            db.session.commit()
            flash('Slot created.', 'success')
            return redirect(back)

    return render_template('examiner/slot_form.html', exam=exam, slot=None, back=back)


@blueprint.route('/slots/<int:slot_id>/edit', methods=['GET', 'POST'])
def edit_slot(slot_id):
    slot = db.get_or_404(ExaminationSlot, slot_id)
    back = url_for('examiner.exam_detail', exam_id=slot.exam_id)

    if slot.examiner_id != current_user.examiner_profile.id:
        abort(403)

    error = slot_change_error(slot)
    if error:
        flash(error, 'danger')
        return redirect(back)

    if request.method == 'POST':
        data, error = read_slot_form(slot.exam, ignore_slot_id=slot.slot_id)
        if error:
            flash(error, 'danger')
        else:
            slot.slot_date = data['slot_date']
            slot.start_time = data['start_time']
            slot.end_time = data['end_time']
            slot.available_seats = data['available_seats']
            db.session.commit()
            flash('Slot updated.', 'success')
            return redirect(back)

    return render_template('examiner/slot_form.html', exam=slot.exam, slot=slot, back=back)


@blueprint.route('/slots/<int:slot_id>/delete', methods=['POST'])
def delete_slot(slot_id):
    slot = db.get_or_404(ExaminationSlot, slot_id)
    exam_id = slot.exam_id

    if slot.examiner_id != current_user.examiner_profile.id:
        abort(403)

    error = slot_change_error(slot)
    if error:
        flash(error, 'danger')
    else:
        db.session.delete(slot)
        db.session.commit()
        flash('Slot removed.', 'success')

    return redirect(url_for('examiner.exam_detail', exam_id=exam_id))


# --------------------------------------------------------- evaluation

@blueprint.route('/bookings/<int:booking_id>/evaluate', methods=['GET', 'POST'])
def evaluate(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    profile = current_user.examiner_profile

    if booking.slot.examiner_id != profile.id:
        abort(403)

    exam = booking.slot.exam
    back = url_for('examiner.exam_detail', exam_id=exam.id)

    if booking.status == 'Cancelled':
        flash('This booking was cancelled.', 'danger')
        return redirect(back)
    if exam.results_published:
        flash('Results are already published, so marks can no longer change.', 'danger')
        return redirect(back)

    rubrics = (ExaminationRubrics.query
               .filter_by(exam_id=exam.id)
               .order_by(ExaminationRubrics.display_order)
               .all())
    if not rubrics:
        flash('No rubrics have been set for this examination yet.', 'danger')
        return redirect(back)

    # An earlier evaluation, if the examiner is editing marks
    evaluation = booking.evaluations[0] if booking.evaluations else None

    if request.method == 'POST':
        # Read one score for every rubric
        scores = {}
        error = None
        for rubric in rubrics:
            try:
                value = float(request.form[f'score_{rubric.rubric_id}'])
            except (KeyError, ValueError):
                error = f'Enter a score for "{rubric.criteria}".'
                break
            if not 0 <= value <= rubric.max_marks:
                error = f'Score for "{rubric.criteria}" must be between 0 and {rubric.max_marks}.'
                break
            scores[rubric.rubric_id] = value

        if error:
            flash(error, 'danger')
        else:
            # Create the evaluation the first time
            if evaluation is None:
                evaluation = Evaluation(booking=booking, examiner_id=profile.id,
                                        date_of_evaluation=datetime.now())
                db.session.add(evaluation)

            # Update old scores, add new ones
            old = {s.rubric_id: s for s in evaluation.scores}
            for rubric_id, value in scores.items():
                if rubric_id in old:
                    old[rubric_id].score = value
                else:
                    db.session.add(EvaluationScores(
                        evaluation=evaluation, rubric_id=rubric_id, score=value))

            evaluation.marks_obtained = sum(scores.values())
            evaluation.remarks = request.form.get('remarks', '').strip() or None
            evaluation.status = 'Completed'
            evaluation.submitted_at = datetime.now()
            booking.status = 'Completed'
            db.session.commit()

            flash('Marks and remarks submitted.', 'success')
            return redirect(back)

    old_scores = {}
    if evaluation:
        old_scores = {s.rubric_id: s.score for s in evaluation.scores}

    return render_template('examiner/evaluate.html', booking=booking, exam=exam,
                           rubrics=rubrics, evaluation=evaluation,
                           old_scores=old_scores, back=back)