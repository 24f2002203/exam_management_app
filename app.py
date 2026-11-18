import os, logging 
from flask import Flask 
from flask_cors import CORS 
from flask_security import SQLAlchemySessionUserDatastore, Security
from flask_login import LoginManager
from core.config import LocalDevelopmentConfig, TestingConfig
from core.database import db 
from flask_migrate import Migrate
from apps import register_blueprints
from flask.cli import with_appcontext
from core.seed import seed_database
from flask_wtf.csrf import CSRFProtect

logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

security = Security()

login_manager = LoginManager()

csrf = CSRFProtect()
 
  
def create_app(): 
    app = Flask(__name__, template_folder = 'templates')

    CORS(app)

    env = os.getenv("ENV", "development")

    if env=="production": 

        app.logger.info("No production environment setup!")
        raise Exception("No prodcution environment is setup!")

    elif env=='testing': 

        app.logger.info("Starting Testing environment")
        app.config.from_object(TestingConfig)

    else:

        app.logger.info("Starting Local development")
        app.config.from_object(LocalDevelopmentConfig)

    db.init_app(app)
    migrate = Migrate(app, db)
    

    csrf.init_app(app)

    from core.models import User, Role

    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    security.init_app(app, user_datastore)

    register_blueprints(app)

    @app.cli.command("seed")
    @with_appcontext
    def seed(): 
        
        seed_database(user_datastore)
        

    return app 

app = create_app()

if __name__ == "__main__": 
    
    app.run(debug=True, host='127.0.0.1', port=5000)

    