"""
Integration tests for database operations
Tests relationships, constraints, cascades, and complex queries
"""

import pytest
from sqlalchemy import func
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.supplier import Supplier
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.transaction_type import TransactionType


class TestDatabaseConstraints:

    def test_item_requires_category(self, db):
        item = Item(
            item_code='NO-CAT',
            item_name='No Category Item',
            unit_price=10.00
        )
        db.session.add(item)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_item_requires_positive_price(self, db, category):
        item = Item(
            item_code='NEG-PRICE',
            item_name='Negative Price',
            category_id=category.category_id,
            unit_price=-10.00
        )
        db.session.add(item)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_transaction_requires_positive_quantity(self, db, item, transaction_types):
        t = Transaction(
            item_id=item.item_id,
            type_id=transaction_types['STOCK_IN'].type_id,
            quantity=-5
        )
        db.session.add(t)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_item_code_must_be_unique(self, db, category, item):
        duplicate = Item(
            item_code='ITEM-001',
            item_name='Duplicate Code',
            category_id=category.category_id,
            unit_price=50.00
        )
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


class TestDatabaseRelationships:

    def test_item_belongs_to_category(self, db, item, category):
        assert item.category_id == category.category_id
        assert item.category.category_name == 'Electronics'

    def test_category_has_many_items(self, db, category):
        items = [
            Item(item_code=f'CAT-{i}', item_name=f'Item {i}',
                 category_id=category.category_id,
                 unit_price=10.00, current_stock=10, reorder_level=2)
            for i in range(3)
        ]
        db.session.add_all(items)
        db.session.commit()
        assert category.items.count() == 3

    def test_transaction_belongs_to_item(self, db, stock_in_transaction, item):
        assert stock_in_transaction.item_id == item.item_id

    def test_item_has_many_transactions(self, db, item, transaction_types):
        for i in range(3):
            t = Transaction(
                item_id=item.item_id,
                type_id=transaction_types['STOCK_IN'].type_id,
                quantity=5
            )
            db.session.add(t)
        db.session.commit()
        assert item.transactions.count() == 3

    def test_supplier_has_many_items(self, db, category, supplier):
        items = [
            Item(item_code=f'SUP-{i}', item_name=f'Supplier Item {i}',
                 category_id=category.category_id,
                 supplier_id=supplier.supplier_id,
                 unit_price=10.00)
            for i in range(2)
        ]
        db.session.add_all(items)
        db.session.commit()
        assert supplier.items.count() == 2


class TestComplexQueries:

    def test_stock_summary_by_category(self, db, category):
        items = [
            Item(item_code=f'SUM-{i}', item_name=f'Sum Item {i}',
                 category_id=category.category_id,
                 unit_price=100.00, current_stock=10, reorder_level=2)
            for i in range(3)
        ]
        db.session.add_all(items)
        db.session.commit()

        result = db.session.query(
            Category.category_name,
            func.count(Item.item_id).label('item_count'),
            func.sum(Item.current_stock * Item.unit_price).label('total_value')
        ).join(Item, Category.category_id == Item.category_id)\
         .filter(Category.category_id == category.category_id)\
         .group_by(Category.category_id, Category.category_name)\
         .first()

        assert result.category_name == 'Electronics'
        assert result.item_count == 3
        assert float(result.total_value) == 3000.0

    def test_transactions_ordered_by_date_desc(self, db, item, transaction_types):
        for i in range(3):
            t = Transaction(
                item_id=item.item_id,
                type_id=transaction_types['STOCK_IN'].type_id,
                quantity=i + 1
            )
            db.session.add(t)
        db.session.commit()

        transactions = db.session.query(Transaction)\
            .order_by(Transaction.transaction_date.desc()).all()

        dates = [t.transaction_date for t in transactions]
        assert dates == sorted(dates, reverse=True)

    def test_stock_in_total_by_item(self, db, item, transaction_types):
        for qty in [10, 20, 30]:
            t = Transaction(
                item_id=item.item_id,
                type_id=transaction_types['STOCK_IN'].type_id,
                quantity=qty
            )
            db.session.add(t)
        db.session.commit()

        total = db.session.query(func.sum(Transaction.quantity))\
            .join(Transaction.transaction_type)\
            .filter(TransactionType.type_name == 'STOCK_IN')\
            .filter(Transaction.item_id == item.item_id)\
            .scalar()

        assert total == 60

    def test_pagination(self, db, category):
        items = [
            Item(item_code=f'PAG-{i:03d}', item_name=f'Page Item {i}',
                 category_id=category.category_id,
                 unit_price=10.00)
            for i in range(25)
        ]
        db.session.add_all(items)
        db.session.commit()

        page1 = db.session.query(Item)\
            .filter(Item.item_code.like('PAG-%'))\
            .order_by(Item.item_name)\
            .limit(20).offset(0).all()

        page2 = db.session.query(Item)\
            .filter(Item.item_code.like('PAG-%'))\
            .order_by(Item.item_name)\
            .limit(20).offset(20).all()

        assert len(page1) == 20
        assert len(page2) == 5
