import pytest 
from app import app 
from core.models import Role, User 

default_roles = ['admin', 'student', 'examiner']



def test_preexisting_roles():

    with app.app_context():
        exisiting_roles = Role.query.all()
        for role in default_roles: 
            assert any(r.name == role for r in exisiting_roles), f"Role '{role}' does not exist in the database."