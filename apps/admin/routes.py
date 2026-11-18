from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_security import auth_required, current_user, roles_required
from flask_security.utils import hash_password
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from core.database import db
from core.models import (
    Booking, BookingReschedules, Course, Examination, ExaminationRubrics,
    ExaminationSlot, ExaminerProfile, Role, SlotExaminerChanges,
    StudentProfile, User,
)
from .forms import (
    TIMELINE_FIELDS, ChangeExaminerForm, CourseForm, ExaminationForm,
    ExaminerCreateForm, ExaminerProfileForm, RescheduleForm, RubricForm,
    StudentProfileForm, TimelineForm, add_error,
)

SEARCH_LIMIT = 20
PER_PAGE = 25
FULL_NAME = User.first_name + ' ' + User.last_name

blueprint = Blueprint('admin', __name__, url_prefix='/admin')


def search_filter(q, columns):
    return or_(*[column.ilike(f'%{q}%') for column in columns])


def save(success, failure='Could not save the changes.'):
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(failure, 'danger')
        return False
    flash(success, 'success')
    return True

@blueprint.before_request
@auth_required()
@roles_required('admin')
def require_admin():
    pass


def course_choices(field):
    courses = Course.query.order_by(Course.course_code).all()
    field.choices = [(c.id, f'{c.course_code} - {c.course_name}') for c in courses]


def fill_course(course, form):
    course.course_code = form.course_code.data.strip().upper()
    course.course_name = form.course_name.data.strip()
    course.description = (form.description.data or '').strip() or None
    course.program = form.program.data.strip()
    course.department = form.department.data.strip()
    course.credits = form.credits.data
    course.semester = form.semester.data.strip()
    course.year_of_study = form.year_of_study.data


def fill_exam(exam, form):
    exam.course_id = form.course_id.data
    exam.exam_name = form.exam_name.data.strip()
    exam.exam_type = form.exam_type.data
    exam.max_marks = form.max_marks.data
    exam.description = (form.description.data or '').strip() or None
    exam.exam_date = datetime.combine(form.exam_date.data, datetime.min.time())
    exam.start_time = form.start_time.data
    exam.duration = form.duration.data
    exam.venue = form.venue.data.strip()
    exam.max_students = form.max_students.data
    exam.status = form.status.data
    for name in TIMELINE_FIELDS:
        setattr(exam, name, getattr(form, name).data)

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

@blueprint.route('/search')
def search():
    q = request.args.get('q', '').strip()
    results = {}

    if q:
        students = (StudentProfile.query.join(User)
                    .filter(search_filter(q, [User.first_name, User.last_name, FULL_NAME,
                                              User.email, StudentProfile.roll_number]))
                    .limit(SEARCH_LIMIT).all())

        examiners = (ExaminerProfile.query.join(User)
                     .filter(search_filter(q, [User.first_name, User.last_name, FULL_NAME,
                                               User.email, ExaminerProfile.department,
                                               ExaminerProfile.designation]))
                     .limit(SEARCH_LIMIT).all())

        examinations = (Examination.query.join(Course)
                        .filter(search_filter(q, [Examination.exam_name, Examination.exam_type,
                                                  Examination.venue, Course.course_code,
                                                  Course.course_name]))
                        .limit(SEARCH_LIMIT).all())

        bookings = (Booking.query
                    .join(StudentProfile, Booking.student_id == StudentProfile.id)
                    .join(User, StudentProfile.user_id == User.id)
                    .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.slot_id)
                    .join(Examination, ExaminationSlot.exam_id == Examination.id)
                    .filter(search_filter(q, [User.first_name, User.last_name, FULL_NAME,
                                              StudentProfile.roll_number, Examination.exam_name]))
                    .limit(SEARCH_LIMIT).all())

        courses = (Course.query
                   .filter(search_filter(q, [Course.course_code, Course.course_name,
                                             Course.department, Course.program]))
                   .limit(SEARCH_LIMIT).all())

        results = {
            'students': students,
            'examiners': examiners,
            'examinations': examinations,
            'bookings': bookings,
            'courses': courses,
        }

    return render_template('admin/search.html', q=q, results=results)

@blueprint.route('/courses')
def view_all_courses():
    q = request.args.get('q', '').strip()
    page_number = request.args.get('page', 1, type=int)

    query = Course.query
    if q:
        query = query.filter(search_filter(q, [Course.course_code, Course.course_name,
                                               Course.department, Course.program]))
    page = query.order_by(Course.course_code).paginate(
        page=page_number, per_page=PER_PAGE, error_out=False)
    return render_template('admin/courses.html', page=page, q=q)


