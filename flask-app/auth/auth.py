from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from .models import User
import redis
import json
import os
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# Initialize Redis (optional, for session sharing)
try:
    redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
    redis_client.ping()
except:
    redis_client = None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.get_by_username(username)
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            
            # Store session in Redis if available
            if redis_client:
                session_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'login_time': datetime.now().isoformat()
                }
                redis_client.setex(f"session:{user.id}", 3600, json.dumps(session_data))
            
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Basic validation
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        try:
            User.create(username, email, password)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    user_id = session.get('user_id')
    
    # Clear Redis session if available
    if redis_client and user_id:
        redis_client.delete(f"session:{user_id}")
    
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/validate-session', methods=['POST'])
def validate_session():
    """API endpoint to validate user session"""
    if 'user_id' not in session:
        return jsonify({'valid': False}), 401
    
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'valid': False}), 401
    
    return jsonify({
        'valid': True,
        'user': user.to_dict()
    })

@auth_bp.route('/api/user/profile')
def get_user_profile():
    """API endpoint to get user profile"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.get_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()) 