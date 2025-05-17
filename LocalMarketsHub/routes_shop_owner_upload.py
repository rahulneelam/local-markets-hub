from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from app import app, db
from models import Shop, Product, Order
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

# Configure upload folder for shop and product images
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    if filename is None:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Check if user is shop owner of a specific shop
def is_shop_owner(shop_id):
    shop = Shop.query.get(shop_id)
    return shop and shop.owner_id == current_user.id

# Product image upload route
@app.route('/shop_owner/shop/<int:shop_id>/product/<int:product_id>/upload_image', methods=['POST'])
@login_required
def upload_product_image(shop_id, product_id):
    # Verify shop ownership
    if not is_shop_owner(shop_id):
        flash('Access denied. You do not own this shop.', 'danger')
        return redirect(url_for('shop_owner_dashboard'))
    
    # Get the product
    product = Product.query.filter_by(id=product_id, shop_id=shop_id).first_or_404()
    
    # Check if image URL is provided
    image_url = request.form.get('image_url')
    if image_url:
        product.image_url = image_url
        db.session.commit()
        flash('Product image updated successfully!', 'success')
        return redirect(url_for('edit_product', shop_id=shop_id, product_id=product_id))
    
    # Check if file is in the request
    if 'product_image' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('edit_product', shop_id=shop_id, product_id=product_id))
    
    file = request.files['product_image']
    
    # If user submits empty form (no file selected)
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('edit_product', shop_id=shop_id, product_id=product_id))
    
    # Process and save the file
    if file and allowed_file(file.filename):
        # Create a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Save file to upload folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Update product with new image URL
        product.image_url = f"/static/uploads/{unique_filename}"
        db.session.commit()
        
        flash('Product image uploaded successfully!', 'success')
        return redirect(url_for('edit_product', shop_id=shop_id, product_id=product_id))
    
    flash('Invalid file type. Allowed types: png, jpg, jpeg, gif, webp', 'danger')
    return redirect(url_for('edit_product', shop_id=shop_id, product_id=product_id))

# Shop image upload route
@app.route('/shop_owner/shop/<int:shop_id>/upload_image', methods=['POST'])
@login_required
def update_shop_image(shop_id):
    # Verify shop ownership
    if not is_shop_owner(shop_id):
        flash('Access denied. You do not own this shop.', 'danger')
        return redirect(url_for('shop_owner_dashboard'))
    
    # Get the shop
    shop = Shop.query.get_or_404(shop_id)
    
    # Check if image URL is provided
    image_url = request.form.get('image_url')
    if image_url:
        shop.image_url = image_url
        db.session.commit()
        flash('Shop image updated successfully!', 'success')
        return redirect(url_for('shop_settings', shop_id=shop_id))
    
    # Check if file is in the request
    if 'shop_image' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('shop_settings', shop_id=shop_id))
    
    file = request.files['shop_image']
    
    # If user submits empty form (no file selected)
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('shop_settings', shop_id=shop_id))
    
    # Process and save the file
    if file and allowed_file(file.filename):
        # Create a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Save file to upload folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Update shop with new image URL
        shop.image_url = f"/static/uploads/{unique_filename}"
        db.session.commit()
        
        flash('Shop image uploaded successfully!', 'success')
        return redirect(url_for('shop_settings', shop_id=shop_id))
    
    flash('Invalid file type. Allowed types: png, jpg, jpeg, gif, webp', 'danger')
    return redirect(url_for('shop_settings', shop_id=shop_id))

# Shop categories update route
@app.route('/shop_owner/shop/<int:shop_id>/update_info', methods=['POST'])
@login_required
def update_shop_info(shop_id):
    # Verify shop ownership
    if not is_shop_owner(shop_id):
        flash('Access denied. You do not own this shop.', 'danger')
        return redirect(url_for('shop_owner_dashboard'))
    
    # Get the shop
    shop = Shop.query.get_or_404(shop_id)
    
    # Update shop information
    shop.name = request.form.get('name')
    shop.description = request.form.get('description')
    shop.email = request.form.get('email')
    shop.phone = request.form.get('phone')
    shop.address = request.form.get('address')
    
    # Handle categories - convert list to comma-separated string
    selected_categories = request.form.getlist('categories')
    shop.categories = ','.join(selected_categories) if selected_categories else None
    
    # Update timestamp
    shop.updated_at = datetime.now()
    
    db.session.commit()
    
    flash('Shop information updated successfully!', 'success')
    return redirect(url_for('shop_settings', shop_id=shop_id))

# Shop settings page route
@app.route('/shop_owner/shop/<int:shop_id>/settings')
@login_required
def shop_settings(shop_id):
    # Verify shop ownership
    if not is_shop_owner(shop_id):
        flash('Access denied. You do not own this shop.', 'danger')
        return redirect(url_for('shop_owner_dashboard'))
    
    # Get the shop
    shop = Shop.query.get_or_404(shop_id)
    
    # Parse categories
    if shop.categories:
        shop.categories_list = shop.categories.split(',')
    else:
        shop.categories_list = []
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Order.total_price)).filter(Order.shop_id == shop_id).scalar() or 0
    
    return render_template('shop_owner/shop_settings.html', 
                          shop=shop, 
                          total_revenue=total_revenue)