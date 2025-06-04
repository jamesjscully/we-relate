from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from .models import User
import os
from datetime import datetime
import jwt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['username']  # Form still uses 'username' field name for compatibility
        password = request.form['password']
        
        # Try to find user by email (which is now the username)
        user = User.get_by_email(email) or User.get_by_username(email)
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = f"{user.first_name} {user.last_name}"
            session['initials'] = f"{user.first_name[0].upper()}{user.last_name[0].upper()}"
            
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        email = request.form['username']  # Form still uses 'username' field name for compatibility
        password = request.form['password']
        
        # Try to find user by email (which is now the username)
        user = User.get_by_email(email) or User.get_by_username(email)
        
        if user and user.check_password(password):
            if user.is_admin:
                session['user_id'] = user.id
                session['username'] = user.username
                session['full_name'] = f"{user.first_name} {user.last_name}"
                session['initials'] = f"{user.first_name[0].upper()}{user.last_name[0].upper()}"
                session['is_admin'] = True
                
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Admin privileges required', 'error')
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('admin_login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
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

@auth_bp.route('/google-signin', methods=['POST'])
def google_signin():
    """Handle Google Sign-In"""
    try:
        # Get the credential from the request
        data = request.get_json()
        credential = data.get('credential')
        
        if not credential:
            return jsonify({'success': False, 'error': 'No credential provided'}), 400
        
        # Verify the Google ID token
        # Note: In production, you should verify the token with Google's servers
        # For now, we'll decode it without verification (NOT SECURE for production)
        try:
            # Decode the JWT token (without verification for demo purposes)
            # In production, use google.auth.transport.requests and google.oauth2.id_token
            decoded_token = jwt.decode(credential, options={"verify_signature": False})
            
            email = decoded_token.get('email')
            name = decoded_token.get('name')
            google_id = decoded_token.get('sub')
            
            if not email:
                return jsonify({'success': False, 'error': 'No email in token'}), 400
            
            # Check if user exists
            user = User.get_by_email(email)
            
            if not user:
                # Create new user with Google info
                # Use email as both username and email
                import secrets
                random_password = secrets.token_urlsafe(32)
                
                try:
                    user = User.create(email, email, random_password)
                    # You might want to add a field to mark this as a Google user
                except ValueError:
                    # Email already exists, this shouldn't happen since we checked above
                    return jsonify({'success': False, 'error': 'User creation failed'}), 500
            
            # Log the user in
            session['user_id'] = user.id
            session['username'] = user.username
            
            return jsonify({'success': True})
            
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 400
            
    except Exception as e:
        print(f"Google sign-in error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
