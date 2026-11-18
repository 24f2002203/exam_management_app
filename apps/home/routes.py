from flask import current_app as app, Blueprint, render_template, request, redirect, url_for, flash


blueprint = Blueprint('home', __name__)

@blueprint.route('/')
def index():
    return redirect(url_for('auth.login'))