from datetime import datetime
from app import db

# Order status history model - for tracking order status changes
class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    previous_status = db.Column(db.String(20), nullable=False)
    new_status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    order = db.relationship('Order', backref=db.backref('status_history', lazy='dynamic'))
    updater = db.relationship('User', backref=db.backref('status_updates', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'notes': self.notes,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updater_name': self.updater.username
        }
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.id}>'