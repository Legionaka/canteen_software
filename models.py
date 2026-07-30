from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String, nullable=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default='student') # 'student', 'staff', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    orders = relationship('Order', backref='user', lazy=True)
    loyalty_records = relationship('LoyaltyPoints', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def loyalty_balance(self):
        return sum(lp.points_earned for lp in self.loyalty_records) # Simplified, should be running total

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String, nullable=False) # 'mains', 'snacks', 'drinks', 'breakfast'
    emoji = db.Column(db.String, nullable=True)
    dietary = db.Column(db.String, nullable=False, default='none') # 'none', 'vegetarian', 'halal', 'vegan'
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # order_items = relationship('OrderItem', backref='back_populates', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'emoji': self.emoji,
            'dietary': self.dietary,
            'is_available': self.is_available
        }

class Promotion(db.Model):
    __tablename__ = 'promotions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False) # 'flat', 'percent', 'loyalty'
    discount_value = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    valid_from = db.Column(db.Date, nullable=True)
    valid_until = db.Column(db.Date, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    orders = relationship('Order', backref='promotion', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    promo_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=True)
    status = db.Column(db.String, nullable=False, default='new') # 'new', 'preparing', 'ready', 'collected'
    pickup_slot = db.Column(db.String, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    service_fee = db.Column(db.Float, default=2.0)
    total = db.Column(db.Float, nullable=False)
    pickup_code = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)
    loyalty_record = relationship('LoyaltyPoints', backref='order', uselist=False, lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.pickup_code:
            self.pickup_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'promo_id': self.promo_id,
            'status': self.status,
            'pickup_slot': self.pickup_slot,
            'subtotal': self.subtotal,
            'service_fee': self.service_fee,
            'total': self.total,
            'pickup_code': self.pickup_code,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    menu_item = relationship('MenuItem')

    menu_item = relationship('MenuItem', backref=backref('order_items', lazy=True))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'menu_item_id': self.menu_item_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'menu_item_name': self.menu_item.name if self.menu_item else None # Assuming menu_item relationship exists
        }

class LoyaltyPoints(db.Model):
    __tablename__ = 'loyalty_points'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    points_earned = db.Column(db.Integer, default=1)
    points_balance = db.Column(db.Integer, nullable=False) # Running total
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
