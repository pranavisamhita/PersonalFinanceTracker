from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # App configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myuser:8090@localhost/finance_tracker'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'tanujach8090'

    # Initialize extensions with the app
    db.init_app(app)
    bcrypt.init_app(app)    
    login_manager.init_app(app)
    login_manager.login_view = 'home'  # 👈 'home' is the login route

    # User loader for Flask-Login
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register the routes
    from .routes import init_routes
    init_routes(app)

    # Create database tables (if not already created)
    with app.app_context():
        db.create_all()  # Ensure tables are created when the app runs

    return app