@blueprint.route('/courses/create', methods=['GET', 'POST'])
def create_course():
    form = CourseForm()

    if form.validate_on_submit():
        code = form.course_code.data.strip().upper()
        if Course.query.filter_by(course_code=code).first():
            add_error(form.course_code, 'A course with this code already exists.')
        else:
            course = Course()
            fill_course(course, form)
            db.session.add(course)
            if save('Course created.'):
                return redirect(url_for('admin.view_all_courses'))

    return render_template('admin/form.html', form=form, title='Create course',
                           cancel_url=url_for('admin.view_all_courses'))

@blueprint.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
def update_course(course_id):
    course = db.get_or_404(Course, course_id)
    form = CourseForm(obj=course)

    if form.validate_on_submit():
        code = form.course_code.data.strip().upper()
        other = Course.query.filter(Course.course_code == code, Course.id != course.id).first()
        if other:
            add_error(form.course_code, 'Another course already uses this code.')
        else:
            fill_course(course, form)
            if save('Course updated.'):
                return redirect(url_for('admin.view_all_courses'))

    return render_template('admin/form.html', form=form, title=f'Edit course {course.course_code}',
                           cancel_url=url_for('admin.view_all_courses'))

@blueprint.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course = db.get_or_404(Course, course_id)

    if course.examinations:
        flash('This course has examinations and cannot be deleted.', 'danger')
    else:
        db.session.delete(course)
        save('Course deleted.', 'Could not delete the course.')

    return redirect(url_for('admin.view_all_courses'))

@blueprint.route('/examinations')
def view_all_examinations():
    q = request.args.get('q', '').strip()
    page_number = request.args.get('page', 1, type=int)

    query = Examination.query.join(Course)
    if q:
        query = query.filter(search_filter(q, [Examination.exam_name, Examination.exam_type,
                                               Examination.venue, Course.course_code,
                                               Course.course_name]))
    page = query.order_by(Examination.exam_date.desc()).paginate(
        page=page_number, per_page=PER_PAGE, error_out=False)
    return render_template('admin/examinations.html', page=page, q=q)

@blueprint.route('/examinations/create', methods=['GET', 'POST'])
def create_examination():
    if not Course.query.first():
        flash('Create a course first, then add its examinations.', 'danger')
        return redirect(url_for('admin.create_course'))

    form = ExaminationForm()
    course_choices(form.course_id)

    if form.validate_on_submit():
        exam = Examination()
        fill_exam(exam, form)
        db.session.add(exam)
        if save('Examination created. Add its rubrics next.'):
            return redirect(url_for('admin.examination_detail', exam_id=exam.id))

    return render_template('admin/form.html', form=form, title='Create examination',
                           cancel_url=url_for('admin.view_all_examinations'))

@blueprint.route('/examinations/<int:exam_id>')
def examination_detail(exam_id):
    exam = db.get_or_404(Examination, exam_id)
    rubrics = (ExaminationRubrics.query.filter_by(exam_id=exam.id)
               .order_by(ExaminationRubrics.display_order).all())
    rubric_total = sum(r.max_marks for r in rubrics)
    return render_template('admin/examination_detail.html', exam=exam,
                           rubrics=rubrics, rubric_total=rubric_total)

@blueprint.route('/examinations/<int:exam_id>/edit', methods=['GET', 'POST'])
def update_examination(exam_id):
    exam = db.get_or_404(Examination, exam_id)
    form = ExaminationForm(obj=exam)
    course_choices(form.course_id)
    back = url_for('admin.examination_detail', exam_id=exam.id)

    if form.validate_on_submit():
        rubrics = ExaminationRubrics.query.filter_by(exam_id=exam.id).all()
        used = sum(r.max_marks for r in rubrics)

        if form.max_marks.data < used:
            add_error(form.max_marks, f'Rubrics already add up to {used} marks. Lower them first.')
        else:
            fill_exam(exam, form)
            if save('Examination updated.'):
                return redirect(back)

    return render_template('admin/form.html', form=form, title=f'Edit {exam.exam_name}',
                           cancel_url=back)

@blueprint.route('/examinations/<int:exam_id>/delete', methods=['POST'])
def delete_examination(exam_id):
    exam = db.get_or_404(Examination, exam_id)

    if exam.slots:
        flash('This examination has slots. Set its status to Cancelled instead of deleting it.', 'danger')
        return redirect(url_for('admin.examination_detail', exam_id=exam.id))

    ExaminationRubrics.query.filter_by(exam_id=exam.id).delete()
    db.session.delete(exam)
    save('Examination deleted.', 'Could not delete the examination.')
    return redirect(url_for('admin.view_all_examinations'))

