from flask import render_template, Blueprint
blueprint = Blueprint('examiner', __name__, url_prefix='/examiner')

@blueprint.route('/dashboard')
def dashboard():
    
    return render_template('examiner/dashboard.html')