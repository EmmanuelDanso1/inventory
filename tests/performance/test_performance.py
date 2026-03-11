"""
Performance tests
Compares query speed between normalized and denormalized schemas
and validates benchmark results structure
"""

import time
import pytest
from sqlalchemy import func
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.transaction_type import TransactionType
from invent_app.models.denormalized.item_denorm import ItemDenorm
from invent_app.models.denormalized.transaction_denorm import TransactionDenorm


# ── HELPERS ───────────────────────────────────────────────────────────────────

def time_query(fn, runs=3):
    """Run a query fn multiple times and return avg ms"""
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        times.append((time.perf_counter() - start) * 1000)
    return round(sum(times) / len(times), 3)


def seed_normalized(db, category, n=50):
    """Seed n items into normalized schema"""
    items = [
        Item(
            item_code=f'PERF-N-{i:04d}',
            item_name=f'Normalized Item {i}',
            category_id=category.category_id,
            unit_price=float(i * 10),
            current_stock=i,
            reorder_level=5
        ) for i in range(1, n + 1)
    ]
    db.session.bulk_save_objects(items)
    db.session.commit()


def seed_denormalized(db, n=50):
    """Seed n items into denormalized schema"""
    items = [
        ItemDenorm(
            item_code=f'PERF-D-{i:04d}',
            item_name=f'Denormalized Item {i}',
            category_name='Electronics',
            supplier_name='Test Supplier',
            unit_price=float(i * 10),
            current_stock=i,
            reorder_level=5
        ) for i in range(1, n + 1)
    ]
    db.session.bulk_save_objects(items)
    db.session.commit()


def seed_denorm_transactions(db, n=50):
    """Seed n transactions into denormalized schema"""
    transactions = [
        TransactionDenorm(
            transaction_type='STOCK_IN' if i % 2 == 0 else 'STOCK_OUT',
            quantity=i + 1,
            item_code=f'PERF-D-{(i % 50) + 1:04d}',
            item_name=f'Denormalized Item {(i % 50) + 1}',
            category_name='Electronics',
            supplier_name='Test Supplier'
        ) for i in range(n)
    ]
    db.session.bulk_save_objects(transactions)
    db.session.commit()


# ── BENCHMARK RESULT STRUCTURE TESTS ─────────────────────────────────────────

class TestBenchmarkStructure:
    """Validate that benchmark functions return correct data structures"""

    def test_benchmark_result_has_required_keys(self, app):
        with app.app_context():
            try:
                from performance.benchmarks.query_benchmarks import run_all_benchmarks
                results = run_all_benchmarks()
                assert isinstance(results, list)
                for r in results:
                    assert 'name' in r
                    assert 'description' in r
                    assert 'normalized' in r
                    assert 'denormalized' in r
                    assert 'winner' in r
                    assert 'diff_ms' in r
            except ImportError:
                pytest.skip('performance module not available')

    def test_benchmark_timing_keys(self, app):
        with app.app_context():
            try:
                from performance.benchmarks.query_benchmarks import run_benchmark, \
                    normalized_get_all_items
                result = run_benchmark(normalized_get_all_items, iterations=3)
                assert 'avg_ms' in result
                assert 'min_ms' in result
                assert 'max_ms' in result
                assert 'result_count' in result
                assert result['avg_ms'] >= 0
                assert result['min_ms'] <= result['avg_ms']
                assert result['max_ms'] >= result['avg_ms']
            except ImportError:
                pytest.skip('performance module not available')

    def test_winner_is_valid_value(self, app):
        with app.app_context():
            try:
                from performance.benchmarks.query_benchmarks import run_all_benchmarks
                results = run_all_benchmarks()
                valid_winners = {'normalized', 'denormalized', 'tie', 'error'}
                for r in results:
                    assert r['winner'] in valid_winners
            except ImportError:
                pytest.skip('performance module not available')

    def test_diff_ms_is_non_negative(self, app):
        with app.app_context():
            try:
                from performance.benchmarks.query_benchmarks import run_all_benchmarks
                results = run_all_benchmarks()
                for r in results:
                    assert r['diff_ms'] >= 0
            except ImportError:
                pytest.skip('performance module not available')


