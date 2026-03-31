"""
Seed routes - Generate randomized sample data.

Changes vs original:
  - Added seed_denormalized() route: mirrors normalized data into
    items_denormalized and transactions_denormalized tables.
    This is the CRITICAL fix: benchmarks were comparing against empty tables.
  - Added RANDOM_SEED constant for reproducibility (spec requirement).
  - Items cap raised to 10,000; transactions to 50,000 to support
    small / medium / large scale testing.
  - Transactions spread across 90-day window for temporal realism.
  - Denormalized clear route added.
"""

import random
from datetime import datetime, timedelta
from faker import Faker
from flask import Blueprint, request, redirect, url_for, flash
from invent_app import db
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.supplier import Supplier
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.transaction_type import TransactionType
from invent_app.models.denormalized.item_denorm import ItemDenorm
from invent_app.models.denormalized.transaction_denorm import TransactionDenorm

bp = Blueprint('seed', __name__)

# Fixed seed guarantees reproducible data distributions across runs (spec requirement)
RANDOM_SEED = 42
fake = Faker()
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

CATEGORY_NAMES = [
    ('Electronics',        'Electronic devices and components'),
    ('Office Supplies',    'Office furniture and stationery'),
    ('Hardware',           'Tools and hardware items'),
    ('Clothing',           'Apparel and accessories'),
    ('Food & Beverage',    'Consumables and drinks'),
    ('Furniture',          'Home and office furniture'),
    ('Sports & Fitness',   'Sporting goods and equipment'),
    ('Automotive',         'Vehicle parts and accessories'),
    ('Medical',            'Medical supplies and equipment'),
    ('Books & Stationery', 'Books, pens, and paper products'),
    ('Toys & Games',       'Children toys and board games'),
    ('Cleaning Supplies',  'Cleaning products and equipment'),
    ('Lighting',           'Bulbs, lamps, and fixtures'),
    ('Networking',         'Routers, cables, and switches'),
    ('Software',           'Licenses and subscriptions'),
]

ITEM_NAMES_BY_CATEGORY = {
    'Electronics':        ['Laptop', 'Monitor', 'Keyboard', 'Mouse', 'Webcam', 'Headphones',
                           'USB Hub', 'SSD Drive', 'RAM Module', 'Graphics Card', 'Tablet', 'Smartphone'],
    'Office Supplies':    ['Stapler', 'Printer Paper', 'Ballpoint Pen', 'Highlighter',
                           'Sticky Notes', 'Binder', 'File Folder', 'Whiteboard', 'Desk Organizer'],
    'Hardware':           ['Hammer', 'Screwdriver Set', 'Power Drill', 'Wrench', 'Tape Measure',
                           'Level Tool', 'Nail Gun', 'Safety Goggles', 'Work Gloves'],
    'Clothing':           ['T-Shirt', 'Polo Shirt', 'Work Trousers', 'Safety Boots', 'High-Vis Vest',
                           'Jacket', 'Cap', 'Gloves', 'Socks Pack'],
    'Food & Beverage':    ['Coffee Beans', 'Tea Bags', 'Water Bottles', 'Snack Bars',
                           'Sugar Sachets', 'Milk Carton', 'Juice Pack', 'Instant Noodles'],
    'Furniture':          ['Office Chair', 'Standing Desk', 'Filing Cabinet', 'Bookshelf',
                           'Sofa', 'Coffee Table', 'Storage Unit', 'Whiteboard Stand'],
    'Sports & Fitness':   ['Yoga Mat', 'Dumbbells', 'Resistance Bands', 'Jump Rope',
                           'Water Bottle', 'Gym Bag', 'Training Gloves', 'Foam Roller'],
    'Automotive':         ['Engine Oil', 'Car Battery', 'Wiper Blades', 'Brake Pads',
                           'Air Filter', 'Spark Plugs', 'Tyre Pressure Gauge'],
    'Medical':            ['First Aid Kit', 'Gloves Box', 'Face Masks', 'Hand Sanitiser',
                           'Bandages Roll', 'Thermometer', 'Blood Pressure Monitor'],
    'Books & Stationery': ['Notebook', 'Planner', 'Textbook', 'Marker Set',
                           'Correction Fluid', 'Ruler', 'Calculator', 'Scissors'],
    'Toys & Games':       ['Building Blocks', 'Board Game', 'Puzzle Set', 'Action Figure',
                           'Remote Control Car', 'Art Kit', 'Card Game'],
    'Cleaning Supplies':  ['Mop', 'Broom', 'Cleaning Spray', 'Disinfectant',
                           'Rubbish Bags', 'Sponge Pack', 'Floor Polish'],
    'Lighting':           ['LED Bulb', 'Desk Lamp', 'Ceiling Light', 'Flood Light',
                           'Strip Light', 'Motion Sensor Light', 'Solar Light'],
    'Networking':         ['Router', 'Switch', 'Ethernet Cable', 'Patch Panel',
                           'Network Card', 'Wi-Fi Extender', 'Fiber Optic Cable'],
    'Software':           ['Antivirus License', 'Office Suite', 'Design Tool', 'Accounting Software',
                           'Project Management Tool', 'VPN Subscription', 'Cloud Storage'],
}


