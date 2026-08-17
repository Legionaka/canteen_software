from datetime import datetime, date
from models import db, User, MenuItem, Promotion, Order, OrderItem, LoyaltyPoints
from flask import Flask
import os
from dotenv import load_dotenv

import random
import string


def seed_data(app):
    with app.app_context():
        db.create_all()  # 6 tables are created

        # Clear existing data (optional, for development)
        db.session.query(LoyaltyPoints).delete()
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.query(Promotion).delete()
        db.session.query(MenuItem).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Users
        user_legion = User(name="Legion C", email="legion@campus.ac.za", student_number="STU2024001", role="student")
        user_legion.set_password("password123")
        user_staff = User(name="Staff User", email="staff@campus.ac.za", role="staff")
        user_staff.set_password("password123")
        user_admin = User(name="Admin User", email="admin@campus.ac.za", role="admin")
        user_admin.set_password("password123")
        db.session.add_all([user_legion, user_staff, user_admin])
        db.session.commit()

        # Menu Items
        menu_items_data = [
            {"name": "Beef Bunny Chow", "description": "Durban-style curry in a quarter loaf", "price": 38.0, "category": "mains", "emoji": "🍞", "dietary": "none", "is_available": True},
            {"name": "Grilled Chicken Wrap", "description": "Halal chicken with fresh salad", "price": 42.0, "category": "mains", "emoji": "🌯", "dietary": "halal", "is_available": True},
            {"name": "Veggie Burger", "description": "Plant-based patty and chips", "price": 35.0, "category": "mains", "emoji": "🍔", "dietary": "vegetarian", "is_available": True},
            {"name": "Pap & Chakalaka", "description": "Traditional maize pap with spicy relish", "price": 28.0, "category": "mains", "emoji": "🥘", "dietary": "vegetarian", "is_available": True},
            {"name": "Boerewors Roll", "description": "South African sausage in a fresh roll", "price": 30.0, "category": "snacks", "emoji": "🌭", "dietary": "none", "is_available": True},
            {"name": "Samoosa x2", "description": "Crispy pastry with spiced filling", "price": 15.0, "category": "snacks", "emoji": "🥟", "dietary": "halal", "is_available": True},
            {"name": "Fruit Cup", "description": "Seasonal fresh fruit", "price": 22.0, "category": "snacks", "emoji": "🍇", "dietary": "vegetarian", "is_available": True},
            {"name": "Cheese Toastie", "description": "Toasted cheese sandwich", "price": 20.0, "category": "snacks", "emoji": "🥪", "dietary": "vegetarian", "is_available": False},
            {"name": "Rooibos Tea", "description": "South African red bush tea", "price": 12.0, "category": "drinks", "emoji": "🍵", "dietary": "vegetarian", "is_available": True},
            {"name": "Coke 330ml", "description": "Chilled canned soft drink", "price": 14.0, "category": "drinks", "emoji": "🥤", "dietary": "none", "is_available": True},
            {"name": "Jungle Oats", "description": "Warm oats with honey", "price": 18.0, "category": "breakfast", "emoji": "🥣", "dietary": "vegetarian", "is_available": True},
            {"name": "Egg & Bacon Roll", "description": "Breakfast roll with egg and bacon", "price": 25.0, "category": "breakfast", "emoji": "🥓", "dietary": "none", "is_available": True},
        ]
        menu_items = []
        for item_data in menu_items_data:
            menu_items.append(MenuItem(**item_data))
        db.session.add_all(menu_items)
        db.session.commit()

        # Promotions
        promo_daily_special = Promotion(name="Daily Special: Bunny Chow + Coke", type="flat", discount_value=9.00)
        promo_loyalty = Promotion(name="10th Meal Free", type="loyalty", discount_value=30.00)
        db.session.add_all([promo_daily_special, promo_loyalty])
        db.session.commit()

        # Orders
        # Order 1: New
        order_new = Order(user_id=user_legion.id, pickup_slot="12:00", subtotal=38.0+14.0, service_fee=2.0, total=38.0+14.0+2.0-9.0, status="new", promo_id=promo_daily_special.id)
        db.session.add(order_new)
        db.session.commit()
        db.session.add(OrderItem(order_id=order_new.id, menu_item_id=next(item.id for item in menu_items if item.name == "Beef Bunny Chow"), quantity=1, unit_price=38.0))
        db.session.add(OrderItem(order_id=order_new.id, menu_item_id=next(item.id for item in menu_items if item.name == "Coke 330ml"), quantity=1, unit_price=14.0))
        db.session.commit()

        # Order 2: Preparing
        order_preparing = Order(user_id=user_legion.id, pickup_slot="12:30", subtotal=42.0, service_fee=2.0, total=42.0+2.0, status="preparing")
        db.session.add(order_preparing)
        db.session.commit()
        db.session.add(OrderItem(order_id=order_preparing.id, menu_item_id=next(item.id for item in menu_items if item.name == "Grilled Chicken Wrap"), quantity=1, unit_price=42.0))
        db.session.commit()

        # Order 3: Collected (with loyalty points)
        order_collected = Order(user_id=user_legion.id, pickup_slot="13:00", subtotal=35.0, service_fee=2.0, total=35.0+2.0, status="collected")
        db.session.add(order_collected)
        db.session.commit()
        db.session.add(OrderItem(order_id=order_collected.id, menu_item_id=next(item.id for item in menu_items if item.name == "Veggie Burger"), quantity=1, unit_price=35.0))
        db.session.commit()

        loyalty_record = LoyaltyPoints(user_id=user_legion.id, order_id=order_collected.id, points_earned=1, points_balance=1)
        db.session.add(loyalty_record)
        db.session.commit()

        print("Database seeded successfully!")


if __name__ == '__main__':
    load_dotenv()
    app = Flask(__name__)
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    db.init_app(app)
    seed_data(app)
