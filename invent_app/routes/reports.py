from flask import Blueprint, render_template, request, redirect, url_for
from invent_app import db
from invent_app.models.normalized import Transaction, TransactionType
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.category import Category
from sqlalchemy import func

bp = Blueprint('reports', __name__)


@bp.route('/')
def index():
    """Reports landing page - redirect to dashboard"""
    return redirect(url_for('main.dashboard'))


# REPORT 1: STOCK LEVELS REPORT
@bp.route('/stock-levels')
def stock_levels():
    """
    Current stock levels report
    Shows all items with their current quantities, values, and status
    """
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    
    # Base query
    query = db.session.query(Item)
    
    # Apply category filter if provided
    if category_id:
        query = query.filter(Item.category_id == category_id)
    
    # Get all items, ordered by stock level (lowest first)
    items = query.order_by(Item.current_stock.asc()).all()
    
    # Get all categories for filter dropdown
    categories = db.session.query(Category).order_by(Category.category_name).all()
    
    # Calculate summary statistics
    total_items = len(items)
    total_value = sum(float(item.current_stock * item.unit_price) for item in items)
    low_stock_count = sum(1 for item in items if item.is_low_stock and not item.is_out_of_stock)
    out_of_stock_count = sum(1 for item in items if item.is_out_of_stock)
    
    return render_template(
        'reports/stock_levels.html',
        items=items,
        categories=categories,
        total_items=total_items,
        total_value=total_value,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count
    )


# REPORT 2: LOW STOCK ALERT
@bp.route('/low-stock')
def low_stock():
    """
    Low stock alert report
    Shows items at or below reorder level that need attention
    """
    # Get items below or at reorder level
    items = db.session.query(Item)\
        .filter(Item.current_stock <= Item.reorder_level)\
        .order_by(Item.current_stock.asc())\
        .all()
    
    # Separate by priority
    critical_items = [item for item in items if item.is_out_of_stock]
    low_items = [item for item in items if not item.is_out_of_stock]
    
    return render_template(
        'reports/low_stock_alert.html',
        items=items,
        critical_items=critical_items,
        low_items=low_items
    )


# REPORT 3: MOVEMENT HISTORY
@bp.route('/movement-history')
def movement_history():
    """
    Stock movement history report
    Shows all transactions with filters for date range and type
    """
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    transaction_type = request.args.get('type')
    
    # Base query
    query = db.session.query(Transaction)
    
    # Apply filters
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Transaction.transaction_date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Add one day to include the end date
            end = end + timedelta(days=1)
            query = query.filter(Transaction.transaction_date < end)
        except ValueError:
            pass
    
    if transaction_type:
        query = query.join(Transaction.transaction_type)\
            .filter(TransactionType.type_name == transaction_type)
    
    # Paginate results
    transactions = query.order_by(Transaction.transaction_date.desc())\
        .paginate(page=page, per_page=50, error_out=False)
    
    # Calculate totals for current filter
    total_stock_in = db.session.query(func.sum(Transaction.quantity))\
        .join(Transaction.transaction_type)\
        .filter(TransactionType.type_name == 'STOCK_IN')
    
    total_stock_out = db.session.query(func.sum(Transaction.quantity))\
        .join(Transaction.transaction_type)\
        .filter(TransactionType.type_name == 'STOCK_OUT')
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        total_stock_in = total_stock_in.filter(Transaction.transaction_date >= start)
        total_stock_out = total_stock_out.filter(Transaction.transaction_date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        total_stock_in = total_stock_in.filter(Transaction.transaction_date < end)
        total_stock_out = total_stock_out.filter(Transaction.transaction_date < end)
    
    stock_in_total = total_stock_in.scalar() or 0
    stock_out_total = total_stock_out.scalar() or 0
    
    return render_template(
        'reports/movement_history.html',
        transactions=transactions,
        stock_in_total=stock_in_total,
        stock_out_total=stock_out_total
    )


# REPORT 4: CATEGORY SUMMARY
@bp.route('/category-summary')
def category_summary():
    """
    Summary report by category
    Shows inventory distribution across categories
    """
    # Get all categories with item counts and values
    categories_data = db.session.query(
        Category.category_name,
        func.count(Item.item_id).label('item_count'),
        func.sum(Item.current_stock).label('total_stock'),
        func.sum(Item.current_stock * Item.unit_price).label('total_value')
    ).outerjoin(Item, Category.category_id == Item.category_id)\
     .group_by(Category.category_id, Category.category_name)\
     .all()
    
    # Calculate totals
    grand_total_items = sum(c.item_count for c in categories_data)
    grand_total_stock = sum(c.total_stock or 0 for c in categories_data)
    grand_total_value = sum(float(c.total_value or 0) for c in categories_data)
    
    return render_template(
        'reports/category_summary.html',
        categories_data=categories_data,
        grand_total_items=grand_total_items,
        grand_total_stock=grand_total_stock,
        grand_total_value=grand_total_value
    )


# REPORT 5: SUPPLIER PERFORMANCE
@bp.route('/supplier-performance')
def supplier_performance():
    """
    Supplier performance report
    Shows transaction counts and values per supplier
    """
    # Get supplier statistics
    supplier_stats = db.session.query(
        Supplier.supplier_name,
        func.count(Transaction.transaction_id).label('transaction_count'),
        func.sum(Transaction.quantity).label('total_quantity'),
        func.sum(Transaction.quantity * Transaction.unit_price).label('total_value'),
        func.count(Item.item_id.distinct()).label('items_supplied')
    ).outerjoin(Item, Supplier.supplier_id == Item.supplier_id)\
     .outerjoin(Transaction, and_(
         Transaction.supplier_id == Supplier.supplier_id,
         Transaction.transaction_type.has(type_name='STOCK_IN')
     ))\
     .group_by(Supplier.supplier_id, Supplier.supplier_name)\
     .all()
    
    return render_template(
        'reports/supplier_performance.html',
        supplier_stats=supplier_stats
    )


# REPORT 6: INVENTORY VALUATION
@bp.route('/inventory-valuation')
def inventory_valuation():
    """
    Inventory valuation report
    Shows total inventory value broken down by various dimensions
    """
    # Total inventory value
    total_value = db.session.query(
        func.sum(Item.current_stock * Item.unit_price)
    ).scalar() or 0
    
    # Value by category
    category_values = db.session.query(
        Category.category_name,
        func.sum(Item.current_stock * Item.unit_price).label('value')
    ).join(Item, Category.category_id == Item.category_id)\
     .group_by(Category.category_id, Category.category_name)\
     .order_by(func.sum(Item.current_stock * Item.unit_price).desc())\
     .all()
    
    # Top 10 most valuable items
    top_items = db.session.query(
        Item.item_name,
        Item.current_stock,
        Item.unit_price,
        (Item.current_stock * Item.unit_price).label('total_value')
    ).order_by((Item.current_stock * Item.unit_price).desc())\
     .limit(10)\
     .all()
    
    return render_template(
        'reports/inventory_valuation.html',
        total_value=float(total_value),
        category_values=category_values,
        top_items=top_items
    )


# REPORT 7: MONTHLY SUMMARY
@bp.route('/monthly-summary')
def monthly_summary():
    """
    Monthly summary report
    Shows key metrics for the current month
    """
    # Get current month date range
    today = datetime.now()
    first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1)
    
    # Transactions this month
    monthly_transactions = db.session.query(Transaction)\
        .filter(Transaction.transaction_date >= first_day)\
        .filter(Transaction.transaction_date < last_day)\
        .count()
    
    # Stock in this month
    stock_in_count = db.session.query(func.sum(Transaction.quantity))\
        .join(Transaction.transaction_type)\
        .filter(TransactionType.type_name == 'STOCK_IN')\
        .filter(Transaction.transaction_date >= first_day)\
        .filter(Transaction.transaction_date < last_day)\
        .scalar() or 0
    
    # Stock out this month
    stock_out_count = db.session.query(func.sum(Transaction.quantity))\
        .join(Transaction.transaction_type)\
        .filter(TransactionType.type_name == 'STOCK_OUT')\
        .filter(Transaction.transaction_date >= first_day)\
        .filter(Transaction.transaction_date < last_day)\
        .scalar() or 0
    
    # Most active items this month
    active_items = db.session.query(
        Item.item_name,
        func.count(Transaction.transaction_id).label('transaction_count')
    ).join(Transaction, Item.item_id == Transaction.item_id)\
     .filter(Transaction.transaction_date >= first_day)\
     .filter(Transaction.transaction_date < last_day)\
     .group_by(Item.item_id, Item.item_name)\
     .order_by(func.count(Transaction.transaction_id).desc())\
     .limit(10)\
     .all()
    
    return render_template(
        'reports/monthly_summary.html',
        month_name=first_day.strftime('%B %Y'),
        monthly_transactions=monthly_transactions,
        stock_in_count=stock_in_count,
        stock_out_count=stock_out_count,
        active_items=active_items
    )