@blueprint.route('/examinations/<int:exam_id>/timeline', methods=['GET', 'POST'])
def update_timeline(exam_id):
    exam = db.get_or_404(Examination, exam_id)
    form = TimelineForm(obj=exam)
    back = url_for('admin.examination_detail', exam_id=exam.id)

    if form.validate_on_submit():
        for name in TIMELINE_FIELDS:
            setattr(exam, name, getattr(form, name).data)
        if save('Timeline updated.'):
            return redirect(back)

    return render_template('admin/form.html', form=form, title=f'Timeline for {exam.exam_name}',
                           cancel_url=back)


@blueprint.route('/examinations/<int:exam_id>/<phase>/<state>', methods=['POST'])
def set_phase(exam_id, phase, state):
    """Manually open or close slot creation or booking for an exam."""
    if phase not in ('slot-creation', 'booking') or state not in ('open', 'close'):
        abort(404)

    exam = db.get_or_404(Examination, exam_id)
    opening = state == 'open'

    if opening and exam.status != 'Scheduled':
        flash(f'Cannot open this phase for a {exam.status.lower()} examination.', 'danger')
    elif opening and phase == 'booking' and not exam.slots:
        flash('Cannot open booking: no examiner has created slots yet.', 'danger')
    else:
        word = 'opened' if opening else 'closed'
        if phase == 'slot-creation':
            exam.slot_creation_open = opening
            save(f'Slot creation {word}.')
        else:
            exam.booking_open = opening
            save(f'Booking {word}.')

    return redirect(url_for('admin.examination_detail', exam_id=exam.id))

@blueprint.route('/examinations/<int:exam_id>/rubrics/create', methods=['GET', 'POST'])
def create_rubric(exam_id):
    exam = db.get_or_404(Examination, exam_id)
    form = RubricForm()
    back = url_for('admin.examination_detail', exam_id=exam.id)
    rubrics = ExaminationRubrics.query.filter_by(exam_id=exam.id).all()

    if request.method == 'GET':
        form.display_order.data = max([r.display_order for r in rubrics], default=0) + 1

    if form.validate_on_submit():
        remaining = exam.max_marks - sum(r.max_marks for r in rubrics)

        if form.max_marks.data > remaining:
            add_error(form.max_marks,
                      f"Only {remaining} of the examination's {exam.max_marks} marks are unassigned.")
        else:
            rubric = ExaminationRubrics(exam_id=exam.id)
            rubric.criteria = form.criteria.data.strip()
            rubric.description = (form.description.data or '').strip() or None
            rubric.weightage = form.weightage.data
            rubric.max_marks = form.max_marks.data
            rubric.display_order = form.display_order.data
            db.session.add(rubric)
            if save('Rubric added.'):
                return redirect(back)

    return render_template('admin/form.html', form=form, title=f'Add rubric to {exam.exam_name}',
                           cancel_url=back)

@blueprint.route('/rubrics/<int:rubric_id>/edit', methods=['GET', 'POST'])
def update_rubric(rubric_id):
    rubric = db.get_or_404(ExaminationRubrics, rubric_id)
    exam = db.get_or_404(Examination, rubric.exam_id)
    form = RubricForm(obj=rubric)
    back = url_for('admin.examination_detail', exam_id=exam.id)

    if form.validate_on_submit():
        # marks used by the OTHER rubrics of this exam
        others = ExaminationRubrics.query.filter(
            ExaminationRubrics.exam_id == exam.id,
            ExaminationRubrics.rubric_id != rubric.rubric_id).all()
        remaining = exam.max_marks - sum(r.max_marks for r in others)

        if form.max_marks.data > remaining:
            add_error(form.max_marks,
                      f"Only {remaining} of the examination's {exam.max_marks} marks are unassigned.")
        else:
            rubric.criteria = form.criteria.data.strip()
            rubric.description = (form.description.data or '').strip() or None
            rubric.weightage = form.weightage.data
            rubric.max_marks = form.max_marks.data
            rubric.display_order = form.display_order.data
            if save('Rubric updated.'):
                return redirect(back)

    return render_template('admin/form.html', form=form, title='Edit rubric', cancel_url=back)