def _get_or_create_transaction_types():
    types = {}
    for name in ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']:
        t = db.session.query(TransactionType).filter_by(type_name=name).first()
        if not t:
            t = TransactionType(type_name=name)
            db.session.add(t)
    db.session.flush()
    for name in ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']:
        types[name] = db.session.query(TransactionType).filter_by(type_name=name).first()
    return types


# ---------------------------------------------------------------------------
# Normalized seeding
# ---------------------------------------------------------------------------

@bp.route('/seed/categories', methods=['POST'])
def seed_categories():
    count = request.form.get('count', 15, type=int)
    count = min(count, 500)

    existing_names = {c.category_name for c in db.session.query(Category).all()}
    available = [(n, d) for n, d in CATEGORY_NAMES if n not in existing_names]

    added = 0
    for name, desc in available[:count]:
        db.session.add(Category(category_name=name, description=desc))
        added += 1

    while added < count:
        name = f'{fake.word().capitalize()} {fake.word().capitalize()} Supplies'
        if name not in existing_names:
            db.session.add(Category(category_name=name, description=fake.sentence()))
            existing_names.add(name)
            added += 1

    db.session.commit()
    flash(f'Generated {added} categories.', 'success')
    return redirect(url_for('categories.list'))


@bp.route('/seed/suppliers', methods=['POST'])
def seed_suppliers():
    count = request.form.get('count', 20, type=int)
    count = min(count, 500)

    for _ in range(count):
        db.session.add(Supplier(
            supplier_name=fake.company(),
            contact_person=fake.name(),
            email=fake.company_email(),
            phone=fake.phone_number()[:20],
            address=fake.address()
        ))

    db.session.commit()
    flash(f'Generated {count} suppliers.', 'success')
    return redirect(url_for('suppliers.list'))


@bp.route('/seed/items', methods=['POST'])
def seed_items():
    count = request.form.get('count', 200, type=int)
    count = min(count, 10000)

    categories = db.session.query(Category).all()
    suppliers  = db.session.query(Supplier).all()

    if not categories:
        flash('Generate some categories first.', 'danger')
        return redirect(url_for('items.list'))

    existing_codes = {i.item_code for i in db.session.query(Item.item_code).all()}

    added = 0
    attempts = 0
    while added < count and attempts < count * 3:
        attempts += 1
        category  = random.choice(categories)
        cat_name  = category.category_name
        name_pool = ITEM_NAMES_BY_CATEGORY.get(cat_name, [])
        base_name = random.choice(name_pool) if name_pool else fake.word().capitalize()
        brand     = fake.company().split()[0]
        item_name = f'{brand} {base_name}'

        code = f'{cat_name[:3].upper()}-{fake.bothify("###??").upper()}'
        if code in existing_codes:
            continue
        existing_codes.add(code)

        db.session.add(Item(
            item_code=code,
            item_name=item_name,
            description=fake.sentence(),
            category_id=category.category_id,
            supplier_id=random.choice(suppliers).supplier_id if suppliers else None,
            unit_price=round(random.uniform(1.99, 999.99), 2),
            current_stock=random.randint(0, 500),
            reorder_level=random.randint(5, 50)
        ))
        added += 1

    db.session.commit()
    flash(f'Generated {added} items.', 'success')
    return redirect(url_for('items.list'))


@bp.route('/seed/transactions', methods=['POST'])
def seed_transactions():
    count = request.form.get('count', 500, type=int)
    count = min(count, 50000)

    items = db.session.query(Item).all()
    if not items:
        flash('Generate some items first.', 'danger')
        return redirect(url_for('transactions.list'))

    types     = _get_or_create_transaction_types()
    suppliers = db.session.query(Supplier).all()
    base_date = datetime.utcnow()

    for _ in range(count):
        item     = random.choice(items)
        tx_type  = random.choice(['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT'])
        quantity = random.randint(1, 100)

        if tx_type == 'STOCK_IN':
            item.current_stock += quantity
        elif tx_type == 'STOCK_OUT':
            quantity = min(quantity, item.current_stock)
            if quantity == 0:
                quantity = 1
                item.current_stock += 10
            item.current_stock -= quantity
        else:
            adjustment = random.randint(-20, 20)
            item.current_stock = max(0, item.current_stock + adjustment)
            quantity = abs(adjustment) or 1

        tx_date = base_date - timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23)
        )

        db.session.add(Transaction(
            item_id=item.item_id,
            type_id=types[tx_type].type_id,
            quantity=quantity,
            unit_price=float(item.unit_price),
            supplier_id=random.choice(suppliers).supplier_id if suppliers and tx_type == 'STOCK_IN' else None,
            reference_number=f'REF-{fake.bothify("####??").upper()}',
            notes=fake.sentence(),
            transaction_date=tx_date
        ))

    db.session.commit()
    flash(f'Generated {count} transactions.', 'success')
    return redirect(url_for('transactions.list'))


