import os 

from flask_security.utils import hash_password
from core.models import User, Role 
from core.database import db

def create_admin(user_datastore): 
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_email or not admin_password:
        raise ValueError(
            "Set ADMIN_EMAIL and ADMIN_PASSWORD before seeding."
        )

    admin_email = admin_email.strip().lower()
    admin = user_datastore.find_user(email=admin_email)

    if not admin:
        admin = user_datastore.create_user(
            first_name="admin",
            last_name="user", 
            email=admin_email,
            password=hash_password(admin_password),
            active=True, 
            roles=['admin']
        )
    else: 
        admin.password = hash_password(admin_password)
        admin.active=True

    # Assign admin role if not already assigned
    if not user_datastore.find_role("admin") in admin.roles:
        user_datastore.add_role_to_user(admin, "admin")

    # Save changes
    
    db.session.commit()

def create_first_student(user_datastore): 

    first_student_email = os.getenv("FIRST_STUDENT_EMAIL")
    first_student_password = os.getenv("FIRST_STUDENT_PASSWORD")
    
    if not first_student_email or not first_student_password:
        raise ValueError(
            "Set FIRST_STUDENT_EMAIL and FIRST_STUDENT_PASSWORD before seeding."
        )

    first_student = user_datastore.find_user(email=first_student_email)

    if not first_student:
        first_student = user_datastore.create_user(
            first_name="student1",
            last_name="user", 
            email=first_student_email,
            password=hash_password(first_student_password),
            active=True, 
            roles=['student']
        )

    if not user_datastore.find_role("student") in first_student.roles:
        user_datastore.add_role_to_user(first_student, "student")

    db.session.commit()

def create_first_examiner(user_datastore): 

    first_examiner_email = os.getenv("FIRST_EXAMINER_EMAIL")
    first_examiner_password = os.getenv("FIRST_EXAMINER_PASSWORD")
    
    if not first_examiner_email or not first_examiner_password:
        raise ValueError(
            "Set FIRST_EXAMINER_EMAIL and FIRST_EXAMINER_PASSWORD before seeding."
        )

    first_examiner = user_datastore.find_user(email=first_examiner_email)

    if not first_examiner:
        first_examiner = user_datastore.create_user(
            first_name="examiner1",
            last_name="user", 
            email=first_examiner_email,
            password=hash_password(first_examiner_password),
            active=True, 
            roles=['examiner']
        )

    if not user_datastore.find_role("examiner") in first_examiner.roles:
        user_datastore.add_role_to_user(first_examiner, "examiner")

    db.session.commit()

def create_first_student_profile(user_datastore): 

    ...

def seed_database(user_datastore): 

    #default roles 
    default_roles = [
        {
            'name':'admin', 
            'description':'Administrator role with full access'
        }, 
        {
            'name':'student', 
            'description':'Student role with access to student functionalities'
        }, 
        {
            'name':'examiner', 
            'description':'Examiner role with access to examiner functionalities'
        }

    ]

    for role_data in default_roles:
        if not user_datastore.find_role(role_data["name"]):
            user_datastore.create_role(**role_data)

    create_admin(user_datastore)
    print("created admin")

    create_first_student(user_datastore)
    print("created first student")

    create_first_examiner(user_datastore)
    print("created first examiner")

    print("Database seeded successfully!")