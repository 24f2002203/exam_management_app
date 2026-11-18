import pytest 
import os, sys 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import app
from core.models import User, Role 
from flask_security.utils import hash_password
from core.database import db 

@pytest.fixture 
def client(): 

    with app.test_client() as client:
        yield client

def test_register_student(client):
    with app.app_context():
        student = User.query.filter(User.roles.any(name='student')).first()
        first, last = student.first_name, student.last_name

    first_name_test = f"{first}_test"
    last_name_test = f"{last}_test"
    email_test = f"{first_name_test}.{last_name_test}@gmail.com"
    password_test = f"{first_name_test}{last_name_test}123"

    print(first_name_test)

    response = client.post('/auth/register', data={
        'first_name': first_name_test,
        'last_name': last_name_test,
        'email': email_test,
        'password': password_test,
        'confirm_password': password_test,
        'role': 'student',
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email=email_test).first()
        assert user is not None
        assert any(r.name == 'student' for r in user.roles)
        
    