"""
API routes for We-Relate Flask app
"""
from flask import session, request, jsonify

from auth.models import User
from auth.decorators import login_required


def register_api_routes(app):
    """Register API routes"""
    
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