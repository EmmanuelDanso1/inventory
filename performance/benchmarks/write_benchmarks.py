"""
Write Benchmarks - Compare insert/update performance between schemas.

Design note on indexing:
  Index maintenance during INSERT and UPDATE happens at the storage engine level,
  regardless of session-level planner settings. SET enable_indexscan = off only
  affects the query planner for SELECT operations. Write benchmarks therefore
  run under normal indexed conditions only. This reflects production-realistic
  behaviour and is documented as a methodological decision, not a limitation.

Changes vs original:
  - All operations run ITERATIONS times (was single-shot).
  - Standard deviation calculated for every benchmark.
  - Bulk insert benchmark added (50 rows per commit).
  - Bulk transaction insert benchmark added.
  - No misleading no-index write variants.
"""

import time
import math
import uuid
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.transaction_type import TransactionType
from invent_app.models.denormalized.item_denorm import ItemDenorm
from invent_app.models.denormalized.transaction_denorm import TransactionDenorm


ITERATIONS    = 10
BULK_ROW_SIZE = 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stddev(times):
    n = len(times)
    if n < 2:
        return 0.0
    mean = sum(times) / n
    return round(math.sqrt(sum((t - mean) ** 2 for t in times) / (n - 1)), 3)


def _run_iterations(fn, iterations=ITERATIONS):
    """Time a write function across multiple iterations and return stats dict."""
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
# Benchmark 1: Single-item insert + delete
# ---------------------------------------------------------------------------

def _insert_norm(category_id):
    code = f'NORM-{uuid.uuid4().hex[:8].upper()}'
    item = Item(
        item_code=code, item_name=f'Benchmark {code}',
        category_id=category_id, unit_price=9.99,
        current_stock=100, reorder_level=10
    )
    db.session.add(item)
    db.session.commit()
    db.session.delete(item)
    db.session.commit()


def _insert_denorm():
    code = f'DENORM-{uuid.uuid4().hex[:8].upper()}'
    item = ItemDenorm(
        item_code=code, item_name=f'Benchmark {code}',
        category_name='Electronics', supplier_name='Benchmark Supplier',
        unit_price=9.99, current_stock=100, reorder_level=10
    )
    db.session.add(item)
    db.session.commit()
    db.session.delete(item)
    db.session.commit()


# ---------------------------------------------------------------------------
# Benchmark 2: Bulk insert BULK_ROW_SIZE items in one commit
# ---------------------------------------------------------------------------

def _bulk_insert_norm(category_id):
    items = [
        Item(
            item_code=f'BULK-N-{uuid.uuid4().hex[:8].upper()}',
            item_name='Bulk Benchmark Item',
            category_id=category_id,
            unit_price=4.99, current_stock=50, reorder_level=5
        )
        for _ in range(BULK_ROW_SIZE)
    ]
    db.session.bulk_save_objects(items)
    db.session.commit()
    db.session.query(Item).filter(Item.item_code.like('BULK-N-%')).delete(synchronize_session=False)
    db.session.commit()


def _bulk_insert_denorm():
    items = [
        ItemDenorm(
            item_code=f'BULK-D-{uuid.uuid4().hex[:8].upper()}',
            item_name='Bulk Benchmark Item',
            category_name='Electronics', supplier_name='Bulk Supplier',
            unit_price=4.99, current_stock=50, reorder_level=5
        )
        for _ in range(BULK_ROW_SIZE)
    ]
    db.session.bulk_save_objects(items)
    db.session.commit()
    db.session.query(ItemDenorm).filter(ItemDenorm.item_code.like('BULK-D-%')).delete(synchronize_session=False)
    db.session.commit()


# ---------------------------------------------------------------------------
# Benchmark 3: Category rename propagation
# Normalized: 1 row updated → all items reflect change via FK
# Denormalized: every matching item row must be rewritten
# ---------------------------------------------------------------------------

def _rename_category_norm(category_id):
    cat = db.session.get(Category, category_id)
    original = cat.category_name
    cat.category_name = '__BenchmarkRename__'
    db.session.commit()
    cat.category_name = original
    db.session.commit()


def _rename_category_denorm(category_name):
    rows = db.session.query(ItemDenorm).filter_by(category_name=category_name).all()
    for row in rows:
        row.category_name = '__BenchmarkRename__'
    db.session.commit()
    for row in rows:
        row.category_name = category_name
    db.session.commit()


# ---------------------------------------------------------------------------
# Benchmark 4: Bulk transaction insert
# ---------------------------------------------------------------------------