# REPORT 8: PERFORMANCE COMPARISON (For Research)
@bp.route('/performance')
def performance():
    """
    Database performance comparison report
    Compares normalized vs denormalized schema performance
    """
    return render_template('reports/performance.html')


# API ENDPOINT: Export Report Data
@bp.route('/export/<report_type>')
def export_report(report_type):
    """
    Export report data as JSON
    Used by frontend for CSV export functionality
    """
    if report_type == 'stock-levels':
        items = db.session.query(Item).all()
        data = [{
            'item_code': item.item_code,
            'item_name': item.item_name,
            'category': item.category.category_name,
            'current_stock': item.current_stock,
            'reorder_level': item.reorder_level,
            'unit_price': float(item.unit_price),
            'total_value': float(item.current_stock * item.unit_price),
            'status': item.stock_status
        } for item in items]
        return jsonify(data)
    
    return jsonify({'error': 'Unknown report type'}), 400


# HELPER FUNCTIONS

def get_date_range(period='month'):
    """
    Get start and end dates for a period
    
    Args:
        period: 'today', 'week', 'month', 'year'
    
    Returns:
        tuple: (start_date, end_date)
    """
    today = datetime.now()
    
    if period == 'today':
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end = today
    elif period == 'week':
        start = today - timedelta(days=7)
        end = today
    elif period == 'month':
        start = today - timedelta(days=30)
        end = today
    elif period == 'year':
        start = today - timedelta(days=365)
        end = today
    else:
        start = today - timedelta(days=30)
        end = today
    
    return start, end


def calculate_stock_turnover(item_id, days=30):
    """
    Calculate stock turnover rate for an item
    
    Args:
        item_id: Item ID
        days: Number of days to calculate over
    
    Returns:
        float: Turnover rate
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # Get total stock out in period
    stock_out = db.session.query(func.sum(Transaction.quantity))\
        .join(Transaction.transaction_type)\
        .filter(TransactionType.type_name == 'STOCK_OUT')\
        .filter(Transaction.item_id == item_id)\
        .filter(Transaction.transaction_date >= start_date)\
        .scalar() or 0
    
    # Get average stock level
    item = db.session.get(Item, item_id)
    avg_stock = item.current_stock if item else 0
    
    # Calculate turnover
    if avg_stock > 0:
        turnover = stock_out / avg_stock
    else:
        turnover = 0
    
    return turnover