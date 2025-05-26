from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from auth.decorators import login_required
from auth.models import User
from .models import Subscription, Payment

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/')
@login_required
def index():
    """Billing dashboard"""
    user = User.get_by_id(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get user's subscriptions and payments
    subscriptions = Subscription.get_by_user_id(user.id)
    payments = Payment.get_by_user_id(user.id)
    active_subscription = Subscription.get_active_by_user_id(user.id)
    
    return render_template('billing.html', 
                         user=user.to_dict(),
                         subscriptions=[s.to_dict() for s in subscriptions],
                         payments=[p.to_dict() for p in payments],
                         active_subscription=active_subscription.to_dict() if active_subscription else None)

@billing_bp.route('/upgrade', methods=['POST'])
@login_required
def upgrade():
    """Upgrade user subscription"""
    user = User.get_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    tier = request.json.get('tier', 'premium')
    duration = request.json.get('duration', 1)  # months
    
    # In a real app, you'd integrate with Stripe here
    # For now, we'll just create a subscription directly
    try:
        subscription = Subscription.create(
            user_id=user.id,
            tier=tier,
            duration_months=duration
        )
        
        flash(f'Successfully upgraded to {tier} tier!', 'success')
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@billing_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user subscription"""
    user = User.get_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    active_subscription = Subscription.get_active_by_user_id(user.id)
    if not active_subscription:
        return jsonify({'error': 'No active subscription found'}), 404
    
    try:
        active_subscription.cancel()
        flash('Subscription cancelled successfully', 'info')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@billing_bp.route('/api/subscription/status')
@login_required
def subscription_status():
    """Get current subscription status"""
    user = User.get_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    active_subscription = Subscription.get_active_by_user_id(user.id)
    
    return jsonify({
        'user_tier': user.tier,
        'credits': user.credits,
        'active_subscription': active_subscription.to_dict() if active_subscription else None
    }) 