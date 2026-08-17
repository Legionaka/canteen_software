from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from utils import login_required, role_required
from models import db, MenuItem, Order, OrderItem

student_bp = Blueprint('student', __name__)


@student_bp.route('/menu')
@login_required
@role_required('student')
def menu():
    items = [item.to_dict() for item in MenuItem.query.all()]
    return render_template('student/menu.html', items=items)


@student_bp.route('/order', methods=['POST'])
@login_required
@role_required('student')
def create_order():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    cart = data.get('cart', [])
    pickup_slot = data.get('pickup_slot', '12:00')

    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400

    order_items = []
    subtotal = 0.0
    for line in cart:
        menu_item_id = line.get('menu_item_id')
        quantity = int(line.get('quantity', 1))
        menu_item = MenuItem.query.get(menu_item_id)

        if not menu_item:
            return jsonify({'error': f'Menu item {menu_item_id} not found'}), 400
        if not menu_item.is_available:
            return jsonify({'error': f'{menu_item.name} is sold out'}), 400
        if quantity < 1:
            return jsonify({'error': 'Quantity must be at least 1'}), 400

        unit_price = menu_item.price
        order_items.append({
            'menu_item_id': menu_item.id,
            'quantity': quantity,
            'unit_price': unit_price
        })
        subtotal += unit_price * quantity

    service_fee = 2.0
    total = subtotal + service_fee

    order = Order(
        user_id=session['user_id'],
        pickup_slot=pickup_slot,
        subtotal=subtotal,
        service_fee=service_fee,
        total=total
    )
    db.session.add(order)
    db.session.commit()

    for item in order_items:
        db.session.add(OrderItem(
            order_id=order.id,
            menu_item_id=item['menu_item_id'],
            quantity=item['quantity'],
            unit_price=item['unit_price']
        ))
    db.session.commit()

    return jsonify({'order_id': order.id})


@student_bp.route('/order/<int:order_id>/track')
@login_required
@role_required('student')
def track(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        return redirect(url_for('student.menu'))
    return render_template('student/track.html', order=order.to_dict())


@student_bp.route('/order/<int:order_id>/status')
@login_required
@role_required('student')
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({'status': order.status})
