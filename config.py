"""
Configuration management for Studyzee application.

Loads environment variables and provides configuration for different environments.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"

    # Supabase configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # File upload configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    UPLOAD_FOLDER = "static/uploads"
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

    # Session configuration
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days in seconds

    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that all required environment variables are set.

        Returns:
            List of missing environment variables. Empty list if all valid.
        """
        required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
        missing = [var for var in required_vars if not getattr(cls, var)]
        return missing


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    SUPABASE_URL = "http://localhost:54321"
    SUPABASE_KEY = "test-key"


# Select configuration based on environment
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

CURRENT_CONFIG = config.get(Config.FLASK_ENV, DevelopmentConfig)
