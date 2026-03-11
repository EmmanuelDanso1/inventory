"""
Integration tests for Flask routes
Tests HTTP responses, redirects, and flash messages
"""

import pytest
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.supplier import Supplier
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.transaction_type import TransactionType


# ── ITEM ROUTES ───────────────────────────────────────────────────────────────

class TestItemRoutes:

    def test_items_list_page_loads(self, client, db, category):
        response = client.get('/items/')
        assert response.status_code == 200

    def test_items_list_shows_item(self, client, db, item):
        response = client.get('/items/')
        assert b'Test Laptop' in response.data

    def test_items_list_search(self, client, db, item):
        response = client.get('/items/?search=laptop')
        assert response.status_code == 200
        assert b'Test Laptop' in response.data

    def test_items_list_search_no_results(self, client, db, item):
        response = client.get('/items/?search=zzznomatch')
        assert response.status_code == 200
        assert b'Test Laptop' not in response.data

    def test_item_detail_page_loads(self, client, db, item):
        response = client.get(f'/items/{item.item_id}')
        assert response.status_code == 200
        assert b'Test Laptop' in response.data

    def test_item_detail_not_found(self, client, db):
        response = client.get('/items/99999')
        assert response.status_code == 302  # redirect

    def test_item_create_page_loads(self, client, db, category):
        response = client.get('/items/create')
        assert response.status_code == 200

    def test_item_create_post(self, client, db, category):
        response = client.post('/items/create', data={
            'item_code': 'NEW-001',
            'item_name': 'New Test Item',
            'category_id': category.category_id,
            'unit_price': '29.99',
            'current_stock': '100',
            'reorder_level': '10',
            'supplier_id': '0',
            'location_id': '0',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'New Test Item' in response.data

    def test_item_edit_page_loads(self, client, db, item):
        response = client.get(f'/items/{item.item_id}/edit')
        assert response.status_code == 200
        assert b'Test Laptop' in response.data

    def test_item_edit_post(self, client, db, item, category):
        response = client.post(f'/items/{item.item_id}/edit', data={
            'item_code': 'ITEM-001',
            'item_name': 'Updated Laptop',
            'category_id': category.category_id,
            'unit_price': '1099.99',
            'current_stock': '50',
            'reorder_level': '10',
            'supplier_id': '0',
            'location_id': '0',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_item_delete(self, client, db, item):
        item_id = item.item_id
        response = client.post(f'/items/{item_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        deleted = db.session.get(Item, item_id)
        assert deleted is None

    def test_item_delete_not_found(self, client, db):
        response = client.post('/items/99999/delete', follow_redirects=True)
        assert response.status_code == 200


# ── CATEGORY ROUTES ───────────────────────────────────────────────────────────

class TestCategoryRoutes:

    def test_categories_list_loads(self, client, category):
        response = client.get('/categories/')
        assert response.status_code == 200
        assert b'Electronics' in response.data

    def test_category_delete_with_items_blocked(self, client, db, category, item):
        response = client.post(
            f'/categories/{category.category_id}/delete',
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Electronics' in response.data

    def test_category_delete_empty_category(self, client, db):
        cat = Category(category_name='Empty Category')
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.category_id

        response = client.post(
            f'/categories/{cat_id}/delete',
            data={'csrf_token': 'test'},
            follow_redirects=True
        )
        assert response.status_code == 200

        # Query fresh from database
        result = db.session.execute(
            db.select(Category).where(Category.category_id == cat_id)
        ).scalar_one_or_none()
        assert result is None

# ── TRANSACTION ROUTES ────────────────────────────────────────────────────────

class TestTransactionRoutes:

    def test_transactions_list_loads(self, client, db):
        response = client.get('/transactions/')
        assert response.status_code == 200

    def test_stock_in_page_loads(self, client, db, item):
        response = client.get('/transactions/stock-in')
        assert response.status_code == 200

    def test_stock_out_page_loads(self, client, db, item):
        response = client.get('/transactions/stock-out')
        assert response.status_code == 200

    def test_stock_in_post(self, client, db, item, transaction_types):
        initial_stock = item.current_stock
        item_id = item.item_id

        response = client.post('/transactions/stock-in', data={
            'item_id': item_id,
            'quantity': '10',
            'unit_price': '900.00',
            'supplier_id': '0',
            'reference_number': 'REF-001',
            'notes': 'Test stock in',
        }, follow_redirects=True)
        assert response.status_code == 200

        updated_item = db.session.get(Item, item_id)
        assert updated_item.current_stock == initial_stock + 10

    def test_stock_out_insufficient_stock(self, client, db, item, transaction_types):
        item_id = item.item_id
        item.current_stock = 5
        db.session.commit()

        response = client.post('/transactions/stock-out', data={
            'item_id': item_id,
            'quantity': '100',
            'reference_number': 'REF-002',
            'notes': 'Test stock out',
        }, follow_redirects=True)
        assert response.status_code == 200

        updated_item = db.session.get(Item, item_id)
        assert updated_item.current_stock == 5


    def test_transaction_detail_loads(self, client, db, stock_in_transaction):
        response = client.get(f'/transactions/{stock_in_transaction.transaction_id}')
        assert response.status_code == 200

    def test_transaction_detail_not_found(self, client, db):
        response = client.get('/transactions/99999', follow_redirects=True)
        assert response.status_code == 200


# ── REPORT ROUTES ─────────────────────────────────────────────────────────────

class TestReportRoutes:

    def test_stock_levels_loads(self, client, db, item):
        response = client.get('/reports/stock-levels')
        assert response.status_code == 200

    def test_low_stock_loads(self, client, db):
        response = client.get('/reports/low-stock')
        assert response.status_code == 200

    def test_movement_history_loads(self, client, db):
        response = client.get('/reports/movement-history')
        assert response.status_code == 200

    def test_category_summary_loads(self, client, db, category):
        response = client.get('/reports/category-summary')
        assert response.status_code == 200

    def test_inventory_valuation_loads(self, client, db, item):
        response = client.get('/reports/inventory-valuation')
        assert response.status_code == 200

    def test_performance_page_loads(self, client, db):
        response = client.get('/reports/performance')
        assert response.status_code == 200

    def test_dashboard_loads(self, client, db):
        response = client.get('/dashboard')
        assert response.status_code == 200
