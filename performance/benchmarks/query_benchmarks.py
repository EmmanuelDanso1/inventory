"""
Query Benchmarks - Compare normalized vs denormalized query performance
"""

import time
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.transaction_type import TransactionType
from invent_app.models.denormalized.item_denorm import ItemDenorm
from invent_app.models.denormalized.transaction_denorm import TransactionDenorm
from sqlalchemy import func


def run_benchmark(func_to_run, iterations=5):
    """Run a function multiple times and return average time in ms"""
    times = []
    result = None
    for _ in range(iterations):
        start = time.perf_counter()
        result = func_to_run()
        end = time.perf_counter()
        times.append((end - start) * 1000)
        db.session.expire_all()
    return {
        'avg_ms': round(sum(times) / len(times), 3),
        'min_ms': round(min(times), 3),
        'max_ms': round(max(times), 3),
        'result_count': len(result) if result and hasattr(result, '__len__') else 0
    }


# NORMALIZED QUERIES

def normalized_get_all_items():
    return db.session.query(Item).join(Item.category).all()


def normalized_get_items_by_category():
    return db.session.query(Item)\
        .join(Item.category)\
        .filter(Category.category_name.ilike('%electronics%'))\
        .all()


def normalized_get_low_stock():
    return db.session.query(Item)\
        .filter(Item.current_stock <= Item.reorder_level)\
        .all()


def normalized_get_stock_summary():
    return db.session.query(
        Category.category_name,
        func.sum(Item.current_stock * Item.unit_price).label('total_value'),
        func.count(Item.item_id).label('item_count')
    ).join(Item, Category.category_id == Item.category_id)\
     .group_by(Category.category_id, Category.category_name)\
     .all()


def normalized_get_transactions():
    return db.session.query(Transaction)\
        .join(Transaction.transaction_type)\
        .join(Transaction.item)\
        .order_by(Transaction.transaction_date.desc())\
        .limit(50)\
        .all()


def normalized_get_stock_in_totals():
    return db.session.query(
        Item.item_name,
        func.sum(Transaction.quantity).label('total_in')
    ).join(Transaction, Item.item_id == Transaction.item_id)\
     .join(TransactionType, Transaction.type_id == TransactionType.type_id)\
     .filter(TransactionType.type_name == 'STOCK_IN')\
     .group_by(Item.item_id, Item.item_name)\
     .all()


# DENORMALIZED QUERIES

def denormalized_get_all_items():
    return db.session.query(ItemDenorm).all()


def denormalized_get_items_by_category():
    return db.session.query(ItemDenorm)\
        .filter(ItemDenorm.category_name.ilike('%electronics%'))\
        .all()


def denormalized_get_low_stock():
    return db.session.query(ItemDenorm)\
        .filter(ItemDenorm.current_stock <= ItemDenorm.reorder_level)\
        .all()


def denormalized_get_stock_summary():
    return db.session.query(
        ItemDenorm.category_name,
        func.sum(ItemDenorm.current_stock * ItemDenorm.unit_price).label('total_value'),
        func.count(ItemDenorm.item_id).label('item_count')
    ).group_by(ItemDenorm.category_name)\
     .all()


def denormalized_get_transactions():
    return db.session.query(TransactionDenorm)\
        .order_by(TransactionDenorm.transaction_date.desc())\
        .limit(50)\
        .all()


def denormalized_get_stock_in_totals():
    return db.session.query(
        TransactionDenorm.item_name,
        func.sum(TransactionDenorm.quantity).label('total_in')
    ).filter(TransactionDenorm.transaction_type == 'STOCK_IN')\
     .group_by(TransactionDenorm.item_name)\
     .all()



def run_all_benchmarks():
    """Run all benchmarks and return comparison results"""
    benchmarks = [
        {
            'name': 'Get All Items',
            'description': 'Fetch all inventory items (normalized needs JOIN to category)',
            'normalized_fn': normalized_get_all_items,
            'denormalized_fn': denormalized_get_all_items,
        },
        {
            'name': 'Filter by Category',
            'description': 'Get items filtered by category name',
            'normalized_fn': normalized_get_items_by_category,
            'denormalized_fn': denormalized_get_items_by_category,
        },
        {
            'name': 'Low Stock Items',
            'description': 'Get all items below reorder level',
            'normalized_fn': normalized_get_low_stock,
            'denormalized_fn': denormalized_get_low_stock,
        },
        {
            'name': 'Stock Value by Category',
            'description': 'Aggregate total inventory value grouped by category',
            'normalized_fn': normalized_get_stock_summary,
            'denormalized_fn': denormalized_get_stock_summary,
        },
        {
            'name': 'Recent Transactions',
            'description': 'Fetch  all transactions with item and type details',
            'normalized_fn': normalized_get_transactions,
            'denormalized_fn': denormalized_get_transactions,
        },
        {
            'name': 'Stock In Totals per Item',
            'description': 'Sum of all stock-in quantities grouped by item',
            'normalized_fn': normalized_get_stock_in_totals,
            'denormalized_fn': denormalized_get_stock_in_totals,
        },
    ]

    results = []
    for b in benchmarks:
        try:
            norm = run_benchmark(b['normalized_fn'])
        except Exception as e:
            norm = {'avg_ms': 0, 'min_ms': 0, 'max_ms': 0, 'result_count': 0, 'error': str(e)}

        try:
            denorm = run_benchmark(b['denormalized_fn'])
        except Exception as e:
            denorm = {'avg_ms': 0, 'min_ms': 0, 'max_ms': 0, 'result_count': 0, 'error': str(e)}

        if norm['avg_ms'] > 0 and denorm['avg_ms'] > 0:
            if norm['avg_ms'] < denorm['avg_ms']:
                winner = 'normalized'
                diff = round(denorm['avg_ms'] - norm['avg_ms'], 3)
            elif denorm['avg_ms'] < norm['avg_ms']:
                winner = 'denormalized'
                diff = round(norm['avg_ms'] - denorm['avg_ms'], 3)
            else:
                winner = 'tie'
                diff = 0
        else:
            winner = 'error'
            diff = 0

        results.append({
            'name': b['name'],
            'description': b['description'],
            'normalized': norm,
            'denormalized': denorm,
            'winner': winner,
            'diff_ms': diff,
        })

    return results