# ── QUERY PERFORMANCE TESTS ───────────────────────────────────────────────────

class TestQueryPerformance:
    """Compare actual query times between schemas"""

    def test_get_all_items_completes_under_500ms(self, db, category):
        seed_normalized(db, category, n=100)
        elapsed = time_query(
            lambda: db.session.query(Item).all()
        )
        assert elapsed < 500, f"Query took {elapsed}ms, expected < 500ms"

    def test_denorm_get_all_items_completes_under_500ms(self, db):
        seed_denormalized(db, n=100)
        elapsed = time_query(
            lambda: db.session.query(ItemDenorm).all()
        )
        assert elapsed < 500, f"Query took {elapsed}ms, expected < 500ms"

    def test_normalized_filter_by_category_completes_fast(self, db, category):
        seed_normalized(db, category, n=50)
        elapsed = time_query(
            lambda: db.session.query(Item)
                .join(Item.category)
                .filter(Category.category_name == 'Electronics')
                .all()
        )
        assert elapsed < 500

    def test_denorm_filter_by_category_completes_fast(self, db):
        seed_denormalized(db, n=50)
        elapsed = time_query(
            lambda: db.session.query(ItemDenorm)
                .filter(ItemDenorm.category_name == 'Electronics')
                .all()
        )
        assert elapsed < 500

    def test_aggregation_query_completes_fast(self, db, category):
        seed_normalized(db, category, n=50)
        elapsed = time_query(
            lambda: db.session.query(
                func.sum(Item.current_stock * Item.unit_price)
            ).scalar()
        )
        assert elapsed < 500

    def test_denorm_aggregation_completes_fast(self, db):
        seed_denormalized(db, n=50)
        elapsed = time_query(
            lambda: db.session.query(
                func.sum(ItemDenorm.current_stock * ItemDenorm.unit_price)
            ).scalar()
        )
        assert elapsed < 500


# ── WRITE PERFORMANCE TESTS ───────────────────────────────────────────────────

class TestWritePerformance:

    def test_bulk_insert_normalized_completes_fast(self, db, category):
        start = time.perf_counter()
        items = [
            Item(
                item_code=f'BULK-N-{i:04d}',
                item_name=f'Bulk Item {i}',
                category_id=category.category_id,
                unit_price=10.00,
                current_stock=100,
                reorder_level=10
            ) for i in range(50)
        ]
        db.session.bulk_save_objects(items)
        db.session.commit()
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 2000, f"Bulk insert took {elapsed}ms"

    def test_bulk_insert_denormalized_completes_fast(self, db):
        start = time.perf_counter()
        items = [
            ItemDenorm(
                item_code=f'BULK-D-{i:04d}',
                item_name=f'Bulk Denorm Item {i}',
                category_name='Electronics',
                unit_price=10.00,
                current_stock=100,
                reorder_level=10
            ) for i in range(50)
        ]
        db.session.bulk_save_objects(items)
        db.session.commit()
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 2000, f"Bulk insert took {elapsed}ms"

    def test_single_item_insert_normalized(self, db, category):
        start = time.perf_counter()
        item = Item(
            item_code='SINGLE-N-001',
            item_name='Single Insert Test',
            category_id=category.category_id,
            unit_price=99.99,
            current_stock=50,
            reorder_level=5
        )
        db.session.add(item)
        db.session.commit()
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 500

    def test_single_item_insert_denormalized(self, db):
        start = time.perf_counter()
        item = ItemDenorm(
            item_code='SINGLE-D-001',
            item_name='Single Denorm Insert Test',
            category_name='Electronics',
            unit_price=99.99,
            current_stock=50,
            reorder_level=5
        )
        db.session.add(item)
        db.session.commit()
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 500
