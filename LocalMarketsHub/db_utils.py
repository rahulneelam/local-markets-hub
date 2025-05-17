from replit import db

def initialize_db():
    """Initialize the Replit DB with required collections if they don't exist"""
    if 'users' not in db:
        db['users'] = {}
    
    if 'shops' not in db:
        db['shops'] = {}
    
    if 'orders' not in db:
        db['orders'] = {}

def clear_db():
    """Clear all data from the database (for development/testing)"""
    keys = list(db.keys())
    for key in keys:
        del db[key]
    initialize_db()

def get_db_stats():
    """Get stats about the database"""
    return {
        'users_count': len(db.get('users', {})),
        'shops_count': len(db.get('shops', {})),
        'orders_count': len(db.get('orders', {})),
        'pending_shops': len([s for s in db.get('shops', {}).values() if s.get('status') == 'pending']),
        'approved_shops': len([s for s in db.get('shops', {}).values() if s.get('status') == 'approved'])
    }
