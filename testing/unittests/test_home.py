import os, sys, pytest 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import app 


@pytest.fixture
def client(): 

    with app.app_context(): 
        client = app.test_client()

        yield client


def test_home_rendering(client): 
    
    response = client.get('/', follow_redirects=True)
    assert b"Login" in response.data
    assert response.status_code == 200


