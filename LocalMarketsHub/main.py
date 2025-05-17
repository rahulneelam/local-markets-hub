from app import app, db
import routes  # This imports all routes
import routes_shop_owner  # This imports all shop owner routes
import routes_user  # This imports all user routes

# Configure database and create admin user
with app.app_context():
    # Import models here to avoid circular imports
    from models import User, Shop, Product, Order, OrderItem, WatchlistItem
    from order_status import OrderStatusHistory
    from user_data import UserData, ShopOwnerData
    
    # Create all tables
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username="RAHUL").first()
    if not admin:
        admin = User(username="RAHUL", email="admin@example.com", is_admin=True)
        admin.set_password("Rahul@123")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
