from flask import Flask, render_template, session, redirect, url_for, request, jsonify, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import redis
import json
from datetime import datetime, timedelta
from functools import wraps

# Import our modules
from config import config
from auth import auth_bp, User, login_required
from billing import billing_bp

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

# Configuration shortcuts
CHAINLIT_SERVICE_URL = app.config['CHAINLIT_SERVICE_URL']
DATABASE_URL = app.config['DATABASE_URL']
REDIS_URL = app.config['REDIS_URL']

# Initialize Redis (optional, for session sharing)
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
    print("Redis connected successfully")
except:
    redis_client = None
    print("Redis not available, using local sessions only")

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tier TEXT DEFAULT 'free',
            credits INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# login_required decorator and User model are now imported from auth module

@app.route('/')
def index():
    """Main landing page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Pass user context to Chainlit via URL parameters
    chainlit_url = f"{CHAINLIT_SERVICE_URL}?user_id={user.id}&tier={user.tier}&credits={user.credits}"
    
    return render_template('chat.html', 
                         chainlit_url=chainlit_url,
                         user=user.to_dict())

# Login/logout routes are now handled by auth blueprint

@app.route('/billing')
@login_required
def billing():
    """Billing and subscription management"""
    user = User.get_by_id(session['user_id'])
    return render_template('billing.html', user=user.to_dict() if user else None)

@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    user = User.get_by_id(session['user_id'])
    return render_template('settings.html', user=user.to_dict() if user else None)

@app.route('/api/user/credits')
@login_required
def get_user_credits():
    """API endpoint to get user credits"""
    user = User.get_by_id(session['user_id'])
    return jsonify({'credits': user.credits if user else 0})

@app.route('/api/user/update-credits', methods=['POST'])
@login_required
def update_user_credits():
    """API endpoint to update user credits (called by Chainlit service)"""
    data = request.get_json()
    credits_used = data.get('credits_used', 1)
    
    user = User.get_by_id(session['user_id'])
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    if user.update_credits(credits_used):
        return jsonify({'success': True, 'credits': user.credits})
    else:
        return jsonify({'success': False, 'error': 'Insufficient credits'}), 400

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'flask-app'})

if __name__ == '__main__':
    init_db()
    
    # Create a demo user for testing
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', ('demo',))
        if not cursor.fetchone():
            demo_password = generate_password_hash('demo123')
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, tier, credits) VALUES (?, ?, ?, ?, ?)',
                ('demo', 'demo@example.com', demo_password, 'premium', 500)
            )
            conn.commit()
            print("Demo user created: username=demo, password=demo123")
        conn.close()
    except Exception as e:
        print(f"Error creating demo user: {e}")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True) 