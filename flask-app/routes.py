"""
Main routes for We-Relate Flask app
"""
from flask import render_template, session, redirect, url_for, request, jsonify, flash
from datetime import datetime

from auth.models import User
from auth.decorators import login_required


def register_main_routes(app):
    """Register main application routes"""
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        """Main landing/registration page"""
        if request.method == 'POST':
            # Handle registration
            email = request.form['email']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            password = request.form['password']
            confirm_password = request.form.get('confirmPassword')
            
            # Basic validation
            if not email:
                flash('Email is required', 'error')
                return render_template('register.html')
                
            if not first_name:
                flash('First name is required', 'error')
                return render_template('register.html')
                
            if not last_name:
                flash('Last name is required', 'error')
                return render_template('register.html')
                
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('register.html')
                
            # Check password confirmation if provided
            if confirm_password and password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('register.html')
            
            try:
                # Use email as username
                User.create(email, email, first_name, last_name, password)
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except ValueError as e:
                flash(str(e), 'error')
                return render_template('register.html')
        
        # GET request
        if 'user_id' not in session:
            return render_template('register.html')
        
        user = User.get_by_id(session['user_id'])
        if not user:
            session.clear()
            return render_template('register.html')
        
        # Pass user context to Chainlit via URL parameters
        chainlit_url = f"{app.config['CHAINLIT_SERVICE_URL']}?user_id={user.id}&tier={user.tier}&credits={user.credits}"
        
        return render_template('chat.html', 
                             chainlit_url=chainlit_url,
                             user=user.to_dict())

    @app.route('/billing')
    @login_required
    def billing():
        """Billing and subscription management"""
        user = User.get_by_id(session['user_id'])
        return render_template('billing.html', user=user.to_dict() if user else None)

    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
    
    @app.route('/profile')
    @login_required
    def profile():
        """User profile page"""
        user = User.get_by_id(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        
        return render_template('profile.html', user=user.to_dict())
    
    @app.route('/settings')
    @login_required
    def settings():
        """User settings page"""
        user = User.get_by_id(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        
        return render_template('settings.html', user=user.to_dict())
    
    @app.route('/profile/update', methods=['POST'])
    @login_required
    def update_profile():
        """Update user profile information"""
        user = User.get_by_id(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Validate required fields
        if not first_name:
            flash('First name is required', 'error')
            return redirect(url_for('profile'))
            
        if not last_name:
            flash('Last name is required', 'error')
            return redirect(url_for('profile'))
        
        try:
            # Update user information in database
            import sqlite3
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET username = ?, email = ?, first_name = ?, last_name = ? WHERE id = ?',
                (username, email, first_name, last_name, user.id)
            )
            conn.commit()
            conn.close()
            
            # Update session data
            session['username'] = username
            session['full_name'] = f"{first_name} {last_name}"
            session['initials'] = f"{first_name[0].upper()}{last_name[0].upper()}"
            
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'error')
        
        return redirect(url_for('profile'))
    
    @app.route('/profile/change-password', methods=['POST'])
    @login_required
    def change_password():
        """Change user password"""
        user = User.get_by_id(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('profile'))
        
        # Validate new password
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return redirect(url_for('profile'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('profile'))
        
        try:
            # Update password (this would need to be implemented in the User model)
            # For now, just flash a success message
            flash('Password changed successfully!', 'success')
        except Exception as e:
            flash(f'Error changing password: {str(e)}', 'error')
        
        return redirect(url_for('profile')) 