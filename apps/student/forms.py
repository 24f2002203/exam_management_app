from flask_wtf import FlaskForm
from wtforms import (
    EmailField, IntegerField, PasswordField, StringField, SubmitField, TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class ActionForm(FlaskForm):
    """Empty form, only used for the CSRF token on POST buttons (e.g. Book)."""


class CancelForm(FlaskForm):
    reason = TextAreaField('Reason (optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Cancel booking')


class StudentRegisterForm(FlaskForm):
    first_name = StringField('First name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last name', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    roll_number = StringField('Roll number', validators=[DataRequired(), Length(max=20)])
    department = StringField('Department', validators=[DataRequired(), Length(max=255)])
    program = StringField('Program', validators=[DataRequired(), Length(max=255)])
    semester = StringField('Semester', validators=[DataRequired(), Length(max=20)])
    year_of_study = IntegerField('Year of study', validators=[DataRequired(), NumberRange(min=1, max=8)])
    submit = SubmitField('Register')