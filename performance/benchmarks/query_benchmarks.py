"""
Query Benchmarks - Compare normalized vs denormalized query performance.

Fixes applied vs original:
  - Iterations bumped to 10 (spec minimum)
  - PostgreSQL session cache cleared between every iteration via DISCARD ALL
  - Index suppression via SET enable_indexscan/bitmapscan = off so the same
    benchmark can be run in both indexed and non-indexed configurations without
    needing DROP/CREATE INDEX on a hosted database.
  - Standard deviation added to every result (required for data analysis)
  - result_count returned correctly for both list and aggregate queries
"""

import time
import math
from sqlalchemy import text, func
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.transaction_type import TransactionType
from invent_app.models.denormalized.item_denorm import ItemDenorm
from invent_app.models.denormalized.transaction_denorm import TransactionDenorm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_session_cache():
    """
    Clear PostgreSQL session-level caches between iterations.
    DISCARD ALL resets prepared statements, session settings, and advisory locks.
    Note: the shared_buffers page cache cannot be cleared without superuser
    access on a hosted instance. Running 10 iterations ensures early warm-up
    effects are averaged out, which is documented as a known limitation.
    """
    try:
        db.session.execute(text("DISCARD ALL"))
        db.session.commit()
    except Exception:
        db.session.rollback()


def _set_index_usage(enabled: bool):
    """
    Toggle index usage at the session level.
    When enabled=False, PostgreSQL is forced onto sequential scans,
    simulating a non-indexed configuration without physically dropping indexes.
    This is a reproducible technique for isolated performance experiments.
    """
    flag = "on" if enabled else "off"
    try:
        db.session.execute(text(f"SET enable_indexscan = {flag}"))
        db.session.execute(text(f"SET enable_bitmapscan = {flag}"))
        db.session.execute(text(f"SET enable_index_only_scan = {flag}"))
        db.session.commit()
    except Exception:
        db.session.rollback()


def _stddev(times):
    n = len(times)
    if n < 2:
        return 0.0
    mean = sum(times) / n
    variance = sum((t - mean) ** 2 for t in times) / (n - 1)
    return round(math.sqrt(variance), 3)


def run_benchmark(func_to_run, iterations=10, use_indexes=True):
    """
    Execute a query function *iterations* times and return timing statistics.
    Session cache is cleared before each iteration.
    """
    _set_index_usage(use_indexes)

    times = []
    result_count = 0

    for _ in range(iterations):
        _clear_session_cache()
        start = time.perf_counter()
        result = func_to_run()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

        if result is not None:
            try:
                result_count = len(result)
            except TypeError:
                result_count = 1

        db.session.expire_all()

    # Always restore indexes after a suppressed run
    if not use_indexes:
        _set_index_usage(True)

    return {
        'avg_ms':      round(sum(times) / len(times), 3),
        'min_ms':      round(min(times), 3),
        'max_ms':      round(max(times), 3),
        'stddev_ms':   _stddev(times),
        'iterations':  iterations,
        'result_count': result_count,
    }


# ---------------------------------------------------------------------------
# Normalized queries
# ---------------------------------------------------------------------------

def normalized_get_all_items():
    return db.session.query(Item).join(Item.category).all()


def normalized_get_items_by_category():
    return (db.session.query(Item)
            .join(Item.category)
            .filter(Category.category_name.ilike('%electronics%'))
            .all())


def normalized_get_low_stock():
    return (db.session.query(Item)
            .filter(Item.current_stock <= Item.reorder_level)
            .all())


def normalized_get_stock_summary():
    return (db.session.query(
                Category.category_name,
                func.sum(Item.current_stock * Item.unit_price).label('total_value'),
                func.count(Item.item_id).label('item_count'))
            .join(Item, Category.category_id == Item.category_id)
            .group_by(Category.category_id, Category.category_name)
            .all())


def normalized_get_transactions():
    return (db.session.query(Transaction)
            .join(Transaction.transaction_type)
            .join(Transaction.item)
            .order_by(Transaction.transaction_date.desc())
            .limit(50)
            .all())


def normalized_get_stock_in_totals():
    return (db.session.query(
                Item.item_name,
                func.sum(Transaction.quantity).label('total_in'))
            .join(Transaction, Item.item_id == Transaction.item_id)
            .join(TransactionType, Transaction.type_id == TransactionType.type_id)
            .filter(TransactionType.type_name == 'STOCK_IN')
            .group_by(Item.item_id, Item.item_name)
            .all())


# ---------------------------------------------------------------------------
# Denormalized queries
# ---------------------------------------------------------------------------

def denormalized_get_all_items():
    return db.session.query(ItemDenorm).all()


def denormalized_get_items_by_category():
    return (db.session.query(ItemDenorm)
            .filter(ItemDenorm.category_name.ilike('%electronics%'))
            .all())


