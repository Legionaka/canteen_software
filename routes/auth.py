from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User

auth_bp = Blueprint('auth', __name__)


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


@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')

    name = request.form.get('name', '').strip()
    student_number = request.form.get('student_number', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash('Please fill in all required fields.', 'error')
        return render_template('auth/register.html')

    if len(password) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return render_template('auth/register.html')

    user_exist = User.query.filter_by(email=email).first()
    if user_exist:
        flash('Email already registered.', 'error')
        return render_template('auth/register.html')

    user = User(name=name, student_number=student_number, email=email, role='student')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash('Registration successful. Please log in.', 'success')
    return redirect(url_for('auth.login'))
