"""
Pytest fixtures shared across all tests
"""

import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
import pytest
from invent_app import create_app, db as _db
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.supplier import Supplier
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.transaction_type import TransactionType


@pytest.fixture(scope='session')
def app():
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    }
    app = create_app(test_config=test_config)
    with app.app_context():
        _db.create_all()
        yield app


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def category(db):
    cat = Category(category_name='Electronics', description='Electronic items')
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture(scope='function')
def supplier(db):
    sup = Supplier(
        supplier_name='Test Supplier',
        contact_person='John Doe',
        email='john@test.com',
        phone='1234567890'
    )
    db.session.add(sup)
    db.session.commit()
    return sup


@pytest.fixture(scope='function')
def transaction_types(db):
    types = {}
    for name in ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']:
        t = TransactionType(type_name=name)
        db.session.add(t)
        types[name] = t
    db.session.commit()
    return types


@pytest.fixture(scope='function')
def item(db, category, supplier):
    i = Item(
        item_code='ITEM-001',
        item_name='Test Laptop',
        category_id=category.category_id,
        supplier_id=supplier.supplier_id,
        unit_price=999.99,
        current_stock=50,
        reorder_level=10
    )
    db.session.add(i)
    db.session.commit()
    return i


@pytest.fixture(scope='function')
def stock_in_transaction(db, item, transaction_types):
    t = Transaction(
        item_id=item.item_id,
        type_id=transaction_types['STOCK_IN'].type_id,
        quantity=20,
        unit_price=900.00,
        notes='Initial stock'
    )
    db.session.add(t)
    db.session.commit()
    return t
