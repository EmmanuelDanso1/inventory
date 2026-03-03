from flask import Blueprint, render_template
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@bp.route('/dashboard')
def dashboard():
    """Main dashboard with statistics and charts"""
    # Get statistics
    total_items = db.session.query(Item).count()
    
    in_stock_items = db.session.query(Item).filter(
        Item.current_stock > Item.reorder_level
    ).count()
    
    low_stock_items = db.session.query(Item).filter(
        Item.current_stock > 0,
        Item.current_stock <= Item.reorder_level
    ).count()
    
    out_of_stock_items = db.session.query(Item).filter(
        Item.current_stock == 0
    ).count()
    
    # Get recent transactions (last 10)
    recent_transactions = db.session.query(Transaction)\
        .order_by(Transaction.transaction_date.desc())\
        .limit(10)\
        .all()
    
    # Get chart data (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Stock In data
    stock_in_data = db.session.query(
        func.date(Transaction.transaction_date).label('date'),
        func.sum(Transaction.quantity).label('total')
    ).join(Transaction.transaction_type)\
     .filter(
         Transaction.transaction_date >= thirty_days_ago,
         Transaction.transaction_type.has(type_name='STOCK_IN')
     ).group_by(func.date(Transaction.transaction_date))\
      .order_by('date')\
      .all()
    
    # Stock Out data
    stock_out_data = db.session.query(
        func.date(Transaction.transaction_date).label('date'),
        func.sum(Transaction.quantity).label('total')
    ).join(Transaction.transaction_type)\
     .filter(
         Transaction.transaction_date >= thirty_days_ago,
         Transaction.transaction_type.has(type_name='STOCK_OUT')
     ).group_by(func.date(Transaction.transaction_date))\
      .order_by('date')\
      .all()
    
    # Prepare chart data - generate all 30 days regardless of transactions
    chart_labels = []
    stock_in_values = []
    stock_out_values = []

    # Convert query results to dicts for easy lookup
    stock_in_dict = {str(row.date): int(row.total or 0) for row in stock_in_data}
    stock_out_dict = {str(row.date): int(row.total or 0) for row in stock_out_data}

    # Fill in all 30 days, using 0 where no transactions exist
    for i in range(30):
        day = (datetime.utcnow() - timedelta(days=29 - i)).date()
        day_str = str(day)
        chart_labels.append(day.strftime('%b %d'))
        stock_in_values.append(stock_in_dict.get(day_str, 0))
        stock_out_values.append(stock_out_dict.get(day_str, 0))
        
    return render_template(
        'reports/dashboard.html',
        total_items=total_items,
        in_stock_items=in_stock_items,
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        recent_transactions=recent_transactions,
        chart_labels=chart_labels,
        stock_in_data=stock_in_values,
        stock_out_data=stock_out_values
    )