@blueprint.route('/rubrics/<int:rubric_id>/delete', methods=['POST'])
def delete_rubric(rubric_id):
    rubric = db.get_or_404(ExaminationRubrics, rubric_id)
    exam_id = rubric.exam_id

    if rubric.scores:
        flash('This rubric already has evaluation scores and cannot be deleted.', 'danger')
    else:
        db.session.delete(rubric)
        save('Rubric deleted.', 'Could not delete the rubric.')

    return redirect(url_for('admin.examination_detail', exam_id=exam_id))


@blueprint.route('/examiners')
def view_all_examiners():
    q = request.args.get('q', '').strip()
    page_number = request.args.get('page', 1, type=int)

    query = ExaminerProfile.query.join(User)
    if q:
        query = query.filter(search_filter(q, [User.first_name, User.last_name, FULL_NAME,
                                               User.email, ExaminerProfile.department,
                                               ExaminerProfile.designation]))
    page = query.order_by(User.first_name, User.last_name).paginate(
        page=page_number, per_page=PER_PAGE, error_out=False)
    return render_template('admin/examiners.html', page=page, q=q)


@blueprint.route('/examiners/create', methods=['GET', 'POST'])
def create_examiner():
    form = ExaminerCreateForm()
    course_choices(form.courses)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        role = Role.query.filter_by(name='examiner').first()

        if User.query.filter_by(email=email).first():
            add_error(form.email, 'A user with this email already exists.')
        elif not role:
            flash('The examiner role is not configured. Run the seed command.', 'danger')
        else:
            user = User(
                first_name=form.first_name.data.strip().title(),
                last_name=form.last_name.data.strip().title(),
                email=email,
                password=hash_password(form.password.data),
                roles=[role],
                status='approved',
                active=True,
            )
            profile = ExaminerProfile(user=user)
            profile.department = form.department.data.strip()
            profile.designation = form.designation.data.strip()
            profile.courses = Course.query.filter(Course.id.in_(form.courses.data or [])).all()
            db.session.add_all([user, profile])
            if save('Examiner added.', 'Could not add the examiner.'):
                return redirect(url_for('admin.view_all_examiners'))

    return render_template('admin/form.html', form=form, title='Add examiner',
                           cancel_url=url_for('admin.view_all_examiners'))

@blueprint.route('/examiners/<int:examiner_id>/edit', methods=['GET', 'POST'])
def update_examiner(examiner_id):
    profile = db.get_or_404(ExaminerProfile, examiner_id)
    form = ExaminerProfileForm(obj=profile)
    course_choices(form.courses)

    if request.method == 'GET':
        form.courses.data = [c.id for c in profile.courses]

    if form.validate_on_submit():
        profile.department = form.department.data.strip()
        profile.designation = form.designation.data.strip()
        profile.courses = Course.query.filter(Course.id.in_(form.courses.data or [])).all()
        if save('Examiner updated.'):
            return redirect(url_for('admin.view_all_examiners'))

    return render_template('admin/form.html', form=form,
                           title=f'Edit {profile.user.first_name} {profile.user.last_name}',
                           cancel_url=url_for('admin.view_all_examiners'))


@blueprint.route('/students')
def view_all_students():
    q = request.args.get('q', '').strip()
    page_number = request.args.get('page', 1, type=int)

    query = StudentProfile.query.join(User)
    if q:
        query = query.filter(search_filter(q, [User.first_name, User.last_name, FULL_NAME,
                                               User.email, StudentProfile.roll_number]))
    page = query.order_by(User.first_name, User.last_name).paginate(
        page=page_number, per_page=PER_PAGE, error_out=False)
    return render_template('admin/students.html', page=page, q=q)


@blueprint.route('/users/pending')
def pending_users():
    status = request.args.get('status', 'pending')
    if status not in ('pending', 'rejected'):
        status = 'pending'

    users = User.query.filter_by(status=status).order_by(User.id).all()
    return render_template('admin/pending_users.html', users=users, status=status)

