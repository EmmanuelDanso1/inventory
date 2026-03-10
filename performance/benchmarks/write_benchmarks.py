"""
Write Benchmarks
Compares insert/update performance between normalized and denormalized schemas
"""

import time
import uuid
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.transaction_type import TransactionType
from invent_app.models.denormalized.item_denorm import ItemDenorm
from invent_app.models.denormalized.transaction_denorm import TransactionDenorm


def _time_write(fn):
    """Time a single write operation in ms"""
    start = time.perf_counter()
    fn()
    return round((time.perf_counter() - start) * 1000, 3)


# ── BENCHMARK 1: Insert single item ─────────────────────────────────────────

def bench_insert_item_normalized(category_id):
    code = f'NORM-{uuid.uuid4().hex[:6].upper()}'
    item = Item(
        item_code=code,
        item_name=f'Test Item {code}',
        category_id=category_id,
        unit_price=9.99,
        current_stock=100,
        reorder_level=10
    )
    db.session.add(item)
    db.session.commit()
    db.session.delete(item)
    db.session.commit()

def bench_insert_item_denormalized():
    code = f'DENORM-{uuid.uuid4().hex[:6].upper()}'
    item = ItemDenorm(
        item_code=code,
        item_name=f'Test Item {code}',
        category_name='Test Category',
        supplier_name='Test Supplier',
        unit_price=9.99,
        current_stock=100,
        reorder_level=10
    )
    db.session.add(item)
    db.session.commit()
    db.session.delete(item)
    db.session.commit()


# ── BENCHMARK 2: Update category name ───────────────────────────────────────
# Normalized: update 1 row in categories table → all items reflect change
# Denormalized: must update ALL rows in items_denormalized table

def bench_update_category_normalized(category_id):
    cat = db.session.get(Category, category_id)
    original = cat.category_name
    cat.category_name = 'Updated Category Name'
    db.session.commit()
    cat.category_name = original
    db.session.commit()
    return db.session.query(Item).filter_by(category_id=category_id).count()

def bench_update_category_denormalized(old_name):
    items = db.session.query(ItemDenorm).filter_by(category_name=old_name).all()
    count = len(items)
    for item in items:
        item.category_name = 'Updated Category Name'
    db.session.commit()
    for item in items:
        item.category_name = old_name
    db.session.commit()
    return count


# ── RUN ALL WRITE BENCHMARKS ─────────────────────────────────────────────────

def run_write_benchmarks():
    # Get a valid category_id for normalized tests
    category = db.session.query(Category).first()
    category_id = category.category_id if category else None
    category_name = category.category_name if category else 'Electronics'

    results = []

    # Insert benchmark
    if category_id:
        norm_time   = _time_write(lambda: bench_insert_item_normalized(category_id))
        denorm_time = _time_write(bench_insert_item_denormalized)
    else:
        norm_time   = 0
        denorm_time = 0

    results.append({
        'name':        'Insert Single Item',
        'description': 'Insert one item and immediately clean up',
        'normalized':  {'avg_ms': norm_time},
        'denormalized':{'avg_ms': denorm_time},
        'winner':      'normalized' if norm_time < denorm_time else 'denormalized',
        'diff_pct':    round(abs(norm_time - denorm_time) / max(norm_time, denorm_time, 0.001) * 100, 1),
        'note': 'Normalized requires valid FK lookup; denormalized stores name directly'
    })

    # Category update benchmark
    if category_id:
        norm_time   = _time_write(lambda: bench_update_category_normalized(category_id))
        denorm_time = _time_write(lambda: bench_update_category_denormalized(category_name))
    else:
        norm_time   = 0
        denorm_time = 0

    results.append({
        'name':        'Update Category Name',
        'description': 'Rename a category and measure propagation cost',
        'normalized':  {'avg_ms': norm_time},
        'denormalized':{'avg_ms': denorm_time},
        'winner':      'normalized' if norm_time < denorm_time else 'denormalized',
        'diff_pct':    round(abs(norm_time - denorm_time) / max(norm_time, denorm_time, 0.001) * 100, 1),
        'note': 'Normalized updates 1 row; denormalized must update every matching item row'
    })

    return results
