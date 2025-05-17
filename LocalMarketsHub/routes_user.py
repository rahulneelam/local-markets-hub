from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import app, db
from models import User, Shop, Product, Order, WatchlistItem
from user_data import UserData
from datetime import datetime
import json

# User preferences routes
@app.route('/user/preferences')
@login_required
def user_preferences():
    # Get or create user data
    user_data = UserData.query.filter_by(user_id=current_user.id).first()
    if not user_data:
        user_data = UserData(user_id=current_user.id)
        db.session.add(user_data)
        db.session.commit()
    
    return render_template('user/preferences.html', user_data=user_data)

@app.route('/user/update_profile', methods=['POST'])
@login_required
def update_user_profile():
    # Update user profile information
    current_user.first_name = request.form.get('first_name')
    current_user.last_name = request.form.get('last_name')
    current_user.email = request.form.get('email')
    current_user.profile_image_url = request.form.get('profile_image_url')
    
    db.session.commit()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('user_preferences'))

@app.route('/user/save_address', methods=['POST'])
@login_required
def save_address():
    # Get or create user data
    user_data = UserData.query.filter_by(user_id=current_user.id).first()
    if not user_data:
        user_data = UserData(user_id=current_user.id)
        db.session.add(user_data)
        db.session.commit()
    
    # Get form data
    address_index = request.form.get('address_index', '-1')
    address = {
        'name': request.form.get('name'),
        'street': request.form.get('street'),
        'city': request.form.get('city'),
        'state': request.form.get('state'),
        'zipcode': request.form.get('zipcode'),
        'phone': request.form.get('phone')
    }
    
    # Get existing addresses
    addresses = user_data.get_saved_addresses()
    
    # Add or update address
    if address_index == '-1':
        addresses.append(address)
    else:
        addresses[int(address_index)] = address
    
    # Save addresses
    user_data.set_saved_addresses(addresses)
    db.session.commit()
    
    flash('Address saved successfully!', 'success')
    return redirect(url_for('user_preferences'))

@app.route('/api/user/address/<int:index>')
@login_required
def get_address(index):
    # Get user data
    user_data = UserData.query.filter_by(user_id=current_user.id).first()
    if not user_data:
        return jsonify({'error': 'User data not found'}), 404
    
    # Get addresses
    addresses = user_data.get_saved_addresses()
    
    # Return address at index
    if 0 <= index < len(addresses):
        return jsonify(addresses[index])
    
    return jsonify({'error': 'Address not found'}), 404

@app.route('/api/user/address/<int:index>/delete', methods=['POST'])
@login_required
def delete_address(index):
    # Get user data
    user_data = UserData.query.filter_by(user_id=current_user.id).first()
    if not user_data:
        return jsonify({'success': False, 'message': 'User data not found'}), 404
    
    # Get addresses
    addresses = user_data.get_saved_addresses()
    
    # Delete address at index
    if 0 <= index < len(addresses):
        addresses.pop(index)
        user_data.set_saved_addresses(addresses)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Address not found'}), 404

@app.route('/user/update_notification_settings', methods=['POST'])
@login_required
def update_notification_settings():
    # Get or create user data
    user_data = UserData.query.filter_by(user_id=current_user.id).first()
    if not user_data:
        user_data = UserData(user_id=current_user.id)
        db.session.add(user_data)
        db.session.commit()
    
    # Get current preferences
    preferences = user_data.get_preferences()
    
    # Update preferences
    preferences['email_notifications'] = 'email_notifications' in request.form
    preferences['order_updates'] = 'order_updates' in request.form
    preferences['promotions'] = 'promotions' in request.form
    preferences['watchlist_alerts'] = 'watchlist_alerts' in request.form
    
    # Save preferences
    user_data.set_preferences(preferences)
    db.session.commit()
    
    flash('Notification settings updated successfully!', 'success')
    return redirect(url_for('user_preferences'))

@app.route('/user/update_appearance_settings', methods=['POST'])
@login_required
def update_appearance_settings():
    # Get or create user data
    user_data = UserData.query.filter_by(user_id=current_user.id).first()
    if not user_data:
        user_data = UserData(user_id=current_user.id)
        db.session.add(user_data)
        db.session.commit()
    
    # Get current preferences
    preferences = user_data.get_preferences()
    
    # Update preferences
    preferences['theme'] = request.form.get('theme')
    try:
        preferences['products_per_page'] = int(request.form.get('products_per_page', 12))
    except (ValueError, TypeError):
        preferences['products_per_page'] = 12
    
    # Save preferences
    user_data.set_preferences(preferences)
    db.session.commit()
    
    flash('Appearance settings updated successfully!', 'success')
    return redirect(url_for('user_preferences'))

# Enhanced order tracking view
@app.route('/user/track_order/<int:order_id>')
@login_required
def user_track_order(order_id):
    # Get order
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    return render_template('user/track_order.html', order=order)

# Cancel order functionality
@app.route('/user/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def user_cancel_order(order_id):
    # Get order
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    # Check if order can be cancelled
    if order.status in ['cancelled', 'delivered']:
        flash('This order cannot be cancelled.', 'danger')
        return redirect(url_for('track_order', order_id=order.id))
    
    # Get reason
    reason = request.form.get('reason', 'Cancelled by user')
    
    # Save previous status
    previous_status = order.status
    
    # Update order status
    order.status = 'cancelled'
    order.updated_at = datetime.now()
    
    # Add status update to history
    from order_status import OrderStatusHistory
    status_update = OrderStatusHistory(
        order_id=order.id,
        previous_status=previous_status,
        new_status='cancelled',
        notes=reason,
        updated_by=current_user.id,
        updated_at=datetime.now()
    )
    
    db.session.add(status_update)
    db.session.commit()
    
    flash('Order cancelled successfully.', 'success')
    return redirect(url_for('track_order', order_id=order.id))