@blueprint.route('/users/<int:user_id>/approve', methods=['GET', 'POST'])
def approve_user(user_id):
    """Approving creates the examiner or student profile the rest of the app needs."""
    user = db.get_or_404(User, user_id)
    role = user.roles[0].name if user.roles else None
    title = f'Approve {user.first_name} {user.last_name} as {role}'
    back = url_for('admin.pending_users')

    if role == 'examiner':
        profile = user.examiner_profile
        form = ExaminerProfileForm(obj=profile)
        course_choices(form.courses)

        if request.method == 'GET' and profile:
            form.courses.data = [c.id for c in profile.courses]

        if form.validate_on_submit():
            profile = profile or ExaminerProfile(user=user)
            profile.department = form.department.data.strip()
            profile.designation = form.designation.data.strip()
            profile.courses = Course.query.filter(Course.id.in_(form.courses.data or [])).all()

            user.status = 'approved'
            user.active = True
            db.session.add(profile)
            if save(f'{user.email} approved.', 'Could not approve this user.'):
                return redirect(back)

        return render_template('admin/form.html', form=form, title=title, cancel_url=back)

    if role == 'student':
        profile = user.student_profile
        form = StudentProfileForm(obj=profile)

        if form.validate_on_submit():
            roll_number = form.roll_number.data.strip()
            profile_id = profile.id if profile else 0
            taken = StudentProfile.query.filter(
                StudentProfile.roll_number == roll_number,
                StudentProfile.id != profile_id).first()

            if taken:
                add_error(form.roll_number, 'This roll number is already in use.')
            else:
                profile = profile or StudentProfile(user=user)
                profile.roll_number = roll_number
                profile.department = form.department.data.strip()
                profile.program = form.program.data.strip()
                profile.semester = form.semester.data.strip()
                profile.year_of_study = form.year_of_study.data

                user.status = 'approved'
                user.active = True
                db.session.add(profile)
                if save(f'{user.email} approved.', 'Could not approve this user.'):
                    return redirect(back)

        return render_template('admin/form.html', form=form, title=title, cancel_url=back)

    abort(400)


@blueprint.route('/users/<int:user_id>/<action>', methods=['POST'])
def user_action(user_id, action):
    if action not in ('reject', 'deactivate', 'activate'):
        abort(404)

    user = db.get_or_404(User, user_id)
    role = user.roles[0].name if user.roles else None

    # Admins and yourself cannot be changed here.
    if role == 'admin' or user.id == current_user.id:
        abort(403)

    if action == 'reject':
        user.status = 'rejected'
        message = f'{user.email} rejected.'
    elif action == 'activate':
        user.active = True
        message = f'{user.email} activated.'
    else:
        user.active = False
        message = f'{user.email} deactivated.'
        if user.examiner_profile:
            pending = ExaminationSlot.query.filter_by(
                examiner_id=user.examiner_profile.id, status='Scheduled').count()
            if pending:
                flash(f'This examiner still has {pending} scheduled slot(s). '
                      'Assign another examiner to them.', 'warning')

    save(message)

    if action != 'reject' and role == 'examiner':
        return redirect(url_for('admin.view_all_examiners'))
    if action != 'reject' and role == 'student':
        return redirect(url_for('admin.view_all_students'))
    return redirect(url_for('admin.pending_users'))

@blueprint.route('/slots')
def view_all_slots():
    exam_id = request.args.get('exam_id', type=int)
    page_number = request.args.get('page', 1, type=int)
    exam = db.session.get(Examination, exam_id) if exam_id else None

    query = ExaminationSlot.query
    if exam_id:
        query = query.filter(ExaminationSlot.exam_id == exam_id)
    page = query.order_by(ExaminationSlot.slot_date, ExaminationSlot.start_time).paginate(
        page=page_number, per_page=PER_PAGE, error_out=False)
    return render_template('admin/slots.html', page=page, exam=exam)


@blueprint.route('/slots/<int:slot_id>')
def slot_detail(slot_id):
    slot = db.get_or_404(ExaminationSlot, slot_id)
    return render_template('admin/slot_detail.html', slot=slot)

@blueprint.route('/slots/<int:slot_id>/change-examiner', methods=['GET', 'POST'])
def change_slot_examiner(slot_id):
    slot = db.get_or_404(ExaminationSlot, slot_id)
    back = url_for('admin.slot_detail', slot_id=slot.slot_id)

    if slot.status != 'Scheduled':
        flash('Only scheduled slots can change examiner.', 'danger')
        return redirect(back)

    # Active, approved examiners other than the current one
    candidates = (ExaminerProfile.query.join(User)
                  .filter(User.active.is_(True), User.status == 'approved',
                          ExaminerProfile.id != slot.examiner_id)
                  .order_by(User.first_name, User.last_name).all())
    if not candidates:
        flash('There is no other active, approved examiner to assign.', 'danger')
        return redirect(back)

    form = ChangeExaminerForm()
    form.new_examiner_id.choices = [
        (e.id, f'{e.user.first_name} {e.user.last_name} ({e.department})') for e in candidates]

    if form.validate_on_submit():
        new_id = form.new_examiner_id.data

        # keep a record of the change
        db.session.add(SlotExaminerChanges(
            slot_id=slot.slot_id,
            old_examiner_id=slot.examiner_id,
            new_examiner_id=new_id,
            change_reason=form.reason.data.strip(),
        ))
        slot.examiner_id = new_id

        # evaluations that are still waiting follow the new examiner
        for booking in slot.bookings:
            for evaluation in booking.evaluations:
                if evaluation.status == 'Pending':
                    evaluation.examiner_id = new_id

        if save('Examiner changed.'):
            return redirect(back)

    return render_template('admin/form.html', form=form,
                           title=f'Change examiner for slot {slot.slot_id}', cancel_url=back)


