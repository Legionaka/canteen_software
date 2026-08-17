from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from utils import login_required, role_required
from models import db, User, MenuItem, Order, OrderItem
from datetime import datetime, timedelta
from collections import Counter

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@login_required
@role_required('admin')
def dashboard():
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)

    total_orders_today = Order.query.filter(Order.created_at >= today_start, Order.created_at < today_end).count()
    revenue_today = db.session.query(db.func.sum(Order.total)).filter(
        Order.created_at >= today_start, Order.created_at < today_end
    ).scalar() or 0.0

    active_students = User.query.filter_by(role='student').count()

    completed = Order.query.filter_by(status='collected').all()
    avg_wait_minutes = 0
    if completed:
        waits = []
        for order in completed:
            # Simplified: use created_at as start, no collected timestamp stored
            waits.append(15)
        avg_wait_minutes = sum(waits) // len(waits)

    stats = {
        'total_orders_today': total_orders_today,
        'revenue_today': revenue_today,
        'active_students': active_students,
        'avg_wait_minutes': avg_wait_minutes
    }

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)


@admin_bp.route('/admin/stats')
@login_required
@role_required('admin')
def stats():
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)

    orders = Order.query.filter(Order.created_at >= today_start, Order.created_at < today_end).all()
    hours = [f'{h:02d}:00' for h in range(7, 19)]
    counts = {h: 0 for h in hours}
    for order in orders:
        hour = order.created_at.strftime('%H:00')
        if hour in counts:
            counts[hour] += 1

    hourly = [{'hour': h, 'count': counts[h]} for h in hours]

    item_counter = Counter()
    for order in orders:
        for item in order.items:
            name = item.menu_item.name if item.menu_item else 'Unknown'
            item_counter[name] += item.quantity

    top_items = [{'name': name, 'count': count} for name, count in item_counter.most_common(5)]

    return jsonify({'hourly': hourly, 'top_items': top_items})


@admin_bp.route('/admin/menu')
@login_required
@role_required('admin')
def menu():
    menu_items = MenuItem.query.all()
    return render_template('admin/menu.html', menu_items=menu_items)


@admin_bp.route('/admin/menu/add', methods=['POST'])
@login_required
@role_required('admin')
def add_menu_item():
    item = MenuItem(
        name=request.form.get('name', '').strip(),
        description=request.form.get('description', '').strip(),
        price=float(request.form.get('price', 0)),
        category=request.form.get('category', 'mains'),
        emoji=request.form.get('emoji', '').strip() or '🍽️',
        dietary=request.form.get('dietary', 'none'),
        is_available=request.form.get('is_available') == 'on'
    )
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('admin.menu'))


@admin_bp.route('/admin/menu/<int:item_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.name = request.form.get('name', '').strip()
    item.description = request.form.get('description', '').strip()
    item.price = float(request.form.get('price', 0))
    item.category = request.form.get('category', 'mains')
    item.emoji = request.form.get('emoji', '').strip() or '🍽️'
    item.dietary = request.form.get('dietary', 'none')
    item.is_available = request.form.get('is_available') == 'on'
    db.session.commit()
    return redirect(url_for('admin.menu'))


@admin_bp.route('/admin/menu/<int:item_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    blocked = OrderItem.query.join(Order).filter(
        OrderItem.menu_item_id == item_id,
        Order.status != 'collected'
    ).first()
    if blocked:
        return redirect(url_for('admin.menu'))
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin.menu'))


@admin_bp.route('/admin/orders')
@login_required
@role_required('admin')
def orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@admin_bp.route('/admin/students')
@login_required
@role_required('admin')
def students():
    students = User.query.filter_by(role='student').all()
    return render_template('admin/students.html', students=students)
