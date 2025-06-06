import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    CHAINLIT_SERVICE_URL = os.environ.get('CHAINLIT_SERVICE_URL', 'http://localhost:8000')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    
    # Flask settings
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Security settings
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS settings
    CORS_ORIGINS = ['*'] if FLASK_ENV == 'development' else [CHAINLIT_SERVICE_URL]

class ProductionConfig(Config):
    """Production configuration for Cloud Run"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # For Cloud Run, we'll use SQLite stored in /tmp or a mounted volume
    # You can upgrade to Cloud SQL later if needed

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 