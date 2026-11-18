from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app as app 
from flask_security.forms import LoginForm
from flask_login import login_user
from flask_security.utils import verify_password, hash_password
from core.models import User, Role
from core.database import db
from .registration_form import RegisterForm

blueprint = Blueprint(
    'auth', 
    __name__, 
    url_prefix='/auth',
    template_folder='templates/auth',
)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST': 

        if form.email.data and form.password.data: 
            
            email = form.email.data
            password = form.password.data 

            user = User.query.filter(User.email == email).first()

            if not user: 
                message = "User with this email does not exist. Please register first."
                return render_template('auth/error.html', message = message)

            role = user.roles[0].name 
            
            if verify_password(password, user.password):

                login_user(user)

                if role == 'admin': 
                    return redirect(url_for('admin.dashboard'))
                elif role == 'student' and user.status == 'approved':
                    return redirect(url_for('student.dashboard', student_id = user.id))
                elif role == 'staff' and user.status == 'pending':
                    message = "Your account is not yet approved by the admin."
                    return render_template('error.html', message = message)
                elif role == 'examiner' and user.status == 'approved':
                    return redirect(url_for('examiner.dashboard', examiner_id = user.id))
                else:
                    message = "Invalid role. Please contact the administrator."
                    return render_template('auth/error.html', message = message)
            else:
                message = "Incorrect email or password."
                return render_template('auth/error.html', message = message)
            
        else:
            message = "Please enter both email and password."
            return render_template('auth/error.html', message = message)
            
    else:
        return render_template('auth/login.html', form = form)

@blueprint.route('/register', methods = ['GET', 'POST'])
def register(): 

    form = RegisterForm()

    if form.validate_on_submit():

        role = str(form.role.data).lower() 

        user = User.query.filter_by(email=form.email.data).first()
        if not user: 

            if form.password.data == form.password_confirm.data: 

                user = User(
                    first_name = str(form.first_name.data).title(), 
                    last_name = str(form.last_name.data).title(),
                    email = form.email.data.strip().lower(), 
                    password = hash_password(form.password.data),
                    roles = [role]
                )
                try:
                    db.session.add(user)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    raise
                
                return redirect(url_for('auth.login'))
                
            else: 
                message = "Passwords do not match" 
                return render_template('auth/error.html', message = message)
            
        else: 
            message = "User with this email already exists" 
            return render_template('auth/error.html', message = message)
        
    return render_template('auth/registration.html', form = form)