import os
import stripe
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User
from datetime import datetime, timedelta

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Create blueprint
stripe_bp = Blueprint('stripe', __name__)


# Pricing configuration
PRICING_PLANS = {
    'pro': {
        'name': 'Pro',
        'price': 9,
        'price_id': os.environ.get('STRIPE_PRO_PRICE_ID'),
        'features': [
            '5 programs',
            '25 projects',
            'Unlimited tasks',
            '25 contacts',
            'Materials tracking',
            'Milestones',
            'Priority support'
        ]
    },
    'business': {
        'name': 'Business',
        'price': 29,
        'price_id': os.environ.get('STRIPE_BUSINESS_PRICE_ID'),
        'features': [
            'Unlimited programs',
            'Unlimited projects',
            'Unlimited tasks',
            'Unlimited contacts',
            'All Pro features',
            'Advanced reporting (coming soon)',
            'API access (coming soon)',
            'Premium support'
        ]
    }
}


@stripe_bp.route('/pricing')
def pricing():
    """Display pricing page"""
    return render_template('pricing.html', 
                         plans=PRICING_PLANS,
                         current_tier=current_user.subscription_tier if current_user.is_authenticated else 'free')


@stripe_bp.route('/subscription')
@login_required
def subscription():
    """Display subscription management page"""
    # Get subscription details if user has one
    subscription_details = None
    if current_user.stripe_subscription_id:
        try:
            subscription_details = stripe.Subscription.retrieve(current_user.stripe_subscription_id)
        except stripe.error.StripeError as e:
            flash(f'Error retrieving subscription: {str(e)}', 'danger')
    
    return render_template('subscription.html', 
                         subscription=subscription_details,
                         plans=PRICING_PLANS)


@stripe_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    plan = request.form.get('plan')
    
    if plan not in PRICING_PLANS:
        flash('Invalid plan selected', 'danger')
        return redirect(url_for('stripe.pricing'))
    
    price_id = PRICING_PLANS[plan]['price_id']
    
    if not price_id:
        flash('Pricing not configured. Please contact support.', 'danger')
        return redirect(url_for('stripe.pricing'))
    
    try:
        # Create or retrieve Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={
                    'user_id': current_user.id,
                    'username': current_user.username
                }
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('stripe.checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('stripe.pricing', _external=True),
            metadata={
                'user_id': current_user.id,
                'plan': plan
            }
        )
        
        return redirect(checkout_session.url, code=303)
    
    except stripe.error.StripeError as e:
        flash(f'Error creating checkout session: {str(e)}', 'danger')
        return redirect(url_for('stripe.pricing'))


@stripe_bp.route('/checkout/success')
@login_required
def checkout_success():
    """Handle successful checkout"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid checkout session', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Update user subscription
        current_user.stripe_subscription_id = session.subscription
        current_user.subscription_tier = session.metadata.get('plan', 'pro')
        current_user.subscription_status = 'active'
        
        db.session.commit()
        
        flash(f'Successfully subscribed to {PRICING_PLANS[current_user.subscription_tier]["name"]} plan!', 'success')
        return redirect(url_for('dashboard'))
    
    except stripe.error.StripeError as e:
        flash(f'Error processing subscription: {str(e)}', 'danger')
        return redirect(url_for('stripe.pricing'))


@stripe_bp.route('/create-portal-session', methods=['POST'])
@login_required
def create_portal_session():
    """Create Stripe customer portal session for managing subscription"""
    if not current_user.stripe_customer_id:
        flash('No active subscription found', 'warning')
        return redirect(url_for('stripe.pricing'))
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=url_for('stripe.subscription', _external=True)
        )
        return redirect(portal_session.url, code=303)
    
    except stripe.error.StripeError as e:
        flash(f'Error accessing customer portal: {str(e)}', 'danger')
        return redirect(url_for('stripe.subscription'))


@stripe_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        # Invalid payload
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_payment_succeeded(invoice)
    
    return jsonify({'status': 'success'}), 200


def handle_subscription_updated(subscription):
    """Handle subscription updated webhook"""
    customer_id = subscription.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        user.subscription_status = subscription.get('status')
        
        # Update subscription end date
        if subscription.get('current_period_end'):
            user.subscription_end_date = datetime.fromtimestamp(subscription['current_period_end'])
        
        db.session.commit()


def handle_subscription_deleted(subscription):
    """Handle subscription deleted webhook"""
    customer_id = subscription.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        user.subscription_tier = 'free'
        user.subscription_status = 'canceled'
        user.stripe_subscription_id = None
        db.session.commit()


def handle_payment_failed(invoice):
    """Handle payment failed webhook"""
    customer_id = invoice.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        user.subscription_status = 'past_due'
        db.session.commit()
        # TODO: Send email notification to user


def handle_payment_succeeded(invoice):
    """Handle payment succeeded webhook"""
    customer_id = invoice.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        user.subscription_status = 'active'
        db.session.commit()
