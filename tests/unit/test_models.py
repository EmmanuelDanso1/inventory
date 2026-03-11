"""
Unit tests for SQLAlchemy models
Tests model properties, constraints, and relationships
"""

import pytest
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.supplier import Supplier
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.transaction_type import TransactionType


# ── CATEGORY MODEL ────────────────────────────────────────────────────────────

class TestCategoryModel:

    def test_create_category(self, db):
        cat = Category(category_name='Furniture', description='Office furniture')
        db.session.add(cat)
        db.session.commit()
        assert cat.category_id is not None
        assert cat.category_name == 'Furniture'
        assert cat.created_at is not None

    def test_category_repr(self, db):
        cat = Category(category_name='Tools')
        assert 'Tools' in repr(cat)

    def test_category_unique_name(self, db, category):
        duplicate = Category(category_name='Electronics')
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_category_items_relationship(self, db, item, category):
        assert item in category.items


# ── SUPPLIER MODEL ────────────────────────────────────────────────────────────

class TestSupplierModel:

    def test_create_supplier(self, db):
        sup = Supplier(
            supplier_name='New Supplier',
            email='new@supplier.com',
            phone='0987654321'
        )
        db.session.add(sup)
        db.session.commit()
        assert sup.supplier_id is not None
        assert sup.supplier_name == 'New Supplier'

    def test_supplier_repr(self, db, supplier):
        assert 'Test Supplier' in repr(supplier)

    def test_supplier_optional_fields(self, db):
        sup = Supplier(supplier_name='Minimal Supplier')
        db.session.add(sup)
        db.session.commit()
        assert sup.contact_person is None
        assert sup.email is None
        assert sup.phone is None


# ── ITEM MODEL ────────────────────────────────────────────────────────────────

class TestItemModel:

    def test_create_item(self, db, category):
        item = Item(
            item_code='NEW-001',
            item_name='New Item',
            category_id=category.category_id,
            unit_price=49.99,
            current_stock=100,
            reorder_level=10
        )
        db.session.add(item)
        db.session.commit()
        assert item.item_id is not None
        assert item.item_code == 'NEW-001'

    def test_item_repr(self, db, item):
        assert 'ITEM-001' in repr(item)

    def test_is_low_stock_false(self, db, item):
        item.current_stock = 50
        item.reorder_level = 10
        assert item.is_low_stock is False

    def test_is_low_stock_true(self, db, item):
        item.current_stock = 5
        item.reorder_level = 10
        assert item.is_low_stock is True

    def test_is_low_stock_at_reorder_level(self, db, item):
        item.current_stock = 10
        item.reorder_level = 10
        assert item.is_low_stock is True

    def test_is_out_of_stock_false(self, db, item):
        item.current_stock = 5
        assert item.is_out_of_stock is False

    def test_is_out_of_stock_true(self, db, item):
        item.current_stock = 0
        assert item.is_out_of_stock is True

    def test_stock_value(self, db, item):
        item.current_stock = 10
        item.unit_price = 100.00
        assert item.stock_value == 1000.0

    def test_stock_status_in_stock(self, db, item):
        item.current_stock = 50
        item.reorder_level = 10
        assert item.stock_status == 'In Stock'

    def test_stock_status_low_stock(self, db, item):
        item.current_stock = 5
        item.reorder_level = 10
        assert item.stock_status == 'Low Stock'

    def test_stock_status_out_of_stock(self, db, item):
        item.current_stock = 0
        assert item.stock_status == 'Out of Stock'

    def test_item_unique_code(self, db, category, item):
        duplicate = Item(
            item_code='ITEM-001',
            item_name='Duplicate',
            category_id=category.category_id,
            unit_price=10.00
        )
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_item_category_relationship(self, db, item, category):
        assert item.category.category_name == 'Electronics'

    def test_item_supplier_relationship(self, db, item, supplier):
        assert item.supplier.supplier_name == 'Test Supplier'

    def test_item_default_stock(self, db, category):
        item = Item(
            item_code='DEFAULT-001',
            item_name='Default Stock Item',
            category_id=category.category_id,
            unit_price=10.00
        )
        db.session.add(item)
        db.session.commit()
        assert item.current_stock == 0
        assert item.reorder_level == 10


# ── TRANSACTION MODEL ─────────────────────────────────────────────────────────

class TestTransactionModel:

    def test_create_transaction(self, db, item, transaction_types):
        t = Transaction(
            item_id=item.item_id,
            type_id=transaction_types['STOCK_IN'].type_id,
            quantity=10,
            unit_price=500.00
        )
        db.session.add(t)
        db.session.commit()
        assert t.transaction_id is not None
        assert t.quantity == 10

    def test_transaction_total_value(self, db, item, transaction_types):
        t = Transaction(
            item_id=item.item_id,
            type_id=transaction_types['STOCK_IN'].type_id,
            quantity=5,
            unit_price=200.00
        )
        db.session.add(t)
        db.session.commit()
        assert t.total_value == 1000.0

    def test_transaction_total_value_no_price(self, db, item, transaction_types):
        t = Transaction(
            item_id=item.item_id,
            type_id=transaction_types['STOCK_OUT'].type_id,
            quantity=5
        )
        db.session.add(t)
        db.session.commit()
        assert t.total_value == 0.0

    def test_transaction_formatted_date(self, db, stock_in_transaction):
        assert '-' in stock_in_transaction.formatted_date
        assert ':' in stock_in_transaction.formatted_date

    def test_transaction_item_relationship(self, db, stock_in_transaction, item):
        assert stock_in_transaction.item.item_name == item.item_name

    def test_transaction_type_relationship(self, db, stock_in_transaction):
        assert stock_in_transaction.transaction_type.type_name == 'STOCK_IN'

    def test_transaction_repr(self, db, stock_in_transaction):
        assert 'STOCK_IN' in repr(stock_in_transaction)


# ── TRANSACTION TYPE MODEL ────────────────────────────────────────────────────

class TestTransactionTypeModel:

    def test_create_transaction_type(self, db):
        t = TransactionType(type_name='RETURN')
        db.session.add(t)
        db.session.commit()
        assert t.type_id is not None
        assert t.type_name == 'RETURN'

    def test_standard_types_exist(self, db, transaction_types):
        assert transaction_types['STOCK_IN'].type_name == 'STOCK_IN'
        assert transaction_types['STOCK_OUT'].type_name == 'STOCK_OUT'
        assert transaction_types['ADJUSTMENT'].type_name == 'ADJUSTMENT'
