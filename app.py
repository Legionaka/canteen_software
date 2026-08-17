from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from models import db, User
from routes.student import student_bp
from routes.staff import staff_bp
from routes.admin import admin_bp
from routes.auth import auth_bp
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
    app = Flask(__name__,static_folder='static', static_url_path='/static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 1800
    }

    db.init_app(app)

    app.register_blueprint(student_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_user():
        user_id = session.get('user_id')
        current_user_name = None
        current_role = None
        if user_id:
            user = User.query.get(user_id)
            if user:
                current_user_name = user.name
                current_role = user.role
        return dict(current_user_name=current_user_name, current_role=current_role)

    @app.route('/')
    def index():
        role = session.get('role')
        if role == 'student':
            return redirect(url_for('student.menu'))
        if role == 'staff':
            return redirect(url_for('staff.dashboard'))
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.login'))

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
