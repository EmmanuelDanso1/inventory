from flask import Blueprint, render_template
# from app.models.normalized.item import Item
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

# @bp.route('/dashboard')
# def dashboard():
#     # Get summary statistics
#     total_items = db.session.query(Item).count()
#     low_stock_items = db.session.query(Item).filter(
#         Item.current_stock <= Item.reorder_level
#     ).count()
    
#     return render_template('reports/dashboard.html',
#                          total_items=total_items,
#                          low_stock_items=low_stock_items)