import os, sys 
from sqlalchemy import inspect 
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import app 
from core.database import db  

@pytest.fixture
def inspector(): 
    with app.app_context(): 
        inspector = inspect(db.engine)
        yield inspector 

def test_table_existence(inspector): 
    tables = inspector.get_table_names()

    assert "users" in tables 
    assert "roles" in tables 
    assert "student_profiles" in tables 
    assert "examiner_profiles" in tables 
    assert "courses" in tables
    assert "examinations" in tables
    assert "evaluations" in tables
    assert "examination_slots" in tables
    assert "bookings" in tables
    assert "slot_examiner_changes" in tables
    assert "booking_reschedules" in tables
    assert "examination_rubrics" in tables
    assert "evaluation_scores" in tables

def get_columns(inspector, table_name): 
    columns_list = inspector.get_columns(table_name)

    columns = [column['name'] for column in columns_list]

    return columns 

def test_user_table_columns(inspector): 

    columns = get_columns(inspector, 'users')

    assert 'id' in columns 
    assert 'first_name' in columns 
    assert 'last_name' in columns 
    assert 'email' in columns 
    assert 'password' in columns 
    assert "fs_uniquifier" in columns

def test_role_columns(inspector): 

    columns = get_columns(inspector, 'roles')

    assert 'id' in columns 
    assert 'name' in columns 
    assert 'description' in columns 

def test_student_profile_columns(inspector): 

    columns = get_columns(inspector, 'student_profiles')

    assert 'id' in columns 
    assert 'user_id' in columns 
    assert 'roll_number' in columns 
    assert 'department' in columns 
    assert 'program' in columns 
    assert 'semester' in columns 
    assert 'year_of_study' in columns 

def test_examiner_profile_columns(inspector):

    columns = get_columns(inspector, 'examiner_profiles')

    assert 'id' in columns 
    assert 'user_id' in columns 
    assert 'department' in columns 
    assert 'designation' in columns 

def test_courses_columns(inspector):

    columns = get_columns(inspector, 'courses')

    assert 'id' in columns 
    assert 'course_code' in columns 
    assert 'course_name' in columns 
    assert 'description' in columns 
    assert 'credits' in columns 
    assert 'department' in columns 
    assert 'semester' in columns 
    assert 'year_of_study' in columns 

def test_examination_columns(inspector):

    columns = get_columns(inspector, 'examinations')

    assert 'id' in columns 
    assert 'course_id' in columns 

    assert 'exam_name' in columns
    assert 'exam_type' in columns
    assert 'max_marks' in columns
    assert 'description' in columns

    assert 'exam_date' in columns 
    assert 'start_time' in columns 
    assert 'duration' in columns
    assert 'venue' in columns

    assert 'max_students' in columns
    assert 'slot_creation_starts_at' in columns
    assert 'slot_creation_ends_at' in columns
    assert 'booking_starts_at' in columns
    assert 'booking_ends_at' in columns

    assert 'slot_creation_open' in columns
    assert 'booking_open' in columns

    assert 'results_published' in columns
    assert 'status' in columns

def test_evaluation_columns(inspector): 

    columns = get_columns(inspector, 'evaluations')

    print(columns)

    assert 'id' in columns 
    assert 'booking_id' in columns
    assert 'examiner_id' in columns

    assert 'date_of_evaluation' in columns
    assert 'status' in columns
    assert 'marks_obtained' in columns
    assert "submitted at" in columns

def test_examination_slots_columns(inspector): 

    columns = get_columns(inspector, 'examination_slots')

    assert 'slot_id' in columns 
    assert 'exam_id' in columns 
    assert 'examiner_id' in columns 

    assert 'slot_date' in columns
    assert 'start_time' in columns
    assert 'end_time' in columns

    assert 'available_seats' in columns
    assert 'status' in columns

def test_booking_columns(inspector): 

    columns = get_columns(inspector, 'bookings')

    assert 'booking_id' in columns 
    assert 'slot_id' in columns 
    assert 'student_id' in columns 

    assert 'booked_at' in columns
    assert 'cancelled_at' in columns
    assert 'cancellation_reason' in columns

    assert 'status' in columns

def test_slot_examiner_changes(inspector): 

    columns = get_columns(inspector, 'slot_examiner_changes')

    assert 'change_id' in columns 
    assert 'slot_id' in columns 

    assert 'old_examiner_id' in columns 
    assert 'new_examiner_id' in columns

    assert 'change_reason' in columns
    assert "changed_at" in columns 

def test_booking_reschedules(inspector): 

    columns = get_columns(inspector, 'booking_reschedules')

    assert 'reschedule_id' in columns 
    assert 'booking_id' in columns 

    assert 'old_slot_id' in columns 
    assert 'new_slot_id' in columns

    assert 'reschedule_reason' in columns
    assert 'rescheduled_at' in columns

def test_examination_rubrics(inspector): 

    columns = get_columns(inspector, 'examination_rubrics')

    assert 'rubric_id' in columns 
    assert 'exam_id' in columns 

    assert 'criteria' in columns 
    assert "description" in columns
    assert 'weightage' in columns
    assert 'max_marks' in columns

    assert 'display_order' in columns


def test_evaluation_scores(inspector): 

    columns = get_columns(inspector, 'evaluation_scores')

    assert 'evaluation_id' in columns 
    assert 'rubric_id' in columns 

    assert 'score' in columns
    assert 'feedback' in columns