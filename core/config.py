import os, random, string, secrets, sys
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))

db_path = os.path.join(basedir, './db_directory/database.sqlite3')
db_path = os.path.abspath(db_path)


test_db_path = os.path.join(basedir, './db_directory/test_database.sqlite3')
test_db_path = os.path.abspath(test_db_path)


SQLITE_DB_DIR = db_path
TEST_SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLITE_DB_DIR

class BaseConfig(): 
    DEBUG=False 
    SQLITE_DB_DIR = None 
    SQLALCHEMY_DATABASE_URI = None 

    SECRET_KEY = os.environ.get('SECRET_KEY')

    SECURITY_PASSWORD_HASH = "argon2"
    SECURITY_PASSWORD_SALT = (
        os.environ.get('SECURITY_PASSWORD_SALT')
        or secrets.token_hex(32)
    )

class LocalDevelopmentConfig(BaseConfig): 
    DEBUG = True 
    SQLITE_DB_DIR = db_path
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLITE_DB_DIR

class TestingConfig(BaseConfig): 
    DEBUG=True 
    SQLITE_DB_DIR = test_db_path
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLITE_DB_DIR
    WTF_CSRF_ENABLED = False