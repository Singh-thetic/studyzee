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
    Bcrypt(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.home"
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Create upload folders
    import os
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs("static/profile_pics", exist_ok=True)

    logger.info(f"Application initialized with {config_class.__name__}")

    return app, login_manager, socketio


# Create app instance
try:
    app, login_manager, socketio = create_app()
except ValueError as e:
    logger.error(f"Failed to create app: {str(e)}")
    raise

if __name__ == "__main__":
    socketio.run(app, debug=Config.DEBUG, host="0.0.0.0", port=5000)
