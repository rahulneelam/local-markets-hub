from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import app, db
from models import User, Shop, Product, Order, ShopReview, ProductReview, OrderItem
from sqlalchemy import func, desc
import json
from datetime import datetime, timedelta

# Admin access decorator
def admin_required(f):
    """Decorator to check if user is an admin."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Admin dashboard
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Count statistics
    user_count = User.query.filter(User.is_admin == False).count()
    shop_owner_count = db.session.query(User).join(Shop, User.id == Shop.owner_id).distinct().count()
    shop_count = Shop.query.count()
    order_count = Order.query.count()
    
    # Recent users
    recent_users = User.query.filter(User.is_admin == False).order_by(User.created_at.desc()).limit(5).all()
    
    # Pending shop requests
    pending_shops = Shop.query.filter_by(status='pending').all()
    
    # Shop owners for the tab
    shop_owners = User.query.join(Shop, User.id == Shop.owner_id).distinct().limit(5).all()
    
    # Recent reviews - combine shop and product reviews
    shop_reviews = ShopReview.query.order_by(ShopReview.created_at.desc()).limit(3).all()
    product_reviews = ProductReview.query.order_by(ProductReview.created_at.desc()).limit(3).all()
    
    # Combine reviews
    recent_reviews = []
    for review in shop_reviews:
        recent_reviews.append(review)
    for review in product_reviews:
        recent_reviews.append(review)
    
    # Sort by date
    recent_reviews = sorted(recent_reviews, key=lambda x: x.created_at, reverse=True)[:5]
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Top-selling products
    top_selling_products = db.session.query(
        Product, func.sum(Order.total_price).label('revenue')
    ).join(Order, Product.shop_id == Order.shop_id).group_by(Product.id).order_by(desc('revenue')).limit(5).all()
    
    # Top revenue shops
    top_shops = db.session.query(
        Shop, func.sum(Order.total_price).label('revenue')
    ).join(Order).group_by(Shop.id).order_by(desc('revenue')).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          user_count=user_count,
                          shop_owner_count=shop_owner_count,
                          shop_count=shop_count,
                          order_count=order_count,
                          recent_users=recent_users,
                          pending_shops=pending_shops,
                          shop_owners=shop_owners,
                          recent_reviews=recent_reviews,
                          recent_orders=recent_orders,
                          top_selling_products=top_selling_products,
                          top_shops=top_shops)

# Admin users
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.filter(User.is_admin == False).all()
    return render_template('admin/users.html', users=users)

# Admin shop owners
@app.route('/admin/shop-owners')
@login_required
@admin_required
def admin_shop_owners():
    # Get all users who are shop owners (have shops)
    shop_owners = User.query.join(Shop, User.id == Shop.owner_id).distinct().all()
    return render_template('admin/shop_owners.html', shop_owners=shop_owners)

# View shop owner details
@app.route('/admin/shop-owners/<int:user_id>')
@login_required
@admin_required
def admin_view_shop_owner(user_id):
    owner = User.query.get_or_404(user_id)
    
    # Ensure user is a shop owner
    if not owner.shops.count() > 0:
        flash('This user is not a shop owner.', 'warning')
        return redirect(url_for('admin_shop_owners'))
    
    # Get shop owner's shop reviews
    shop_ids = [shop.id for shop in owner.shops]
    shop_reviews = ShopReview.query.filter(ShopReview.shop_id.in_(shop_ids)).order_by(ShopReview.created_at.desc()).all() if shop_ids else []
    
    # Get product reviews for owner's products
    product_ids = []
    for shop in owner.shops:
        for product in shop.products:
            product_ids.append(product.id)
    
    product_reviews = ProductReview.query.filter(ProductReview.product_id.in_(product_ids)).order_by(ProductReview.created_at.desc()).all() if product_ids else []
    
    # Combine reviews
    recent_reviews = []
    for review in shop_reviews:
        recent_reviews.append(review)
    for review in product_reviews:
        recent_reviews.append(review)
    
    # Sort by date
    recent_reviews = sorted(recent_reviews, key=lambda x: x.created_at, reverse=True)[:10]
    
    return render_template('admin/shop_owner_detail.html', 
                          owner=owner, 
                          recent_reviews=recent_reviews)

# Admin shops
@app.route('/admin/shops')
@login_required
@admin_required
def admin_shops():
    shops = Shop.query.all()
    return render_template('admin/shops.html', shops=shops)

# Admin shop detail
@app.route('/admin/shops/<int:shop_id>')
@login_required
@admin_required
def admin_shop_detail(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    return render_template('admin/shop_detail.html', shop=shop, Order=Order)

# Approve shop
@app.route('/admin/shops/<int:shop_id>/approve')
@login_required
@admin_required
def approve_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    shop.status = 'approved'
    db.session.commit()
    flash(f'Shop "{shop.name}" has been approved.', 'success')
    return redirect(url_for('admin_shops'))

# Reject shop
@app.route('/admin/shops/<int:shop_id>/reject')
@login_required
@admin_required
def reject_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    shop.status = 'rejected'
    db.session.commit()
    flash(f'Shop "{shop.name}" has been rejected.', 'danger')
    return redirect(url_for('admin_shops'))

# Suspend shop
@app.route('/admin/shops/<int:shop_id>/suspend')
@login_required
@admin_required
def suspend_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    shop.status = 'suspended'
    db.session.commit()
    flash(f'Shop "{shop.name}" has been suspended.', 'warning')
    return redirect(url_for('admin_shops'))

# Delete shop
@app.route('/admin/shops/<int:shop_id>/delete')
@login_required
@admin_required
def delete_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    shop_name = shop.name
    db.session.delete(shop)
    db.session.commit()
    flash(f'Shop "{shop_name}" has been permanently deleted.', 'danger')
    return redirect(url_for('admin_shops'))

# Admin orders
@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

# Admin reviews
@app.route('/admin/reviews')
@login_required
@admin_required
def admin_reviews():
    shop_reviews = ShopReview.query.order_by(ShopReview.created_at.desc()).all()
    product_reviews = ProductReview.query.order_by(ProductReview.created_at.desc()).all()
    return render_template('admin/reviews.html', shop_reviews=shop_reviews, product_reviews=product_reviews)

# Admin delete shop review
@app.route('/admin/shop-reviews/<int:review_id>/delete')
@login_required
@admin_required
def admin_delete_shop_review(review_id):
    review = ShopReview.query.get_or_404(review_id)
    shop_name = review.shop.name
    db.session.delete(review)
    db.session.commit()
    flash(f'Shop review for "{shop_name}" has been deleted.', 'success')
    return redirect(url_for('admin_reviews'))

# Admin delete product review
@app.route('/admin/product-reviews/<int:review_id>/delete')
@login_required
@admin_required
def admin_delete_product_review(review_id):
    review = ProductReview.query.get_or_404(review_id)
    product_name = review.product.name
    db.session.delete(review)
    db.session.commit()
    flash(f'Product review for "{product_name}" has been deleted.', 'success')
    return redirect(url_for('admin_reviews'))