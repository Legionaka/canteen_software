from flask import Blueprint, render_template, request, redirect, url_for , session, flash
from models import db, User

auth_bp = Blueprint('auth', __name__)

from flask import render_template, request, flash, redirect, url_for, session

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')

    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        flash("Invalid email or password.", "error")
        return render_template('auth/login.html'), 401
    
    session.clear()
    session['user_id'] = user.id
    session['role'] = user.role

    role_redirects = {
        'student': 'student.menu',
        'staff': 'staff.dashboard',
        'admin': 'admin.dashboard'
    }

    target_route = role_redirects.get(user.role)
    
    if target_route:
        return redirect(url_for(target_route))
    
    flash("Account configuration error. Please contact support.", "warning")
    return redirect(url_for('auth.login'))


    