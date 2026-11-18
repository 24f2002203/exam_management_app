import os, sys, pytest 


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import app 
from core.models import User, Role
from dotenv import load_dotenv
from flask_security.utils import verify_password

load_dotenv()

@pytest.fixture 
def client(): 

    client = app.test_client()

    yield client 

def test_admin_credentials(): 

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    assert admin_email is not None 
    assert admin_password is not None

    with app.app_context():

        admin = User.query.filter_by(
            email=admin_email.strip().lower()
        ).first()

        assert verify_password(admin_password, admin.password)

def test_admin_dashboard_access(client): 

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    response = client.post('/auth/login', 
                           data = {
                               'email':admin_email.strip().lower(), 
                               'password':admin_password
                           }, 
                           follow_redirects=False)

    print("Login status:", response.status_code)
    print("Redirect location:", response.headers.get('Location'))

    # Check authentication
    with client.session_transaction() as session:
        print("Session:", dict(session))
        assert '_user_id' in session, "Admin login failed!"

    # Access dashboard
    response = client.get(response.headers['Location'])

    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data
    assert b"Courses" in response.data 
    assert b"Examinations" in response.data
    assert b"Students" in response.data 
    assert b"Bookings" in response.data
    assert b"Slots" in response.data 
    assert b"Pending users" in response.data
    assert b"Search" in response.data
    assert b"Examinations with an open phase" in response.data

def test_unauthenticated_admin_access(client):

    response = client.get(
        '/admin/dashboard',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Login' in response.data

def test_admin_search(client): 

    response = client.get('/admin/search', query_string='Student1')

    assert response.code == 200 
    assert b"Search results for \"Student1\""