def _bulk_tx_norm(category_id):
    sentinel = f'TX-N-{uuid.uuid4().hex[:6].upper()}'
    item = Item(
        item_code=sentinel, item_name='TX Benchmark Item',
        category_id=category_id, unit_price=1.00,
        current_stock=9999, reorder_level=1
    )
    db.session.add(item)
    db.session.flush()

    tx_type = db.session.query(TransactionType).filter_by(type_name='STOCK_IN').first()
    txs = [
        Transaction(
            item_id=item.item_id, type_id=tx_type.type_id,
            quantity=1, unit_price=1.00,
            reference_number=f'REF-{uuid.uuid4().hex[:6].upper()}'
        )
        for _ in range(BULK_ROW_SIZE)
    ]
    db.session.bulk_save_objects(txs)
    db.session.commit()
    db.session.query(Transaction).filter_by(item_id=item.item_id).delete(synchronize_session=False)
    db.session.delete(item)
    db.session.commit()


def _bulk_tx_denorm():
    txs = [
        TransactionDenorm(
            item_code=f'TX-D-{uuid.uuid4().hex[:6].upper()}',
            item_name='TX Benchmark Item',
            category_name='Electronics', supplier_name='Benchmark Supplier',
            transaction_type='STOCK_IN', quantity=1, unit_price=1.00,
            reference_number=f'REF-{uuid.uuid4().hex[:6].upper()}'
        )
        for _ in range(BULK_ROW_SIZE)
    ]
    db.session.bulk_save_objects(txs)
    db.session.commit()
    db.session.query(TransactionDenorm).filter(
        TransactionDenorm.item_name == 'TX Benchmark Item'
    ).delete(synchronize_session=False)
    db.session.commit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_write_benchmarks(iterations=ITERATIONS):
    """
    Run all write benchmarks under normal (indexed) conditions.
    Returns a list of result dicts for the performance.html template.
    """
    # Resolve FK anchors
    category = db.session.query(Category).first()
    if not category:
        fallback = Category(category_name='__Benchmark__', description='Auto-created')
        db.session.add(fallback)
        db.session.commit()
        category = fallback

    category_id   = category.category_id
    category_name = category.category_name

    benchmark_defs = [
        {
            'name':        'Single Item Insert',
            'description': f'Insert one item then delete it ({iterations} iterations)',
            'note':        'Normalized requires valid FK; denormalized stores name directly.',
            'norm_fn':     lambda: _insert_norm(category_id),
            'denorm_fn':   _insert_denorm,
        },
        {
            'name':        f'Bulk Insert ({BULK_ROW_SIZE} items)',
            'description': f'Insert {BULK_ROW_SIZE} items in one transaction ({iterations} iterations)',
            'note':        'Tests batch write throughput. Both schemas maintain indexes during insert.',
            'norm_fn':     lambda: _bulk_insert_norm(category_id),
            'denorm_fn':   _bulk_insert_denorm,
        },
        {
            'name':        'Category Rename Propagation',
            'description': f'Rename a category and measure propagation cost ({iterations} iterations)',
            'note':        'Normalized updates 1 row; denormalized rewrites every matching item row.',
            'norm_fn':     lambda: _rename_category_norm(category_id),
            'denorm_fn':   lambda: _rename_category_denorm(category_name),
        },
        {
            'name':        f'Bulk Transaction Insert ({BULK_ROW_SIZE} rows)',
            'description': f'Insert {BULK_ROW_SIZE} transaction records in one commit ({iterations} iterations)',
            'note':        'Simulates automated stock sync. Normalized uses FK; denormalized is self-contained.',
            'norm_fn':     lambda: _bulk_tx_norm(category_id),
            'denorm_fn':   _bulk_tx_denorm,
        },
    ]

    results = []
    for b in benchmark_defs:
        row = {'name': b['name'], 'description': b['description'], 'note': b['note']}

        for key, fn in [('normalized', b['norm_fn']), ('denormalized', b['denorm_fn'])]:
            try:
                row[key] = _run_iterations(fn, iterations)
            except Exception as e:
                db.session.rollback()
                row[key] = {
                    'avg_ms': 0, 'min_ms': 0, 'max_ms': 0,
                    'stddev_ms': 0, 'iterations': 0, 'error': str(e)
                }

        n = row['normalized']['avg_ms']
        d = row['denormalized']['avg_ms']
        if n > 0 and d > 0:
            faster      = 'normalized' if n < d else 'denormalized'
            slower_val  = max(n, d)
            row['winner']   = faster
            row['diff_ms']  = round(abs(n - d), 3)
            row['diff_pct'] = round(abs(n - d) / slower_val * 100, 1)
        else:
            row['winner']   = 'error'
            row['diff_ms']  = 0
            row['diff_pct'] = 0

        results.append(row)

    return results
