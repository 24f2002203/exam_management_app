from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app as app 
from flask_security.forms import LoginForm
from flask_security import login_user, logout_user
from flask_security.utils import verify_password, hash_password
from core.models import User, Role, StudentProfile, ExaminerProfile
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
        if not form.validate_on_submit():
            print("Form errors:", form.errors)   
            return render_template('auth/login.html', form=form,
                                   message="Incorrect email or password.")

        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        
        if not user or not verify_password(form.password.data, user.password):
            return render_template('auth/login.html', form=form,
                                   message="Incorrect email or password.")

        if not user.roles:
            return render_template('auth/login.html', form=form,
                                   message="No role assigned. Contact the administrator.")

        role = user.roles[0].name

        if role != 'admin' and user.status != 'approved':
            messages = {
                'pending': "Your account is awaiting admin approval.",
                'rejected': "Your account has been rejected. Contact the administrator.",
            }
            return render_template('auth/login.html', form=form,
                                   message=messages.get(user.status, "Your account is inactive. Contact the administrator."))

        if role=='student':
            student = StudentProfile.query.filter_by(user_id = user.id).first()
        elif role=='examiner': 
            examiner = ExaminerProfile.query.filter_by(user_id = user.id).first()

        role_redirects = {
            'admin': lambda: url_for('admin.dashboard'),
            'student': lambda: url_for('student.dashboard'),
            'examiner': lambda: url_for('examiner.dashboard'),
        }
        if role not in role_redirects:
            return render_template('auth/login.html', form=form,
                                   message="Invalid role. Contact the administrator.")

        login_user(user)                      # only after every check passes
        return redirect(role_redirects[role]())

    return render_template('auth/login.html', form=form, message='')


@blueprint.route('/register', methods=['GET', 'POST'])
def register():

    form = RegisterForm()

    if form.validate_on_submit():

        # Normalize email
        email = form.email.data.strip().lower()

        # Check for existing user
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return render_template(
                'auth/registration.html',
                form=form,
                message="User with this email already exists."
            )

        # Assign permitted role server-side
        role = Role.query.filter_by(name='student').first()

        if not role:
            return render_template(
                'auth/registration.html',
                form=form,
                message="Student role is not configured."
            )

        # Create user
        user = User(
            first_name=form.first_name.data.strip().title(),
            last_name=form.last_name.data.strip().title(),
            email=email,
            password=hash_password(form.password.data),
            roles=[role],
            status='pending'
        )

        try:
            db.session.add(user)
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        flash("Registration successful! Await admin approval.", "success")

        return redirect(url_for('auth.login'))

    return render_template(
        'auth/registration.html',
        form=form,
        message=''
    )