# ---------------------------------------------------------------------------
# Denormalized seeding  -- THE CRITICAL FIX
# ---------------------------------------------------------------------------

@bp.route('/seed/denormalized', methods=['POST'])
def seed_denormalized():
    """
    Mirror all normalized items and transactions into the denormalized tables.
    Must be called AFTER seeding normalized data and BEFORE running benchmarks.
    Both tables must contain identical logical datasets for comparisons to be valid.
    """
    norm_items = db.session.query(Item).all()
    if not norm_items:
        flash('No normalized items found. Seed normalized data first.', 'danger')
        return redirect(url_for('reports.performance'))

    # Wipe existing denormalized data before re-sync
    db.session.query(TransactionDenorm).delete()
    db.session.query(ItemDenorm).delete()
    db.session.commit()

    # Mirror items
    denorm_items = []
    for item in norm_items:
        cat_name    = item.category.category_name  if item.category  else 'Unknown'
        sup_name    = item.supplier.supplier_name  if item.supplier  else ''
        sup_email   = item.supplier.email          if item.supplier  else ''
        sup_phone   = item.supplier.phone          if item.supplier  else ''
        sup_contact = item.supplier.contact_person if item.supplier  else ''

        denorm_items.append(ItemDenorm(
            item_code=item.item_code,
            item_name=item.item_name,
            description=item.description,
            category_name=cat_name,
            supplier_name=sup_name,
            supplier_email=sup_email,
            supplier_phone=sup_phone,
            supplier_contact=sup_contact,
            unit_price=item.unit_price,
            current_stock=item.current_stock,
            reorder_level=item.reorder_level,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ))

    db.session.bulk_save_objects(denorm_items)
    db.session.commit()
    item_count = len(denorm_items)

    # Mirror transactions
    # Build item map to avoid N+1 on the category/supplier lookups
    item_map = {i.item_id: i for i in norm_items}
    norm_txs = db.session.query(Transaction).all()

    denorm_txs = []
    for tx in norm_txs:
        item     = item_map.get(tx.item_id)
        tx_type  = tx.transaction_type.type_name if tx.transaction_type else 'STOCK_IN'
        cat_name = item.category.category_name if item and item.category else ''
        sup_name = item.supplier.supplier_name if item and item.supplier else ''

        denorm_txs.append(TransactionDenorm(
            item_code=item.item_code if item else f'UNKNOWN-{tx.item_id}',
            item_name=item.item_name if item else 'Unknown Item',
            category_name=cat_name,
            supplier_name=sup_name,
            transaction_type=tx_type,
            quantity=tx.quantity,
            unit_price=tx.unit_price,
            reference_number=tx.reference_number,
            notes=tx.notes,
            transaction_date=tx.transaction_date,
            created_by=tx.created_by,
        ))

    db.session.bulk_save_objects(denorm_txs)
    db.session.commit()
    tx_count = len(denorm_txs)

    flash(
        f'Denormalized tables synced: {item_count} items and {tx_count} transactions.',
        'success'
    )
    return redirect(url_for('reports.performance'))


# ---------------------------------------------------------------------------
# Clear routes
# ---------------------------------------------------------------------------

@bp.route('/seed/categories/clear', methods=['POST'])
def clear_categories():
    empty = db.session.query(Category).filter(~Category.items.any()).all()
    count = len(empty)
    for cat in empty:
        db.session.delete(cat)
    db.session.commit()
    flash(f'Deleted {count} empty categories.', 'success')
    return redirect(url_for('categories.list'))


@bp.route('/seed/suppliers/clear', methods=['POST'])
def clear_suppliers():
    empty = db.session.query(Supplier).filter(~Supplier.items.any()).all()
    count = len(empty)
    for sup in empty:
        db.session.delete(sup)
    db.session.commit()
    flash(f'Deleted {count} unlinked suppliers.', 'success')
    return redirect(url_for('suppliers.list'))


@bp.route('/seed/items/clear', methods=['POST'])
def clear_items():
    items = db.session.query(Item).all()
    count = len(items)
    for item in items:
        for t in item.transactions:
            db.session.delete(t)
        db.session.delete(item)
    db.session.commit()
    flash(f'Deleted {count} items and their transactions.', 'success')
    return redirect(url_for('items.list'))


@bp.route('/seed/transactions/clear', methods=['POST'])
def clear_transactions():
    count = db.session.query(Transaction).count()
    db.session.query(Transaction).delete()
    db.session.commit()
    flash(f'Deleted {count} transactions.', 'success')
    return redirect(url_for('transactions.list'))


@bp.route('/seed/denormalized/clear', methods=['POST'])
def clear_denormalized():
    item_count = db.session.query(ItemDenorm).count()
    tx_count   = db.session.query(TransactionDenorm).count()
    db.session.query(TransactionDenorm).delete()
    db.session.query(ItemDenorm).delete()
    db.session.commit()
    flash(f'Cleared denormalized tables: {item_count} items, {tx_count} transactions.', 'success')
    return redirect(url_for('reports.performance'))
