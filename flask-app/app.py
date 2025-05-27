"""
We-Relate Flask Application
===========================

A de-escalation coach platform for practicing intentional dialogue.
"""
from flask import Flask
from flask_cors import CORS
import os

# Import configuration and modules
from config import config
from database import init_db, create_demo_user
from routes import register_main_routes
from api_routes import register_api_routes

# Import blueprints
from auth import auth_bp
from billing import billing_bp

# Create Flask app
app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])
app.secret_key = app.config['SECRET_KEY']

# Initialize CORS
CORS(app, origins=app.config['CORS_ORIGINS'])

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(billing_bp, url_prefix='/billing')

# Register routes
register_main_routes(app)
register_api_routes(app)

# Print session info
print("Using local sessions only (no Redis) - optimized for Cloud Run")


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Create demo user for testing
    create_demo_user()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 