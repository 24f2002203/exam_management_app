from flask_wtf import FlaskForm
from wtforms import (
    DateField, DateTimeLocalField, EmailField, FloatField, IntegerField,
    PasswordField, SelectField, SelectMultipleField, StringField, SubmitField,
    TextAreaField, TimeField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

from wtforms.validators import DataRequired, Length, NumberRange, Optional

DT_FORMAT = '%Y-%m-%dT%H:%M'
EXAM_TYPES = [(t, t) for t in ( 'Viva', 'Practical', 'Project')]
EXAM_STATUSES = [(s, s) for s in ('Scheduled', 'Completed', 'Cancelled')]

TIMELINE_FIELDS = (
    'slot_creation_starts_at',
    'slot_creation_ends_at',
    'booking_starts_at',
    'booking_ends_at',
)

def add_error(field, message):
    field.errors = list(field.errors) + [message]

def timeline_field(label):
    """A required date-and-time field, used by the timeline."""
    return DateTimeLocalField(label, format=DT_FORMAT, validators=[DataRequired()])

def check_timeline(form):
    """Check that the four timeline dates are in a sensible order."""
    ok = True
    if form.slot_creation_ends_at.data <= form.slot_creation_starts_at.data:
        add_error(form.slot_creation_ends_at, 'Slot creation must close after it opens.')
        ok = False
    if form.booking_starts_at.data < form.slot_creation_ends_at.data:
        add_error(form.booking_starts_at, 'Booking cannot open before slot creation closes.')
        ok = False
    if form.booking_ends_at.data <= form.booking_starts_at.data:
        add_error(form.booking_ends_at, 'Booking must close after it opens.')
        ok = False
    return ok

class CourseForm(FlaskForm):
    course_code = StringField('Course code', validators=[DataRequired(), Length(min=2, max=20)])
    course_name = StringField('Course name', validators=[DataRequired(), Length(min=2, max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    program = StringField('Program', validators=[DataRequired(), Length(min=2, max=255)])
    department = StringField('Department', validators=[DataRequired(), Length(min=2, max=255)])
    credits = IntegerField('Credits', validators=[DataRequired(), NumberRange(min=1, max=30)])
    semester = StringField('Semester', validators=[DataRequired(), Length(max=20)])
    year_of_study = IntegerField('Year of study', validators=[DataRequired(), NumberRange(min=1, max=8)])
    submit = SubmitField('Save course')

class ExaminationForm(FlaskForm):
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    exam_name = StringField('Examination name', validators=[DataRequired(), Length(max=255)])
    exam_type = SelectField('Type', choices=EXAM_TYPES)
    max_marks = IntegerField('Maximum marks', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    exam_date = DateField('Examination date', validators=[DataRequired()])
    start_time = TimeField('Start time', validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[DataRequired(), NumberRange(min=1)])
    venue = StringField('Venue', validators=[DataRequired(), Length(max=255)])
    max_students = IntegerField('Maximum students', validators=[DataRequired(), NumberRange(min=1)])
    status = SelectField('Status', choices=EXAM_STATUSES)
    slot_creation_starts_at = timeline_field('Examiner slot creation opens')
    slot_creation_ends_at = timeline_field('Examiner slot creation closes')
    booking_starts_at = timeline_field('Student booking opens')
    booking_ends_at = timeline_field('Student booking closes')
    submit = SubmitField('Save examination')

    def validate(self, extra_validators=None):
        return super().validate(extra_validators) and check_timeline(self)


class RubricForm(FlaskForm):
    criteria = StringField('Criteria', validators=[DataRequired(), Length(max=500)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    weightage = FloatField('Weightage (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    max_marks = IntegerField('Maximum marks', validators=[DataRequired(), NumberRange(min=1)])
    display_order = IntegerField('Display order', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save rubric')

class TimelineForm(FlaskForm):
    slot_creation_starts_at = timeline_field('Examiner slot creation opens')
    slot_creation_ends_at = timeline_field('Examiner slot creation closes')
    booking_starts_at = timeline_field('Student booking opens')
    booking_ends_at = timeline_field('Student booking closes')
    submit = SubmitField('Save timeline')

    def validate(self, extra_validators=None):
        return super().validate(extra_validators) and check_timeline(self)


class ExaminerCreateForm(FlaskForm):
    first_name = StringField('First name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last name', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Temporary password', validators=[DataRequired(), Length(min=8)])
    department = StringField('Department', validators=[DataRequired(), Length(max=255)])
    designation = StringField('Designation', validators=[DataRequired(), Length(max=255)])
    courses = SelectMultipleField('Assigned courses', coerce=int, validators=[Optional()])
    submit = SubmitField('Add examiner')

    
class ExaminerProfileForm(FlaskForm):
    department = StringField('Department', validators=[DataRequired(), Length(max=255)])
    designation = StringField('Designation', validators=[DataRequired(), Length(max=255)])
    courses = SelectMultipleField('Assigned courses', coerce=int, validators=[Optional()])
    submit = SubmitField('Save examiner')

class StudentProfileForm(FlaskForm):
    roll_number = StringField('Roll number', validators=[DataRequired(), Length(max=20)])
    department = StringField('Department', validators=[DataRequired(), Length(max=255)])
    program = StringField('Program', validators=[DataRequired(), Length(max=255)])
    semester = StringField('Semester', validators=[DataRequired(), Length(max=20)])
    year_of_study = IntegerField('Year of study', validators=[DataRequired(), NumberRange(min=1, max=8)])
    submit = SubmitField('Save student')