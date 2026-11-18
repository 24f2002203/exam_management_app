from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,StringField, SubmitField,TextAreaField)

from wtforms.validators import DataRequired, Length, NumberRange, Optional

def add_error(field, message):
    field.errors = list(field.errors) + [message]

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