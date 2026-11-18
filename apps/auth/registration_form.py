from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, StringField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegisterForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password_confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    role = SelectField(
        'Register As', 
        choices = [
            ('student', 'Student'), 
            ('examiner', 'Examiner')
        ], 
        validators=[DataRequired()]
    )
    submit = SubmitField('Register')