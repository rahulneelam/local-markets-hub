from flask import render_template, request, jsonify, redirect, url_for, flash, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Shop, Product, Order, OrderItem, WatchlistItem, ShopReview, ProductReview
from order_status import OrderStatusHistory
from user_data import UserData, ShopOwnerData
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
import logging

# Home page
@app.route('/')
def index():
    # Get query and category parameters
    search_query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    # Get approved shops
    shops_query = Shop.query.filter_by(status='approved')
    shops = shops_query.all()
    
    # Get featured or filtered products
    products_query = Product.query.join(Shop).filter(Shop.status == 'approved', Product.is_available == True)
    
    # Apply category filter if provided
    if category:
        products_query = products_query.filter(Product.category == category)
    
    # Apply search filter if provided
    if search_query:
        products_query = products_query.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%'),
                Shop.name.ilike(f'%{search_query}%')
            )
        )
    
    # Get products
    products = products_query.limit(12).all()
    
    return render_template('index.html', shops=shops, products=products, 
                         current_category=category, search_query=search_query)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Admin user check
        if username == "RAHUL" and password == "Rahul@123":
            user = User.query.filter_by(username="RAHUL").first()
            if user:
                login_user(user)
                next_page = request.args.get('next', url_for('admin_dashboard'))
                return redirect(next_page)
        
        # Regular user login
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next', url_for('dashboard'))
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Make sure email is not empty string
        if email == '':
            email = None
        
        # Check if username or email already exists
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first() if email else None
        
        if user_exists:
            flash('Username already taken', 'danger')
        elif email_exists:
            flash('Email already registered', 'danger')
        else:
            try:
                # Create new user
                new_user = User(username=username, email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Registration error: {str(e)}")
                flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# User dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard_view'))
    elif current_user.is_shop_owner():
        return redirect(url_for('shop_owner_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

# Admin Dashboard - Direct route
@app.route('/admin')
@login_required
def admin_dashboard_view():
    if not current_user.is_admin:
        abort(403)
    
    # Get basic stats for the dashboard
    users = User.query.filter(User.is_admin == False).all()
    recent_users = User.query.filter(User.is_admin == False).order_by(User.created_at.desc()).limit(5).all()
    
    # Get shop owners by checking which users have shops
    shop_owners = []
    try:
        shop_owners = db.session.query(User).join(Shop, User.id == Shop.owner_id).distinct().all()
    except Exception as e:
        logging.error(f"Error getting shop owners: {e}")
    
    # Shop statistics
    shops = Shop.query.all()
    pending_shops = Shop.query.filter_by(status='pending').all()
    
    # Order statistics
    orders = Order.query.all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html', 
                          users=users or [],
                          recent_users=recent_users or [],
                          shop_owners=shop_owners or [],
                          shops=shops or [],
                          pending_shops=pending_shops or [],
                          orders=orders or [],
                          recent_orders=recent_orders or [])

# User section routes
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    # Get all approved shops to display
    shops = Shop.query.filter_by(status='approved').all()
    # Get user's orders
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    # Get user's watchlist
    watchlist = WatchlistItem.query.filter_by(user_id=current_user.id).all()
    
    return render_template('user/dashboard.html', 
                          shops=shops, 
                          orders=orders, 
                          watchlist=watchlist)

@app.route('/user/shops')
@login_required
def user_shops():
    shops = Shop.query.filter_by(status='approved').all()
    return render_template('user/shops.html', shops=shops)

@app.route('/user/shop/<int:shop_id>')
@login_required
def view_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.status != 'approved':
        flash('This shop is not available', 'warning')
        return redirect(url_for('user_shops'))
    
    products = Product.query.filter_by(shop_id=shop.id, is_available=True).all()
    return render_template('user/shop_detail.html', shop=shop, products=products)

@app.route('/user/orders')
@login_required
def user_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('user/orders.html', orders=orders)

@app.route('/user/track_order/<int:order_id>')
@login_required
def track_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    shop = Shop.query.get_or_404(order.shop_id)
    order_items = OrderItem.query.filter_by(order_id=order_id).all()
    
    # Get actual status history from database
    status_updates = OrderStatusHistory.query.filter_by(order_id=order.id).order_by(OrderStatusHistory.updated_at.asc()).all()
    
    # Create initial status entry for order creation
    timeline = [
        {
            'status': 'Ordered',
            'date': order.created_at,
            'description': 'Your order has been placed successfully.',
            'notes': None,
            'completed': True
        }
    ]
    
    # Add actual status updates with real timestamps
    status_mapping = {
        'pending': 'Ordered',
        'processing': 'Processing',
        'shipped': 'Ready for pickup',
        'delivered': 'Completed',
        'cancelled': 'Cancelled'
    }
    
    descriptions = {
        'processing': 'Shop owner is preparing your order.',
        'shipped': 'Your order is packed and ready for pickup at the shop.',
        'delivered': 'You have received your order.',
        'cancelled': 'This order has been cancelled.'
    }
    
    # Add all status updates to timeline
    for update in status_updates:
        if update.new_status in status_mapping:
            timeline.append({
                'status': status_mapping[update.new_status],
                'date': update.updated_at,
                'description': descriptions.get(update.new_status, ''),
                'notes': update.notes,
                'completed': True
            })
    
    # If no history exists, fallback to the predicted timeline
    if len(timeline) <= 1:
        timeline.extend([
            {
                'status': 'Processing',
                'date': order.updated_at if order.status != 'pending' else None,
                'description': 'Shop owner is preparing your order.',
                'notes': None,
                'completed': order.status not in ['pending']
            },
            {
                'status': 'Ready for pickup',
                'date': order.updated_at if order.status in ['shipped', 'delivered'] else None,
                'description': 'Your order is packed and ready for pickup at the shop.',
                'notes': None,
                'completed': order.status in ['shipped', 'delivered']
            },
            {
                'status': 'Completed',
                'date': order.updated_at if order.status == 'delivered' else None,
                'description': 'You have received your order.',
                'notes': None,
                'completed': order.status == 'delivered'
            }
        ])
    
    # Sort timeline by completion status and date
    timeline.sort(key=lambda x: (not x['completed'], x['date'] or datetime.min))
    
    return render_template('user/track_order.html', 
                          order=order, 
                          shop=shop, 
                          order_items=order_items,
                          status_history=timeline)

@app.route('/user/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    # Only allow cancellation if order is still pending
    if order.status == 'pending':
        previous_status = order.status
        order.status = 'cancelled'
        
        # Create a status update record
        status_update = OrderStatusHistory(
            order_id=order.id,
            previous_status=previous_status,
            new_status='cancelled',
            notes='Cancelled by customer',
            updated_by=current_user.id,
            updated_at=datetime.now()
        )
        
        db.session.add(status_update)
        db.session.commit()
        flash('Your order has been cancelled successfully.', 'success')
    else:
        flash('Sorry, this order cannot be cancelled as it is already being processed.', 'danger')
    
    return redirect(url_for('user_orders'))

@app.route('/user/watchlist')
@login_required
def user_watchlist():
    watchlist_items = WatchlistItem.query.filter_by(user_id=current_user.id).all()
    return render_template('user/watchlist.html', watchlist_items=watchlist_items)

@app.route('/user/watchlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_watchlist(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if already in watchlist
    existing = WatchlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash('Product already in watchlist', 'info')
    else:
        watchlist_item = WatchlistItem(user_id=current_user.id, product_id=product_id)
        db.session.add(watchlist_item)
        db.session.commit()
        flash('Product added to watchlist', 'success')
    
    return redirect(url_for('view_shop', shop_id=product.shop_id))

@app.route('/user/watchlist/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_watchlist(item_id):
    watchlist_item = WatchlistItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(watchlist_item)
    db.session.commit()
    flash('Product removed from watchlist', 'success')
    return redirect(url_for('user_watchlist'))

# Order placement routes
@app.route('/user/cart')
@login_required
def view_cart():
    # Ensure cart exists in session with default values
    if 'cart' not in session:
        session['cart'] = {'items': [], 'total': 0.0, 'shop_id': None}
    
    cart = session['cart']
    
    # Get product details for items in cart
    cart_products = []
    shop = None
    
    if cart['items']:
        # Recalculate total price in case product prices changed
        total = 0
        
        for item in cart['items']:
            product = Product.query.get(item['product_id'])
            if product and product.is_available and product.stock > 0:
                subtotal = product.price * item['quantity']
                total += subtotal
                
                if not shop and product.shop:
                    shop = product.shop
                
                item_details = {
                    'product': product,
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                }
                cart_products.append(item_details)
        
        # Update cart total
        cart['total'] = total
        session.modified = True
    
    return render_template('user/cart.html', cart_products=cart_products, cart=cart, shop=shop)

@app.route('/user/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    if not product.is_available or product.stock <= 0:
        flash('Product is not available', 'warning')
        return redirect(url_for('view_shop', shop_id=product.shop_id))
    
    quantity = int(request.form.get('quantity', 1))
    if quantity > product.stock:
        quantity = product.stock
        flash(f'Only {product.stock} items available', 'warning')
    
    # Initialize cart in session if not exists
    if 'cart' not in session:
        session['cart'] = {'items': [], 'total': 0.0, 'shop_id': product.shop_id}
    
    # Check if cart has items from another shop
    if session['cart']['items'] and session['cart']['shop_id'] != product.shop_id:
        flash('You can only order from one shop at a time. Please clear your cart first.', 'warning')
        return redirect(url_for('view_shop', shop_id=product.shop_id))
    
    # Set shop_id if cart is empty
    session['cart']['shop_id'] = product.shop_id
    
    # Check if product already in cart
    cart_item = next((item for item in session['cart']['items'] if item['product_id'] == product.id), None)
    
    if cart_item:
        cart_item['quantity'] += quantity
    else:
        session['cart']['items'].append({
            'product_id': product.id,
            'product_name': product.name,
            'price': product.price,
            'quantity': quantity
        })
    
    # Recalculate total
    total = sum(item['price'] * item['quantity'] for item in session['cart']['items'])
    session['cart']['total'] = total
    
    # Save cart to session
    session.modified = True
    
    flash(f'Added {quantity} {product.name} to cart', 'success')
    return redirect(url_for('view_cart'))

@app.route('/user/cart/update/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 0))
    
    if 'cart' not in session or not session['cart']['items']:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('view_cart'))
    
    # Find product in cart
    for item in session['cart']['items']:
        if item['product_id'] == product_id:
            if quantity <= 0:
                session['cart']['items'].remove(item)
            else:
                if quantity > product.stock:
                    quantity = product.stock
                    flash(f'Only {product.stock} items available', 'warning')
                item['quantity'] = quantity
            break
    
    # Recalculate total
    if session['cart']['items']:
        total = sum(item['price'] * item['quantity'] for item in session['cart']['items'])
        session['cart']['total'] = total
    else:
        session['cart'] = {'items': [], 'total': 0.0}
    
    # Save cart to session
    session.modified = True
    
    flash('Cart updated', 'success')
    return redirect(url_for('view_cart'))

@app.route('/user/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    session['cart'] = {'items': [], 'total': 0.0}
    flash('Cart cleared', 'success')
    return redirect(url_for('view_cart'))

@app.route('/user/cart/sync', methods=['POST'])
@login_required
def sync_cart():
    try:
        # Get cart data from request
        cart_data = request.json
        
        # Validate cart data
        if not cart_data:
            cart_data = {'items': [], 'total': 0}
        
        if 'items' not in cart_data:
            cart_data['items'] = []
            
        # Update session cart
        session['cart'] = {
            'items': cart_data['items'],
            'total': cart_data.get('total', 0),
            'shop_id': cart_data.get('shopId')
        }
        session.modified = True
        
        logging.debug(f"Synced cart: {session['cart']}")
        
        return jsonify({'success': True, 'cart': session['cart']})
    except Exception as e:
        logging.error(f"Error syncing cart: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while syncing cart'})

@app.route('/user/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Ensure cart exists in session with default values
    if 'cart' not in session:
        session['cart'] = {'items': [], 'total': 0.0, 'shop_id': None}
    
    # Redirect if cart is empty
    if not session['cart']['items']:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('view_cart'))
        
    # Get product details for items in cart (for GET request)
    cart = session['cart']
    cart_products = []
    shop = None
    
    if request.method == 'GET':
        if cart['items']:
            for item in cart['items']:
                product = Product.query.get(item['product_id'])
                if product and product.is_available and product.stock > 0:
                    subtotal = product.price * item['quantity']
                    
                    if not shop and product.shop:
                        shop = product.shop
                    
                    item_details = {
                        'product': product,
                        'quantity': item['quantity'],
                        'subtotal': subtotal
                    }
                    cart_products.append(item_details)
        
        return render_template('user/checkout.html', cart_products=cart_products, cart=cart, shop=shop)
    
    if request.method == 'POST':
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        # Create order
        shop_id = session['cart']['shop_id']
        total_price = session['cart']['total']
        
        # Add current timestamp to help with sorting recent orders
        current_time = datetime.now()
        
        new_order = Order(
            user_id=current_user.id,
            shop_id=shop_id,
            total_price=total_price,
            status='pending',
            address=address,
            phone=phone,
            created_at=current_time,
            updated_at=current_time
        )
        db.session.add(new_order)
        db.session.flush()  # Get ID without committing
        
        # Create order items
        for item in session['cart']['items']:
            product = Product.query.get(item['product_id'])
            if product:
                # Create order item
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=item['quantity'],
                    price=product.price
                )
                db.session.add(order_item)
                
                # Update product stock
                product.stock -= item['quantity']
                if product.stock <= 0:
                    product.is_available = False
        
        db.session.commit()
        
        # Clear cart after successful order
        session['cart'] = {'items': [], 'total': 0.0}
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True, 
                'redirect': url_for('order_confirmation', order_id=new_order.id),
                'message': 'Order placed successfully!'
            })
        else:
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_confirmation', order_id=new_order.id))
    
    return render_template('user/checkout.html', cart=session['cart'])

@app.route('/user/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('user/order_confirmation.html', order=order)

# Shop Owner routes
@app.route('/shop_owner/dashboard')
@login_required
def shop_owner_dashboard():
    shops = Shop.query.filter_by(owner_id=current_user.id).all()
    return render_template('shop_owner/dashboard.html', shops=shops)

@app.route('/shop_owner/request', methods=['GET', 'POST'])
@login_required
def request_shop():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        new_shop = Shop(
            name=name,
            description=description,
            address=address,
            phone=phone,
            email=email,
            status='pending',
            owner_id=current_user.id
        )
        
        db.session.add(new_shop)
        db.session.commit()
        
        flash('Shop request submitted! Waiting for admin approval.', 'success')
        return redirect(url_for('shop_owner_dashboard'))
        
    return render_template('shop_owner/request_shop.html')

@app.route('/shop_owner/shop/<int:shop_id>')
@login_required
def shop_detail(shop_id):
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    products = Product.query.filter_by(shop_id=shop.id).all()
    return render_template('shop_owner/shop_detail.html', shop=shop, products=products)

@app.route('/shop_owner/shop/<int:shop_id>/products')
@login_required
def manage_products(shop_id):
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    
    # Only approved shops can manage products
    if shop.status != 'approved':
        flash('Your shop must be approved to manage products', 'warning')
        return redirect(url_for('shop_owner_dashboard'))
    
    products = Product.query.filter_by(shop_id=shop.id).all()
    return render_template('shop_owner/manage_products.html', shop=shop, products=products)

@app.route('/shop_owner/shop/<int:shop_id>/products/add', methods=['GET', 'POST'])
@login_required
def add_product(shop_id):
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    
    # Only approved shops can add products
    if shop.status != 'approved':
        flash('Your shop must be approved to add products', 'warning')
        return redirect(url_for('shop_owner_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        is_available = bool(request.form.get('is_available'))
        image_url = request.form.get('image_url')
        category = request.form.get('category')
        
        new_product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            is_available=is_available,
            shop_id=shop.id,
            image_url=image_url,
            category=category
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('manage_products', shop_id=shop.id))
    
    return render_template('shop_owner/manage_products.html', shop=shop)

@app.route('/shop_owner/shop/<int:shop_id>/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(shop_id, product_id):
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    product = Product.query.filter_by(id=product_id, shop_id=shop.id).first_or_404()
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.is_available = 'is_available' in request.form
        product.image_url = request.form.get('image_url')
        product.category = request.form.get('category')
        
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('manage_products', shop_id=shop.id))
    
    return render_template('shop_owner/manage_products.html', shop=shop, product=product)

@app.route('/shop_owner/shop/<int:shop_id>/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(shop_id, product_id):
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    product = Product.query.filter_by(id=product_id, shop_id=shop.id).first_or_404()
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('manage_products', shop_id=shop.id))

@app.route('/shop_owner/shop/<int:shop_id>/orders')
@login_required
def shop_orders(shop_id):
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    orders = Order.query.filter_by(shop_id=shop.id).order_by(Order.created_at.desc()).all()
    return render_template('shop_owner/orders.html', shop=shop, orders=orders)

@app.route('/shop_owner/shop/<int:shop_id>/orders/<int:order_id>')
@login_required
def shop_order_detail(shop_id, order_id):
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    order = Order.query.filter_by(id=order_id, shop_id=shop.id).first_or_404()
    return render_template('shop_owner/order_detail.html', shop=shop, order=order)

@app.route('/shop_owner/shop/<int:shop_id>/orders/<int:order_id>/update', methods=['POST'])
@login_required
def update_order_status(shop_id, order_id):
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first_or_404()
    order = Order.query.filter_by(id=order_id, shop_id=shop.id).first_or_404()
    
    # Get status and notes from form
    status = request.form.get('status')
    notes = request.form.get('notes')
    
    if status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        # Only update if status has changed
        if order.status != status:
            previous_status = order.status
            order.status = status
            
            # Record the timestamp of this status change
            order.updated_at = datetime.now()
            
            # Create a status update record in OrderStatusHistory
            status_update = OrderStatusHistory(
                order_id=order.id,
                previous_status=previous_status,
                new_status=status,
                notes=notes,
                updated_by=current_user.id,
                updated_at=datetime.now()
            )
            
            db.session.add(status_update)
            db.session.commit()
            
            # Create notification for the user
            flash(f'Order status updated successfully from {previous_status} to {status}!', 'success')
        else:
            flash('No change in status. Select a different status to update.', 'warning')
    else:
        flash('Invalid status selected.', 'danger')
    
    return redirect(url_for('shop_order_detail', shop_id=shop.id, order_id=order.id))

# Admin routes - redirection handled in routes_admin.py

@app.route('/admin/shops')
@login_required
def admin_shops():
    if not current_user.is_admin:
        abort(403)
    
    status = request.args.get('status')
    if status:
        shops = Shop.query.filter_by(status=status).all()
    else:
        shops = Shop.query.all()
    
    return render_template('admin/shops.html', shops=shops)

@app.route('/admin/shops/<int:shop_id>')
@login_required
def admin_shop_detail(shop_id):
    if not current_user.is_admin:
        abort(403)
    
    shop = Shop.query.get_or_404(shop_id)
    products = Product.query.filter_by(shop_id=shop.id).all()
    return render_template('admin/shop_detail.html', shop=shop, products=products)

@app.route('/admin/shops/<int:shop_id>/approve', methods=['POST'])
@login_required
def approve_shop(shop_id):
    if not current_user.is_admin:
        abort(403)
    
    shop = Shop.query.get_or_404(shop_id)
    shop.status = 'approved'
    db.session.commit()
    
    flash(f'Shop "{shop.name}" has been approved!', 'success')
    return redirect(url_for('admin_shops', status='pending'))

@app.route('/admin/shops/<int:shop_id>/reject', methods=['POST'])
@login_required
def reject_shop(shop_id):
    if not current_user.is_admin:
        abort(403)
    
    shop = Shop.query.get_or_404(shop_id)
    shop.status = 'rejected'
    db.session.commit()
    
    flash(f'Shop "{shop.name}" has been rejected!', 'warning')
    return redirect(url_for('admin_shops', status='pending'))

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        abort(403)
    
    status = request.args.get('status')
    if status:
        orders = Order.query.filter_by(status=status).order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders)

# API routes for AJAX requests
@app.route('/api/shops/search', methods=['GET'])
def search_shops_api():
    query = request.args.get('query', '').lower()
    status = request.args.get('status', 'approved')
    
    if status:
        shops = Shop.query.filter_by(status=status).all()
    else:
        shops = Shop.query.all()
    
    if query:
        shops = [shop for shop in shops if query.lower() in shop.name.lower() or 
                (shop.description and query.lower() in shop.description.lower())]
    
    return jsonify([{
        'id': shop.id,
        'name': shop.name,
        'description': shop.description,
        'status': shop.status,
        'owner': shop.owner.username
    } for shop in shops])

@app.route('/api/products/search', methods=['GET'])
def search_products_api():
    query = request.args.get('query', '').lower()
    shop_id = request.args.get('shop_id')
    
    products_query = Product.query
    if shop_id:
        products_query = products_query.filter_by(shop_id=shop_id)
    
    products = products_query.all()
    
    if query:
        products = [product for product in products if query.lower() in product.name.lower() or 
                   (product.description and query.lower() in product.description.lower())]
    
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'is_available': product.is_available,
        'shop_id': product.shop_id,
        'shop_name': product.shop.name
    } for product in products])

# Reviews routes - Shop Reviews
@app.route('/shop/<int:shop_id>/reviews')
def shop_reviews(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    reviews = ShopReview.query.filter_by(shop_id=shop_id).order_by(ShopReview.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating = db.session.query(func.avg(ShopReview.rating).label('average')).filter(ShopReview.shop_id == shop_id).scalar() or 0
    avg_rating = round(float(avg_rating), 1)
    
    # Check if user has already reviewed this shop
    user_review = None
    if current_user.is_authenticated:
        user_review = ShopReview.query.filter_by(shop_id=shop_id, user_id=current_user.id).first()
    
    return render_template('reviews/shop_reviews.html', shop=shop, reviews=reviews, 
                          avg_rating=avg_rating, user_review=user_review)

@app.route('/shop/<int:shop_id>/review', methods=['GET', 'POST'])
@login_required
def add_shop_review(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    
    # Check if user has already reviewed this shop
    existing_review = ShopReview.query.filter_by(shop_id=shop_id, user_id=current_user.id).first()
    
    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        comment = request.form.get('comment', '').strip()
        
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars', 'warning')
            return redirect(url_for('add_shop_review', shop_id=shop_id))
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.updated_at = datetime.now()
            flash('Your review has been updated', 'success')
        else:
            # Create new review
            new_review = ShopReview(
                shop_id=shop_id,
                user_id=current_user.id,
                rating=rating,
                comment=comment
            )
            db.session.add(new_review)
            flash('Your review has been added', 'success')
        
        db.session.commit()
        return redirect(url_for('shop_reviews', shop_id=shop_id))
    
    return render_template('reviews/add_shop_review.html', shop=shop, existing_review=existing_review)

@app.route('/shop/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_shop_review(review_id):
    review = ShopReview.query.get_or_404(review_id)
    
    # Check if this review belongs to the current user
    if review.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    shop_id = review.shop_id
    db.session.delete(review)
    db.session.commit()
    
    flash('Review has been deleted', 'success')
    return redirect(url_for('shop_reviews', shop_id=shop_id))

# Reviews routes - Product Reviews
@app.route('/product/<int:product_id>/reviews')
def product_reviews(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = ProductReview.query.filter_by(product_id=product_id).order_by(ProductReview.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating = db.session.query(func.avg(ProductReview.rating).label('average')).filter(ProductReview.product_id == product_id).scalar() or 0
    avg_rating = round(float(avg_rating), 1)
    
    # Check if user has already reviewed this product
    user_review = None
    if current_user.is_authenticated:
        user_review = ProductReview.query.filter_by(product_id=product_id, user_id=current_user.id).first()
    
    # Get user's orders that contain this product to verify purchase
    user_orders = []
    has_purchased = False
    if current_user.is_authenticated:
        user_orders_query = Order.query.join(OrderItem).filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == product_id,
            Order.status.in_(['delivered', 'completed'])
        ).all()
        user_orders = [order.id for order in user_orders_query]
        has_purchased = len(user_orders) > 0
    
    return render_template('reviews/product_reviews.html', product=product, reviews=reviews, 
                          avg_rating=avg_rating, user_review=user_review, 
                          user_orders=user_orders, has_purchased=has_purchased)

@app.route('/product/<int:product_id>/review', methods=['GET', 'POST'])
@login_required
def add_product_review(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if user has already reviewed this product
    existing_review = ProductReview.query.filter_by(product_id=product_id, user_id=current_user.id).first()
    
    # Get user's orders that contain this product
    user_orders = Order.query.join(OrderItem).filter(
        Order.user_id == current_user.id,
        OrderItem.product_id == product_id,
        Order.status.in_(['delivered', 'completed'])
    ).all()
    
    # Check if user has purchased the product (optional verification)
    has_purchased = len(user_orders) > 0
    
    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        comment = request.form.get('comment', '').strip()
        order_id = request.form.get('order_id')
        
        if order_id:
            order_id = int(order_id)
            # Verify the order belongs to the user and contains the product
            order_valid = any(order.id == order_id for order in user_orders)
            if not order_valid:
                order_id = None
        
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars', 'warning')
            return redirect(url_for('add_product_review', product_id=product_id))
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.comment = comment
            if order_id:
                existing_review.order_id = order_id
            existing_review.updated_at = datetime.now()
            flash('Your review has been updated', 'success')
        else:
            # Create new review
            new_review = ProductReview(
                product_id=product_id,
                user_id=current_user.id,
                order_id=order_id,
                rating=rating,
                comment=comment
            )
            db.session.add(new_review)
            flash('Your review has been added', 'success')
        
        db.session.commit()
        return redirect(url_for('product_reviews', product_id=product_id))
    
    return render_template('reviews/add_product_review.html', product=product, 
                          existing_review=existing_review, orders=user_orders, has_purchased=has_purchased)

@app.route('/product/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_product_review(review_id):
    review = ProductReview.query.get_or_404(review_id)
    
    # Check if this review belongs to the current user
    if review.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    product_id = review.product_id
    db.session.delete(review)
    db.session.commit()
    
    flash('Review has been deleted', 'success')
    return redirect(url_for('product_reviews', product_id=product_id))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500
