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
            password = request.form['password']
            confirm_password = request.form.get('confirmPassword')
            
            # Basic validation
            if not email:
                flash('Email is required', 'error')
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
                User.create(email, email, password)
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

    @app.route('/settings')
    @login_required
    def settings():
        """User settings page"""
        user = User.get_by_id(session['user_id'])
        return render_template('settings.html', user=user.to_dict() if user else None)

    @app.route('/health')
    def health():
        """Health check endpoint for Cloud Run"""
        return jsonify({
            'status': 'healthy', 
            'service': 'flask-app', 
            'timestamp': datetime.now().isoformat()
        }) 