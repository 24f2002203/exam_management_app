from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app as app 
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from core.models import User, Course, Examination, ExaminerProfile, StudentProfile, ExaminationSlot, ExaminationRubrics, Booking, BookingReschedules
from core.database import db 
from .forms import CourseForm, add_error

SEARCH_LIMIT = 20
PER_PAGE = 25


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


def fill_course(course, form):
    course.course_code = form.course_code.data.strip().upper()
    course.course_name = form.course_name.data.strip()
    course.description = (form.description.data or '').strip() or None
    course.program = form.program.data.strip()
    course.department = form.department.data.strip()
    course.credits = form.credits.data
    course.semester = form.semester.data.strip()
    course.year_of_study = form.year_of_study.data

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