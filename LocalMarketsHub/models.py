from datetime import datetime
import json

from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    profile_image_url = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    shops = db.relationship('Shop', backref='owner', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    watchlist = db.relationship('WatchlistItem', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_shop_owner(self):
        return self.shops.count() > 0
    
    @staticmethod
    def get_admin():
        return User.query.filter_by(is_admin=True).first()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'profile_image_url': self.profile_image_url,
            'is_shop_owner': self.is_shop_owner(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

# Shop model
class Shop(db.Model):
    __tablename__ = 'shops'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(256), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    image_url = db.Column(db.String(256), nullable=True)
    categories = db.Column(db.String(256), nullable=True)  # Comma-separated list of categories
    latitude = db.Column(db.Float, nullable=True)  # For Google Maps location
    longitude = db.Column(db.Float, nullable=True)  # For Google Maps location
    show_map = db.Column(db.Boolean, default=False)  # Option to show/hide map

    # Relationships
    products = db.relationship('Product', backref='shop', lazy='dynamic', 
                             cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='shop', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner_username': self.owner.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Shop {self.name}>'

# Product model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    is_available = db.Column(db.Boolean, default=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    image_url = db.Column(db.String(256), nullable=True)
    category = db.Column(db.String(64), nullable=True)

    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    watchlist_items = db.relationship('WatchlistItem', backref='product', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'is_available': self.is_available,
            'shop_id': self.shop_id,
            'shop_name': self.shop.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'image_url': self.image_url,
            'category': self.category
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'

# Order model
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, delivered, cancelled
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    address = db.Column(db.String(256), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic',
                           cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'shop_id': self.shop_id,
            'user_name': self.user.username,
            'shop_name': self.shop.name,
            'status': self.status,
            'total_price': self.total_price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'address': self.address,
            'phone': self.phone,
            'items': [item.to_dict() for item in self.items]
        }
    
    def __repr__(self):
        return f'<Order {self.id}>'

# Order item model
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of purchase

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'quantity': self.quantity,
            'price': self.price,
            'subtotal': self.price * self.quantity
        }
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'

# Watchlist item model
class WatchlistItem(db.Model):
    __tablename__ = 'watchlist_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'product_price': self.product.price,
            'product_shop': self.product.shop.name,
            'product_image': self.product.image_url,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }
    
    def __repr__(self):
        return f'<WatchlistItem {self.id}>'

# Shop review model
class ShopReview(db.Model):
    __tablename__ = 'shop_reviews'
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    shop = db.relationship('Shop', backref=db.backref('reviews', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('shop_reviews', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_name': self.user.username,
            'shop_name': self.shop.name
        }
    
    def __repr__(self):
        return f'<ShopReview {self.id}>'

# Product review model
class ProductReview(db.Model):
    __tablename__ = 'product_reviews'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)  # Optional, link to the order where product was purchased
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    product = db.relationship('Product', backref=db.backref('reviews', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('product_reviews', lazy='dynamic'))
    order = db.relationship('Order', backref=db.backref('reviews', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_name': self.user.username,
            'product_name': self.product.name
        }
    
    def __repr__(self):
        return f'<ProductReview {self.id}>'