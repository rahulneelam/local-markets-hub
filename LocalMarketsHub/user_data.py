from datetime import datetime
import json
from app import db

# User data storage (separate from shop owner data)
class UserData(db.Model):
    __tablename__ = 'user_data'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    preferences = db.Column(db.Text, nullable=True)  # User preferences in JSON format
    saved_addresses = db.Column(db.Text, nullable=True)  # Saved addresses for delivery
    payment_info = db.Column(db.Text, nullable=True)  # Stored payment information (securely encrypted)
    viewed_products = db.Column(db.Text, nullable=True)  # Recently viewed products
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('data', uselist=False))
    
    def get_preferences(self):
        if self.preferences:
            return json.loads(self.preferences)
        return {}
    
    def set_preferences(self, preferences_dict):
        self.preferences = json.dumps(preferences_dict)
        
    def get_saved_addresses(self):
        if self.saved_addresses:
            return json.loads(self.saved_addresses)
        return []
    
    def set_saved_addresses(self, addresses_list):
        self.saved_addresses = json.dumps(addresses_list)
        
    def get_viewed_products(self):
        if self.viewed_products:
            return json.loads(self.viewed_products)
        return []
    
    def add_viewed_product(self, product_id):
        products = self.get_viewed_products()
        if product_id in products:
            products.remove(product_id)
        products.insert(0, product_id)
        # Keep only the 20 most recent products
        self.viewed_products = json.dumps(products[:20])
    
    def __repr__(self):
        return f'<UserData {self.id}>'

# Shop owner data storage (separate from user data)
class ShopOwnerData(db.Model):
    __tablename__ = 'shop_owner_data'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    business_info = db.Column(db.Text, nullable=True)  # Business information
    bank_details = db.Column(db.Text, nullable=True)  # Banking information for payments
    tax_info = db.Column(db.Text, nullable=True)  # Tax information
    settings = db.Column(db.Text, nullable=True)  # Shop settings
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('shop_data', uselist=False))
    
    def get_business_info(self):
        if self.business_info:
            return json.loads(self.business_info)
        return {}
    
    def set_business_info(self, info_dict):
        self.business_info = json.dumps(info_dict)
    
    def get_settings(self):
        if self.settings:
            return json.loads(self.settings)
        return {}
    
    def set_settings(self, settings_dict):
        self.settings = json.dumps(settings_dict)
    
    def __repr__(self):
        return f'<ShopOwnerData {self.id}>'