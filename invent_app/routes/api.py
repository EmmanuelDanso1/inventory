from flask import Blueprint, jsonify, request
from invent_app import db
from invent_app.models.normalized.item import Item

bp = Blueprint('api', __name__)


@bp.route('/items')
def get_items():
    """Get items as JSON"""
    items = db.session.query(Item).all()
    
    return jsonify([{
        'item_id': item.item_id,
        'item_code': item.item_code,
        'item_name': item.item_name,
        'current_stock': item.current_stock,
        'unit_price': float(item.unit_price)
    } for item in items])


@bp.route('/items/<int:id>')
def get_item(id):
    """Get single item as JSON"""
    item = db.session.get(Item, id)
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    return jsonify({
        'item_id': item.item_id,
        'item_code': item.item_code,
        'item_name': item.item_name,
        'description': item.description,
        'category': item.category.category_name,
        'current_stock': item.current_stock,
        'unit_price': float(item.unit_price),
        'reorder_level': item.reorder_level
    })


@bp.route('/stats')
def get_stats():
    """Get dashboard statistics as JSON"""
    total_items = db.session.query(Item).count()
    low_stock = db.session.query(Item).filter(
        Item.current_stock <= Item.reorder_level
    ).count()
    
    return jsonify({
        'total_items': total_items,
        'low_stock_items': low_stock
    })