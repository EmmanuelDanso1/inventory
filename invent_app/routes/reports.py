from flask import Blueprint, render_template, request
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.category import Category
from sqlalchemy import func

bp = Blueprint('reports', __name__)


@bp.route('/')
def index():
    """Reports landing page"""
    return redirect(url_for('main.dashboard'))


@bp.route('/stock-levels')
def stock_levels():
    """Current stock levels report"""
    category_id = request.args.get('category', type=int)
    
    query = db.session.query(Item)
    
    if category_id:
        query = query.filter(Item.category_id == category_id)
    
    items = query.order_by(Item.current_stock.asc()).all()
    categories = db.session.query(Category).order_by(Category.category_name).all()
    
    return render_template(
        'reports/stock_levels.html',
        items=items,
        categories=categories
    )


@bp.route('/low-stock')
def low_stock():
    """Low stock alert report"""
    items = db.session.query(Item)\
        .filter(Item.current_stock <= Item.reorder_level)\
        .order_by(Item.current_stock.asc())\
        .all()
    
    return render_template('reports/low_stock_alert.html', items=items)


@bp.route('/movement-history')
def movement_history():
    """Stock movement history"""
    page = request.args.get('page', 1, type=int)
    
    transactions = db.session.query(Transaction)\
        .order_by(Transaction.transaction_date.desc())\
        .paginate(page=page, per_page=50, error_out=False)
    
    return render_template('reports/movement_history.html', transactions=transactions)


@bp.route('/performance')
def performance():
    """Database performance comparison"""
    # This will show normalized vs denormalized performance metrics
    return render_template('reports/performance.html')