@blueprint.route('/bookings')
def view_all_bookings():
    q = request.args.get('q', '').strip()
    exam_id = request.args.get('exam_id', type=int)
    status = request.args.get('status', '').strip() or None
    page_number = request.args.get('page', 1, type=int)

    query = (Booking.query
             .join(StudentProfile, Booking.student_id == StudentProfile.id)
             .join(User, StudentProfile.user_id == User.id)
             .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.slot_id)
             .join(Examination, ExaminationSlot.exam_id == Examination.id))

    if q:
        query = query.filter(search_filter(q, [User.first_name, User.last_name, FULL_NAME,
                                               StudentProfile.roll_number, Examination.exam_name]))
    if exam_id:
        query = query.filter(Examination.id == exam_id)
    if status:
        query = query.filter(Booking.status == status)

    page = query.order_by(Booking.booking_id.desc()).paginate(
        page=page_number, per_page=PER_PAGE, error_out=False)
    return render_template('admin/bookings.html', page=page, q=q, exam_id=exam_id, status=status)


@blueprint.route('/bookings/<int:booking_id>')
def booking_detail(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    return render_template('admin/booking_detail.html', booking=booking)


@blueprint.route('/bookings/<int:booking_id>/reschedule', methods=['GET', 'POST'])
def reschedule_booking(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    back = url_for('admin.booking_detail', booking_id=booking.booking_id)

    if booking.status != 'Booked':
        flash('Only active bookings can be rescheduled.', 'danger')
        return redirect(back)

    # Other scheduled slots of the same exam that still have free seats
    slots = (ExaminationSlot.query
             .filter(ExaminationSlot.exam_id == booking.slot.exam_id,
                     ExaminationSlot.slot_id != booking.slot_id,
                     ExaminationSlot.status == 'Scheduled',
                     ExaminationSlot.available_seats > 0)
             .order_by(ExaminationSlot.slot_date, ExaminationSlot.start_time).all())
    if not slots:
        flash('No other slot with free seats exists for this examination.', 'danger')
        return redirect(back)

    form = RescheduleForm()
    form.new_slot_id.choices = [
        (s.slot_id,
         f'Slot {s.slot_id}: {s.slot_date:%d %b %Y} {s.start_time:%H:%M}-{s.end_time:%H:%M}, '
         f'{s.examiner.user.first_name} {s.examiner.user.last_name}, {s.available_seats} seats left')
        for s in slots]

    if form.validate_on_submit():
        new_slot = db.session.get(ExaminationSlot, form.new_slot_id.data)
        already_booked = Booking.query.filter_by(
            student_id=booking.student_id, slot_id=new_slot.slot_id).first()

        if new_slot.available_seats < 1:
            add_error(form.new_slot_id, 'That slot just filled up. Pick another.')
        elif already_booked:
            add_error(form.new_slot_id, 'This student already has a booking record for that slot.')
        else:
            old_slot = booking.slot

            # keep a record of the move
            db.session.add(BookingReschedules(
                booking_id=booking.booking_id,
                old_slot_id=old_slot.slot_id,
                new_slot_id=new_slot.slot_id,
                reschedule_reason=form.reason.data.strip(),
            ))

            # update seats and the booking itself
            old_slot.available_seats += 1
            new_slot.available_seats -= 1
            booking.slot_id = new_slot.slot_id

            # evaluations that are still waiting follow the new examiner
            for evaluation in booking.evaluations:
                if evaluation.status == 'Pending':
                    evaluation.examiner_id = new_slot.examiner_id

            if save('Booking rescheduled.'):
                return redirect(back)

    return render_template('admin/form.html', form=form,
                           title=f'Reschedule booking {booking.booking_id}', cancel_url=back)