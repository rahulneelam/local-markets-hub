import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_dev")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # For proper URL generation

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Setup user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    # Import models here
    import models
    
    # Only create all if tables don't exist yet (otherwise use migrations)
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    if not inspector.has_table('users'):
        db.create_all()
        logging.info("Created database tables")
    else:
        logging.info("Database tables already exist")