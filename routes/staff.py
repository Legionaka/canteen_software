from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from utils import login_required, role_required
from models import db, MenuItem, Order, LoyaltyPoints

staff_bp = Blueprint('staff', __name__)


def _active_orders():
    return Order.query.filter(Order.status.in_(['new', 'preparing', 'ready'])).all()


@staff_bp.route('/staff')
@login_required
@role_required('staff')
def dashboard():
    new_orders = [o.to_dict() for o in Order.query.filter_by(status='new').all()]
    preparing_orders = [o.to_dict() for o in Order.query.filter_by(status='preparing').all()]
    ready_orders = [o.to_dict() for o in Order.query.filter_by(status='ready').all()]
    menu_items = MenuItem.query.all()
    return render_template(
        'staff/dashboard.html',
        new_orders=new_orders,
        preparing_orders=preparing_orders,
        ready_orders=ready_orders,
        menu_items=menu_items
    )


@staff_bp.route('/staff/order/<int:order_id>/status', methods=['POST'])
@login_required
@role_required('staff')
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('new_status')
    valid_progression = {
        'new': 'preparing',
        'preparing': 'ready',
        'ready': 'collected'
    }
    if new_status in valid_progression.values() and valid_progression.get(order.status) == new_status:
        order.status = new_status
        db.session.commit()

        if new_status == 'collected':
            last = LoyaltyPoints.query.filter_by(user_id=order.user_id).order_by(LoyaltyPoints.awarded_at.desc()).first()
            previous_balance = last.points_balance if last else 0
            record = LoyaltyPoints(
                user_id=order.user_id,
                order_id=order.id,
                points_earned=1,
                points_balance=previous_balance + 1
            )
            db.session.add(record)
            db.session.commit()

    return redirect(url_for('staff.dashboard'))


@staff_bp.route('/staff/menu/<int:item_id>/toggle', methods=['POST'])
@login_required
@role_required('staff')
def toggle_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    return redirect(url_for('staff.dashboard'))


@staff_bp.route('/staff/orders/live')
@login_required
@role_required('staff')
def live_orders():
    orders = [o.to_dict() for o in _active_orders()]
    return jsonify(orders)