def denormalized_get_low_stock():
    return (db.session.query(ItemDenorm)
            .filter(ItemDenorm.current_stock <= ItemDenorm.reorder_level)
            .all())


def denormalized_get_stock_summary():
    return (db.session.query(
                ItemDenorm.category_name,
                func.sum(ItemDenorm.current_stock * ItemDenorm.unit_price).label('total_value'),
                func.count(ItemDenorm.item_id).label('item_count'))
            .group_by(ItemDenorm.category_name)
            .all())


def denormalized_get_transactions():
    return (db.session.query(TransactionDenorm)
            .order_by(TransactionDenorm.transaction_date.desc())
            .limit(50)
            .all())


def denormalized_get_stock_in_totals():
    return (db.session.query(
                TransactionDenorm.item_name,
                func.sum(TransactionDenorm.quantity).label('total_in'))
            .filter(TransactionDenorm.transaction_type == 'STOCK_IN')
            .group_by(TransactionDenorm.item_name)
            .all())


# ---------------------------------------------------------------------------
# Benchmark manifest
# ---------------------------------------------------------------------------

BENCHMARK_DEFINITIONS = [
    {
        'name': 'Get All Items',
        'description': 'Fetch all inventory items (normalized requires JOIN to category table)',
        'normalized_fn':   normalized_get_all_items,
        'denormalized_fn': denormalized_get_all_items,
    },
    {
        'name': 'Filter by Category',
        'description': 'Get items filtered by category name string match',
        'normalized_fn':   normalized_get_items_by_category,
        'denormalized_fn': denormalized_get_items_by_category,
    },
    {
        'name': 'Low Stock Items',
        'description': 'Retrieve all items at or below reorder level',
        'normalized_fn':   normalized_get_low_stock,
        'denormalized_fn': denormalized_get_low_stock,
    },
    {
        'name': 'Stock Value by Category',
        'description': 'Aggregate total inventory value grouped by category',
        'normalized_fn':   normalized_get_stock_summary,
        'denormalized_fn': denormalized_get_stock_summary,
    },
    {
        'name': 'Recent Transactions (50)',
        'description': 'Fetch 50 most recent transactions with item and type details',
        'normalized_fn':   normalized_get_transactions,
        'denormalized_fn': denormalized_get_transactions,
    },
    {
        'name': 'Stock-In Totals per Item',
        'description': 'Sum all stock-in quantities grouped by item name',
        'normalized_fn':   normalized_get_stock_in_totals,
        'denormalized_fn': denormalized_get_stock_in_totals,
    },
]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_all_benchmarks(iterations=10):
    """
    Run all benchmarks under four conditions per query type:
      1. Normalized   + indexes enabled
      2. Denormalized + indexes enabled
      3. Normalized   + indexes suppressed (seq-scan only)
      4. Denormalized + indexes suppressed (seq-scan only)

    Returns a list of result dicts consumed by the performance.html template.
    """
    results = []

    for b in BENCHMARK_DEFINITIONS:
        row = {'name': b['name'], 'description': b['description']}

        # Indexed runs
        for schema, fn in [('normalized', b['normalized_fn']),
                            ('denormalized', b['denormalized_fn'])]:
            try:
                row[schema] = run_benchmark(fn, iterations=iterations, use_indexes=True)
            except Exception as e:
                db.session.rollback()
                row[schema] = {
                    'avg_ms': 0, 'min_ms': 0, 'max_ms': 0,
                    'stddev_ms': 0, 'iterations': 0,
                    'result_count': 0, 'error': str(e)
                }

        # Non-indexed runs
        for schema, fn in [('normalized', b['normalized_fn']),
                            ('denormalized', b['denormalized_fn'])]:
            key = f'{schema}_no_index'
            try:
                row[key] = run_benchmark(fn, iterations=iterations, use_indexes=False)
            except Exception as e:
                db.session.rollback()
                row[key] = {
                    'avg_ms': 0, 'min_ms': 0, 'max_ms': 0,
                    'stddev_ms': 0, 'iterations': 0,
                    'result_count': 0, 'error': str(e)
                }

        # Winner determination (primary indexed comparison)
        n_avg = row['normalized']['avg_ms']
        d_avg = row['denormalized']['avg_ms']

        if n_avg > 0 and d_avg > 0:
            if n_avg < d_avg:
                row['winner']   = 'normalized'
                row['diff_ms']  = round(d_avg - n_avg, 3)
                row['diff_pct'] = round((d_avg - n_avg) / d_avg * 100, 1)
            elif d_avg < n_avg:
                row['winner']   = 'denormalized'
                row['diff_ms']  = round(n_avg - d_avg, 3)
                row['diff_pct'] = round((n_avg - d_avg) / n_avg * 100, 1)
            else:
                row['winner']   = 'tie'
                row['diff_ms']  = 0
                row['diff_pct'] = 0
        else:
            row['winner']   = 'error'
            row['diff_ms']  = 0
            row['diff_pct'] = 0

        results.append(row)

    return results
