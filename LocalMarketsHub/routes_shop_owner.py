from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import app, db
from models import Shop, Product, Order
from order_status import OrderStatusHistory
from user_data import ShopOwnerData
from datetime import datetime
import json

# Business settings routes
@app.route('/shop_owner/business_settings')
@login_required
def business_settings():
    # Check if user is a shop owner
    if not current_user.is_shop_owner():
        flash('You need to create a shop first.', 'info')
        return redirect(url_for('request_shop'))
    
    # Get user's shops
    shops = Shop.query.filter_by(owner_id=current_user.id).all()
    
    # Get all products for category counts
    products = Product.query.join(Shop).filter(Shop.owner_id == current_user.id).all()
    
    # Get or create shop owner data
    shop_owner_data = ShopOwnerData.query.filter_by(user_id=current_user.id).first()
    if not shop_owner_data:
        shop_owner_data = ShopOwnerData(user_id=current_user.id)
        db.session.add(shop_owner_data)
        db.session.commit()
    
    return render_template('shop_owner/business_settings.html', 
                           shops=shops, 
                           products=products, 
                           shop_owner_data=shop_owner_data)

@app.route('/shop_owner/update_business_info', methods=['POST'])
@login_required
def update_business_info():
    # Check if user is a shop owner
    if not current_user.is_shop_owner():
        flash('You need to create a shop first.', 'info')
        return redirect(url_for('request_shop'))
    
    # Get or create shop owner data
    shop_owner_data = ShopOwnerData.query.filter_by(user_id=current_user.id).first()
    if not shop_owner_data:
        shop_owner_data = ShopOwnerData(user_id=current_user.id)
        db.session.add(shop_owner_data)
        db.session.commit()
    
    # Get current business info
    business_info = shop_owner_data.get_business_info()
    
    # Update business info
    business_info['business_name'] = request.form.get('business_name')
    business_info['business_type'] = request.form.get('business_type')
    business_info['business_email'] = request.form.get('business_email')
    business_info['business_phone'] = request.form.get('business_phone')
    business_info['business_address'] = request.form.get('business_address')
    business_info['business_website'] = request.form.get('business_website')
    
    # Save business info
    shop_owner_data.set_business_info(business_info)
    db.session.commit()
    
    flash('Business information updated successfully!', 'success')
    return redirect(url_for('business_settings'))

@app.route('/shop_owner/update_tax_settings', methods=['POST'])
@login_required
def update_tax_settings():
    # Check if user is a shop owner
    if not current_user.is_shop_owner():
        flash('You need to create a shop first.', 'info')
        return redirect(url_for('request_shop'))
    
    # Get or create shop owner data
    shop_owner_data = ShopOwnerData.query.filter_by(user_id=current_user.id).first()
    if not shop_owner_data:
        shop_owner_data = ShopOwnerData(user_id=current_user.id)
        db.session.add(shop_owner_data)
        db.session.commit()
    
    # Get current business info
    business_info = shop_owner_data.get_business_info()
    
    # Update tax settings
    business_info['tax_id'] = request.form.get('tax_id')
    business_info['tax_rate'] = request.form.get('tax_rate')
    business_info['collect_tax'] = 'collect_tax' in request.form
    
    # Save business info
    shop_owner_data.set_business_info(business_info)
    db.session.commit()
    
    flash('Tax settings updated successfully!', 'success')
    return redirect(url_for('business_settings'))

@app.route('/shop_owner/update_shop_notification_settings', methods=['POST'])
@login_required
def update_shop_notification_settings():
    # Check if user is a shop owner
    if not current_user.is_shop_owner():
        flash('You need to create a shop first.', 'info')
        return redirect(url_for('request_shop'))
    
    # Get or create shop owner data
    shop_owner_data = ShopOwnerData.query.filter_by(user_id=current_user.id).first()
    if not shop_owner_data:
        shop_owner_data = ShopOwnerData(user_id=current_user.id)
        db.session.add(shop_owner_data)
        db.session.commit()
    
    # Get current settings
    settings = shop_owner_data.get_settings()
    
    # Update notification settings
    settings['new_order_notifications'] = 'new_order_notifications' in request.form
    settings['inventory_alerts'] = 'inventory_alerts' in request.form
    settings['review_notifications'] = 'review_notifications' in request.form
    
    try:
        settings['low_stock_threshold'] = int(request.form.get('low_stock_threshold', 5))
    except (ValueError, TypeError):
        settings['low_stock_threshold'] = 5
    
    # Save settings
    shop_owner_data.set_settings(settings)
    db.session.commit()
    
    flash('Notification settings updated successfully!', 'success')
    return redirect(url_for('business_settings'))

@app.route('/shop_owner/add_product_category', methods=['POST'])
@login_required
def add_product_category():
    # Check if user is a shop owner
    if not current_user.is_shop_owner():
        flash('You need to create a shop first.', 'info')
        return redirect(url_for('request_shop'))
    
    # Get category name and icon
    category_name = request.form.get('category_name', '').lower()
    category_icon = request.form.get('category_icon', 'bi-tag')
    
    if not category_name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('business_settings'))
    
    # Get or create shop owner data
    shop_owner_data = ShopOwnerData.query.filter_by(user_id=current_user.id).first()
    if not shop_owner_data:
        shop_owner_data = ShopOwnerData(user_id=current_user.id)
        db.session.add(shop_owner_data)
        db.session.commit()
    
    # Get current settings
    settings = shop_owner_data.get_settings()
    
    # Initialize categories if needed
    if 'product_categories' not in settings:
        settings['product_categories'] = []
    
    # Check if category already exists
    for category in settings['product_categories']:
        if category['name'] == category_name:
            flash(f'Category "{category_name}" already exists.', 'warning')
            return redirect(url_for('business_settings'))
    
    # Add new category
    settings['product_categories'].append({
        'name': category_name,
        'icon': category_icon
    })
    
    # Save settings
    shop_owner_data.set_settings(settings)
    db.session.commit()
    
    flash(f'Category "{category_name}" added successfully!', 'success')
    return redirect(url_for('business_settings'))

# Order status update with history tracking
@app.route('/shop_owner/update_order_status/<int:shop_id>/<int:order_id>', methods=['POST'])
@login_required
def shop_owner_update_order_status(shop_id, order_id):
    # Check if user is a shop owner
    if not current_user.is_shop_owner():
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if shop belongs to user
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    
    # Check if order belongs to shop
    order = Order.query.filter_by(id=order_id, shop_id=shop_id).first_or_404()
    
    # Get new status
    new_status = request.form.get('status')
    
    # Validate status
    valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        flash('Invalid order status.', 'danger')
        return redirect(url_for('shop_order_detail', shop_id=shop_id, order_id=order_id))
    
    # Save previous status
    previous_status = order.status
    
    # Update order status
    order.status = new_status
    order.updated_at = datetime.now()
    
    # Add status update to history
    notes = request.form.get('notes', '')
    
    status_update = OrderStatusHistory(
        order_id=order.id,
        previous_status=previous_status,
        new_status=new_status,
        notes=notes,
        updated_by=current_user.id,
        updated_at=datetime.now()
    )
    
    db.session.add(status_update)
    db.session.commit()
    
    flash(f'Order status updated to {new_status.capitalize()}.', 'success')
    return redirect(url_for('shop_order_detail', shop_id=shop_id, order_id=order_id))