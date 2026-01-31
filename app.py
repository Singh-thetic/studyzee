"""
Studyzee - Study Management and Collaboration Platform

A comprehensive web application for students to manage courses, track assignments,
generate study materials, and connect with peers.
"""

import logging
from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import CURRENT_CONFIG, Config
from utils.db import DatabaseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config_class=CURRENT_CONFIG) -> tuple:
    """
    Application factory function.

    Args:
        config_class: Configuration class to use.

    Returns:
        Tuple of (app, login_manager, socketio).

    Raises:
        ValueError: If required environment variables are missing.
    """
    # Validate configuration
    missing_vars = config_class.validate()
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    bcrypt = Bcrypt(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.home"
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Initialize database client
    db = DatabaseClient(app.config["SUPABASE_URL"], app.config["SUPABASE_KEY"])
    app.db = db
    app.bcrypt = bcrypt

    # Create upload folders
    import os
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs("static/profile_pics", exist_ok=True)

    # Register routes
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.courses import courses_bp
    from routes.study_groups import study_groups_bp
    from routes.chat import chat_bp, register_socket_events
    from routes.social import social_bp
    from routes.flashcards import flashcards_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(study_groups_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(flashcards_bp)
    
    # Register WebSocket event handlers
    register_socket_events(socketio)

    # User loader for Flask-Login
    from models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        user_data = db.select_one("users", "id", user_id)
        if user_data:
            return User.from_dict(user_data)
        return None

    logger.info(f"Application initialized with {config_class.__name__}")

    return app, login_manager, socketio


# Create app instance
try:
    app, login_manager, socketio = create_app()
except ValueError as e:
    logger.error(f"Failed to create app: {str(e)}")
    raise

if __name__ == "__main__":
    socketio.run(app, debug=Config.DEBUG, host="0.0.0.0", port=5001)
