"""
Write Benchmarks - Compare insert/update performance between schemas.

Fixes applied vs original:
  - All write operations now run ITERATIONS times (was single-shot before).
  - Standard deviation calculated for every write benchmark.
  - Bulk insert benchmark added: tests inserting N rows in one commit,
    which is more representative than single-row insert/delete cycles.
  - Index suppression applied for non-indexed write comparison.
  - Cleanup is handled within each iteration so tests stay self-contained.
"""

import time
import math
import uuid
from sqlalchemy import text
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.transaction_type import TransactionType
from invent_app.models.denormalized.item_denorm import ItemDenorm
from invent_app.models.denormalized.transaction_denorm import TransactionDenorm


ITERATIONS = 10
BULK_INSERT_SIZE = 50   # rows per bulk-insert test


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stddev(times):
    n = len(times)
    if n < 2:
        return 0.0
    mean = sum(times) / n
    return round(math.sqrt(sum((t - mean) ** 2 for t in times) / (n - 1)), 3)


def _set_index_usage(enabled: bool):
    flag = "on" if enabled else "off"
    try:
        db.session.execute(text(f"SET enable_indexscan = {flag}"))
        db.session.execute(text(f"SET enable_bitmapscan = {flag}"))
        db.session.execute(text(f"SET enable_index_only_scan = {flag}"))
        db.session.commit()
    except Exception:
        db.session.rollback()


