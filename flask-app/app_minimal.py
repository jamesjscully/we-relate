"""
Minimal We-Relate Flask Application for Debugging
================================================

Testing Flask app without Phoenix proxy to isolate hanging issue.
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
from datetime import datetime

# Import configuration and modules
from config import config
from database import init_db, create_demo_user, create_admin_user
from routes import register_main_routes
from api_routes import register_api_routes

# Import blueprints
from auth import auth_bp
from billing import billing_bp
# Skip phoenix_proxy import for testing

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
# Skip phoenix_bp for testing

# Register routes
register_main_routes(app)
register_api_routes(app)

# Simple health check
@app.route('/test')
def test():
    return jsonify({'status': 'minimal app working', 'timestamp': datetime.now().isoformat()})

# Print session info
print("Using local sessions only (no Redis) - optimized for Cloud Run")


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Create demo user for testing
    create_demo_user()
    
    # Create admin user for troubleshooting
    create_admin_user()
    
    # Run the app
    port = int(os.environ.get('PORT', 5001))  # Use different port
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 