from flask import render_template 

@blueprint.route('/dashboard')
def dashboard():
    
    return render_template('examiner/dashboard.html')