def _run_write_iterations(fn, iterations=ITERATIONS):
    """Time a write function across multiple iterations. Returns stats dict."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        times.append((time.perf_counter() - start) * 1000)
    return {
        'avg_ms':    round(sum(times) / len(times), 3),
        'min_ms':    round(min(times), 3),
        'max_ms':    round(max(times), 3),
        'stddev_ms': _stddev(times),
        'iterations': iterations,
    }


# ---------------------------------------------------------------------------
# Benchmark 1: Single-item insert (round-trip: insert + delete)
# ---------------------------------------------------------------------------

def _insert_item_normalized(category_id):
    code = f'NORM-{uuid.uuid4().hex[:8].upper()}'
    item = Item(
        item_code=code,
        item_name=f'Benchmark Item {code}',
        category_id=category_id,
        unit_price=9.99,
        current_stock=100,
        reorder_level=10
    )
    db.session.add(item)
    db.session.commit()
    db.session.delete(item)
    db.session.commit()


def _insert_item_denormalized():
    code = f'DENORM-{uuid.uuid4().hex[:8].upper()}'
    item = ItemDenorm(
        item_code=code,
        item_name=f'Benchmark Item {code}',
        category_name='Electronics',
        supplier_name='Benchmark Supplier',
        unit_price=9.99,
        current_stock=100,
        reorder_level=10
    )
    db.session.add(item)
    db.session.commit()
    db.session.delete(item)
    db.session.commit()


# ---------------------------------------------------------------------------
# Benchmark 2: Bulk insert (BULK_INSERT_SIZE rows in one transaction)
# ---------------------------------------------------------------------------

def _bulk_insert_normalized(category_id):
    items = []
    for _ in range(BULK_INSERT_SIZE):
        code = f'BULK-N-{uuid.uuid4().hex[:8].upper()}'
        items.append(Item(
            item_code=code,
            item_name=f'Bulk Item {code}',
            category_id=category_id,
            unit_price=4.99,
            current_stock=50,
            reorder_level=5
        ))
    db.session.bulk_save_objects(items)
    db.session.commit()
    # Cleanup: remove what we just inserted
    db.session.query(Item).filter(Item.item_code.like('BULK-N-%')).delete(synchronize_session=False)
    db.session.commit()


def _bulk_insert_denormalized():
    items = []
    for _ in range(BULK_INSERT_SIZE):
        code = f'BULK-D-{uuid.uuid4().hex[:8].upper()}'
        items.append(ItemDenorm(
            item_code=code,
            item_name=f'Bulk Item {code}',
            category_name='Electronics',
            supplier_name='Bulk Supplier',
            unit_price=4.99,
            current_stock=50,
            reorder_level=5
        ))
    db.session.bulk_save_objects(items)
    db.session.commit()
    db.session.query(ItemDenorm).filter(ItemDenorm.item_code.like('BULK-D-%')).delete(synchronize_session=False)
    db.session.commit()


# ---------------------------------------------------------------------------
# Benchmark 3: Category rename propagation
# Normalized: update 1 row in categories → all items reflect it via FK
# Denormalized: must rewrite every matching row in items_denormalized
# ---------------------------------------------------------------------------

def _update_category_normalized(category_id):
    cat = db.session.get(Category, category_id)
    original = cat.category_name
    cat.category_name = '__BenchmarkRename__'
    db.session.commit()
    cat.category_name = original
    db.session.commit()


def _update_category_denormalized(category_name):
    rows = db.session.query(ItemDenorm).filter_by(category_name=category_name).all()
    for row in rows:
        row.category_name = '__BenchmarkRename__'
    db.session.commit()
    for row in rows:
        row.category_name = category_name
    db.session.commit()


# ---------------------------------------------------------------------------
# Benchmark 4: Bulk transaction insert
# Simulates automated discovery tool syncing many stock events at once
# ---------------------------------------------------------------------------

def _bulk_insert_transactions_normalized(category_id):
    item_code = f'TX-N-{uuid.uuid4().hex[:6].upper()}'
    item = Item(
        item_code=item_code,
        item_name='Transaction Benchmark Item',
        category_id=category_id,
        unit_price=1.00,
        current_stock=9999,
        reorder_level=1
    )
    db.session.add(item)
    db.session.flush()

    tx_type = db.session.query(TransactionType).filter_by(type_name='STOCK_IN').first()
    txs = [
        Transaction(
            item_id=item.item_id,
            type_id=tx_type.type_id,
            quantity=1,
            unit_price=1.00,
            reference_number=f'REF-{uuid.uuid4().hex[:6].upper()}'
        )
        for _ in range(BULK_INSERT_SIZE)
    ]
    db.session.bulk_save_objects(txs)
    db.session.commit()

    # Cleanup
    db.session.query(Transaction).filter_by(item_id=item.item_id).delete(synchronize_session=False)
    db.session.delete(item)
    db.session.commit()


def _bulk_insert_transactions_denormalized():
    txs = [
        TransactionDenorm(
            item_code=f'TX-D-{uuid.uuid4().hex[:6].upper()}',
            item_name='Transaction Benchmark Item',
            category_name='Electronics',
            supplier_name='Benchmark Supplier',
            transaction_type='STOCK_IN',
            quantity=1,
            unit_price=1.00,
            reference_number=f'REF-{uuid.uuid4().hex[:6].upper()}'
        )
        for _ in range(BULK_INSERT_SIZE)
    ]
    db.session.bulk_save_objects(txs)
    db.session.commit()
    db.session.query(TransactionDenorm).filter(
        TransactionDenorm.item_name == 'Transaction Benchmark Item'
    ).delete(synchronize_session=False)
    db.session.commit()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_write_benchmarks(iterations=ITERATIONS):
    """
    Run all write benchmarks under both indexed and non-indexed conditions.
    Returns a list of result dicts for the performance.html template.
    """
    # Resolve required FK references once
    category = db.session.query(Category).first()
    category_id   = category.category_id   if category else None
    category_name = category.category_name if category else 'Electronics'

    # Fallback category for FK tests
    if not category_id:
        fallback = Category(category_name='__Benchmark__', description='Auto-created for benchmarks')
        db.session.add(fallback)
        db.session.commit()
        category_id   = fallback.category_id
        category_name = fallback.category_name

    results = []

    benchmarks = [
        {
            'name': 'Single Item Insert',
            'description': f'Insert one item then delete it ({iterations} iterations)',
            'note': 'Normalized requires valid FK lookup; denormalized stores name directly.',
            'norm_fn':   lambda: _insert_item_normalized(category_id),
            'denorm_fn': _insert_item_denormalized,
        },
        {
            'name': f'Bulk Insert ({BULK_INSERT_SIZE} items)',
            'description': f'Insert {BULK_INSERT_SIZE} items in a single transaction ({iterations} iterations)',
            'note': 'Tests batch write throughput. Normalized has index maintenance on multiple columns.',
            'norm_fn':   lambda: _bulk_insert_normalized(category_id),
            'denorm_fn': _bulk_insert_denormalized,
        },
        {
            'name': 'Category Rename Propagation',
            'description': 'Rename a category and measure the propagation cost',
            'note': 'Normalized updates 1 row; denormalized must rewrite every matching item row.',
            'norm_fn':   lambda: _update_category_normalized(category_id),
            'denorm_fn': lambda: _update_category_denormalized(category_name),
        },
        {
            'name': f'Bulk Transaction Insert ({BULK_INSERT_SIZE} rows)',
            'description': f'Insert {BULK_INSERT_SIZE} transaction records in one commit',
            'note': 'Simulates automated discovery tool syncing. Normalized uses FK joins; denormalized is self-contained.',
            'norm_fn':   lambda: _bulk_insert_transactions_normalized(category_id),
            'denorm_fn': _bulk_insert_transactions_denormalized,
        },
    ]

    for b in benchmarks:
        row = {
            'name':        b['name'],
            'description': b['description'],
            'note':        b['note'],
        }

        # Indexed
        for key, fn in [('normalized', b['norm_fn']), ('denormalized', b['denorm_fn'])]:
            try:
                _set_index_usage(True)
                row[key] = _run_write_iterations(fn, iterations)
            except Exception as e:
                db.session.rollback()
                row[key] = {'avg_ms': 0, 'min_ms': 0, 'max_ms': 0, 'stddev_ms': 0, 'error': str(e)}

        # Non-indexed
        for key, fn in [('normalized', b['norm_fn']), ('denormalized', b['denorm_fn'])]:
            ni_key = f'{key}_no_index'
            try:
                _set_index_usage(False)
                row[ni_key] = _run_write_iterations(fn, iterations)
            except Exception as e:
                db.session.rollback()
                row[ni_key] = {'avg_ms': 0, 'min_ms': 0, 'max_ms': 0, 'stddev_ms': 0, 'error': str(e)}

        _set_index_usage(True)  # restore

        # Winner
        n_avg = row['normalized']['avg_ms']
        d_avg = row['denormalized']['avg_ms']
        if n_avg > 0 and d_avg > 0:
            faster = 'normalized' if n_avg < d_avg else 'denormalized'
            slower_val = max(n_avg, d_avg)
            row['winner']   = faster
            row['diff_ms']  = round(abs(n_avg - d_avg), 3)
            row['diff_pct'] = round(abs(n_avg - d_avg) / slower_val * 100, 1)
        else:
            row['winner']   = 'error'
            row['diff_ms']  = 0
            row['diff_pct'] = 0

        results.append(row)

    return results
