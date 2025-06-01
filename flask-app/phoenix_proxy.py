"""
Phoenix iframe integration for admin users.
Provides secure access to Phoenix observability through iframe embedding.
"""

import os
import requests
from flask import Blueprint, render_template, jsonify, current_app
from functools import wraps
from auth.decorators import admin_required

phoenix_bp = Blueprint('phoenix', __name__)

def get_phoenix_url():
    """Get Phoenix service URL from environment."""
    return os.environ.get('PHOENIX_SERVICE_URL', 'http://localhost:6006')

def check_phoenix_health():
    """Check if Phoenix service is accessible."""
    try:
        phoenix_url = get_phoenix_url()
        response = requests.get(f"{phoenix_url}/", timeout=5)
        return response.status_code == 200
    except:
        return False

@phoenix_bp.route('/admin/phoenix')
@admin_required
def phoenix_dashboard():
    """
    Render Phoenix dashboard in iframe for admin users.
    Provides secure, embedded access to Phoenix observability.
    """
    phoenix_url = get_phoenix_url()
    return render_template('phoenix_iframe.html', phoenix_url=phoenix_url)

@phoenix_bp.route('/admin/phoenix/health')
@admin_required  
def phoenix_health():
    """
    Health check endpoint for Phoenix service.
    Returns JSON status for admin monitoring.
    """
    phoenix_url = get_phoenix_url()
    is_healthy = check_phoenix_health()
    
    return jsonify({
        'status': 'healthy' if is_healthy else 'unhealthy',
        'phoenix_url': phoenix_url,
        'accessible': is_healthy,
        'message': 'Phoenix service is accessible' if is_healthy else 'Phoenix service is not accessible'
    })

@phoenix_bp.route('/admin/phoenix/status')
@admin_required
def phoenix_status():
    """
    Detailed status endpoint for Phoenix service.
    Provides comprehensive health and configuration info.
    """
    phoenix_url = get_phoenix_url()
    is_healthy = check_phoenix_health()
    
    status_info = {
        'service': 'Phoenix AI Observability',
        'url': phoenix_url,
        'status': 'online' if is_healthy else 'offline',
        'accessible': is_healthy,
        'integration_type': 'iframe_embed',
        'auth_required': True,
        'admin_only': True
    }
    
    if is_healthy:
        try:
            # Try to get additional Phoenix info
            response = requests.get(f"{phoenix_url}/", timeout=3)
            status_info['response_time'] = response.elapsed.total_seconds()
            status_info['http_status'] = response.status_code
        except:
            pass
    
    return jsonify(status_info)

@phoenix_bp.route('/test-health')
def test_phoenix_health():
    """Test endpoint to verify Phoenix integration (bypasses auth for testing)."""
    try:
        phoenix_url = get_phoenix_url()
        response = requests.get(f"{phoenix_url}/", timeout=5)
        return jsonify({
            'status': 'success',
            'phoenix_url': phoenix_url,
            'phoenix_status_code': response.status_code,
            'phoenix_accessible': response.status_code == 200
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'phoenix_url': get_phoenix_url(),
            'error': str(e),
            'phoenix_accessible': False
        }), 500 