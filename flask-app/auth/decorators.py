from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from .models import User

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        
        user = User.get_by_id(session['user_id'])
        if not user or user.tier != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin privileges required'}), 403
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def tier_required(required_tier):
    """Decorator to require specific user tier"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login'))
            
            user = User.get_by_id(session['user_id'])
            if not user:
                if request.is_json:
                    return jsonify({'error': 'User not found'}), 404
                return redirect(url_for('login'))
            
            tier_hierarchy = {'free': 0, 'premium': 1, 'admin': 2}
            user_tier_level = tier_hierarchy.get(user.tier, 0)
            required_tier_level = tier_hierarchy.get(required_tier, 0)
            
            if user_tier_level < required_tier_level:
                if request.is_json:
                    return jsonify({'error': f'{required_tier} tier required'}), 403
                return redirect(url_for('billing'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator 