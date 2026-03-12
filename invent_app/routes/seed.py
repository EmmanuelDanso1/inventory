"""
Seed routes - Generate randomized sample data
"""

import random
from faker import Faker
from flask import Blueprint, request, redirect, url_for, flash
from invent_app import db
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.supplier import Supplier
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.transaction_type import TransactionType

bp = Blueprint('seed', __name__)
fake = Faker()

CATEGORY_NAMES = [
    ('Electronics', 'Electronic devices and components'),
    ('Office Supplies', 'Office furniture and stationery'),
    ('Hardware', 'Tools and hardware items'),
    ('Clothing', 'Apparel and accessories'),
    ('Food & Beverage', 'Consumables and drinks'),
    ('Furniture', 'Home and office furniture'),
    ('Sports & Fitness', 'Sporting goods and equipment'),
    ('Automotive', 'Vehicle parts and accessories'),
    ('Medical', 'Medical supplies and equipment'),
    ('Books & Stationery', 'Books, pens, and paper products'),
    ('Toys & Games', 'Children toys and board games'),
    ('Cleaning Supplies', 'Cleaning products and equipment'),
    ('Lighting', 'Bulbs, lamps, and fixtures'),
    ('Networking', 'Routers, cables, and switches'),
    ('Software', 'Licenses and subscriptions'),
]

ITEM_NAMES_BY_CATEGORY = {
    'Electronics': ['Laptop', 'Monitor', 'Keyboard', 'Mouse', 'Webcam', 'Headphones',
                    'USB Hub', 'SSD Drive', 'RAM Module', 'Graphics Card', 'Tablet', 'Smartphone'],
    'Office Supplies': ['Stapler', 'Printer Paper', 'Ballpoint Pen', 'Highlighter',
                        'Sticky Notes', 'Binder', 'File Folder', 'Whiteboard', 'Desk Organizer'],
    'Hardware': ['Hammer', 'Screwdriver Set', 'Power Drill', 'Wrench', 'Tape Measure',
                 'Level Tool', 'Nail Gun', 'Safety Goggles', 'Work Gloves'],
    'Clothing': ['T-Shirt', 'Polo Shirt', 'Work Trousers', 'Safety Boots', 'High-Vis Vest',
                 'Jacket', 'Cap', 'Gloves', 'Socks Pack'],
    'Food & Beverage': ['Coffee Beans', 'Tea Bags', 'Water Bottles', 'Snack Bars',
                        'Sugar Sachets', 'Milk Carton', 'Juice Pack', 'Instant Noodles'],
    'Furniture': ['Office Chair', 'Standing Desk', 'Filing Cabinet', 'Bookshelf',
                  'Sofa', 'Coffee Table', 'Storage Unit', 'Whiteboard Stand'],
    'Sports & Fitness': ['Yoga Mat', 'Dumbbells', 'Resistance Bands', 'Jump Rope',
                         'Water Bottle', 'Gym Bag', 'Training Gloves', 'Foam Roller'],
    'Automotive': ['Engine Oil', 'Car Battery', 'Wiper Blades', 'Brake Pads',
                   'Air Filter', 'Spark Plugs', 'Tyre Pressure Gauge'],
    'Medical': ['First Aid Kit', 'Gloves Box', 'Face Masks', 'Hand Sanitiser',
                'Bandages Roll', 'Thermometer', 'Blood Pressure Monitor'],
    'Books & Stationery': ['Notebook', 'Planner', 'Textbook', 'Marker Set',
                           'Correction Fluid', 'Ruler', 'Calculator', 'Scissors'],
    'Toys & Games': ['Building Blocks', 'Board Game', 'Puzzle Set', 'Action Figure',
                     'Remote Control Car', 'Art Kit', 'Card Game'],
    'Cleaning Supplies': ['Mop', 'Broom', 'Cleaning Spray', 'Disinfectant',
                          'Rubbish Bags', 'Sponge Pack', 'Floor Polish'],
    'Lighting': ['LED Bulb', 'Desk Lamp', 'Ceiling Light', 'Flood Light',
                 'Strip Light', 'Motion Sensor Light', 'Solar Light'],
    'Networking': ['Router', 'Switch', 'Ethernet Cable', 'Patch Panel',
                   'Network Card', 'Wi-Fi Extender', 'Fiber Optic Cable'],
    'Software': ['Antivirus License', 'Office Suite', 'Design Tool', 'Accounting Software',
                 'Project Management Tool', 'VPN Subscription', 'Cloud Storage'],
}


def get_or_create_transaction_types():
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


@bp.route('/seed/categories', methods=['POST'])
def seed_categories():
    count = request.form.get('count', 10, type=int)
    count = min(count, 500)

    existing_names = {c.category_name for c in db.session.query(Category).all()}
    available = [(n, d) for n, d in CATEGORY_NAMES if n not in existing_names]

    added = 0
    # First add from predefined list
    for name, desc in available[:count]:
        db.session.add(Category(category_name=name, description=desc))
        added += 1

    # If more needed, generate with faker
    while added < count:
        name = f'{fake.word().capitalize()} {fake.word().capitalize()} Supplies'
        if name not in existing_names:
            db.session.add(Category(
                category_name=name,
                description=fake.sentence()
            ))
            existing_names.add(name)
            added += 1

    db.session.commit()
    flash(f'Successfully generated {added} categories!', 'success')
    return redirect(url_for('categories.list'))


@bp.route('/seed/suppliers', methods=['POST'])
def seed_suppliers():
    count = request.form.get('count', 10, type=int)
    count = min(count, 500)

    for _ in range(count):
        company = fake.company()
        db.session.add(Supplier(
            supplier_name=company,
            contact_person=fake.name(),
            email=fake.company_email(),
            phone=fake.phone_number()[:20],
            address=fake.address()
        ))

    db.session.commit()
    flash(f'Successfully generated {count} suppliers!', 'success')
    return redirect(url_for('suppliers.list'))


@bp.route('/seed/items', methods=['POST'])
def seed_items():
    count = request.form.get('count', 50, type=int)
    count = min(count, 2000)

    categories = db.session.query(Category).all()
    suppliers = db.session.query(Supplier).all()

    if not categories:
        flash('Please generate some categories first!', 'danger')
        return redirect(url_for('items.list'))

    # Get existing item codes to avoid duplicates
    existing_codes = {i.item_code for i in db.session.query(Item.item_code).all()}

    added = 0
    attempts = 0
    while added < count and attempts < count * 3:
        attempts += 1
        category = random.choice(categories)
        cat_name = category.category_name

        # Pick item name from category or generate one
        name_pool = ITEM_NAMES_BY_CATEGORY.get(cat_name, [])
        if name_pool:
            base_name = random.choice(name_pool)
            brand = fake.company().split()[0]
            item_name = f'{brand} {base_name}'
        else:
            item_name = f'{fake.word().capitalize()} {fake.word().capitalize()}'

        # Generate unique item code
        code = f'{cat_name[:3].upper()}-{fake.bothify("###??").upper()}'
        if code in existing_codes:
            continue
        existing_codes.add(code)

        current_stock = random.randint(0, 500)
        reorder_level = random.randint(5, 50)
        unit_price = round(random.uniform(1.99, 999.99), 2)

        item = Item(
            item_code=code,
            item_name=item_name,
            description=fake.sentence(),
            category_id=category.category_id,
            supplier_id=random.choice(suppliers).supplier_id if suppliers else None,
            unit_price=unit_price,
            current_stock=current_stock,
            reorder_level=reorder_level
        )
        db.session.add(item)
        added += 1

    db.session.commit()
    flash(f'Successfully generated {added} items!', 'success')
    return redirect(url_for('items.list'))


@bp.route('/seed/transactions', methods=['POST'])
def seed_transactions():
    count = request.form.get('count', 100, type=int)
    count = min(count, 5000)

    items = db.session.query(Item).all()
    if not items:
        flash('Please generate some items first!', 'danger')
        return redirect(url_for('transactions.list'))

    types = get_or_create_transaction_types()
    suppliers = db.session.query(Supplier).all()

    for _ in range(count):
        item = random.choice(items)
        tx_type = random.choice(['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT'])
        quantity = random.randint(1, 100)

        # Update stock levels realistically
        if tx_type == 'STOCK_IN':
            item.current_stock += quantity
        elif tx_type == 'STOCK_OUT':
            quantity = min(quantity, item.current_stock)
            if quantity == 0:
                quantity = 1
                item.current_stock += 10  # restock first
            item.current_stock -= quantity
        else:  # ADJUSTMENT
            adjustment = random.randint(-20, 20)
            item.current_stock = max(0, item.current_stock + adjustment)
            quantity = abs(adjustment) or 1

        t = Transaction(
            item_id=item.item_id,
            type_id=types[tx_type].type_id,
            quantity=quantity,
            unit_price=float(item.unit_price),
            supplier_id=random.choice(suppliers).supplier_id if suppliers and tx_type == 'STOCK_IN' else None,
            reference_number=f'REF-{fake.bothify("####??").upper()}',
            notes=fake.sentence()
        )
        db.session.add(t)

    db.session.commit()
    flash(f'Successfully generated {count} transactions!', 'success')
    return redirect(url_for('transactions.list'))


#Autodeletion

@bp.route('/seed/categories/clear', methods=['POST'])
def clear_categories():
    # Only delete categories with no items
    empty = db.session.query(Category).filter(~Category.items.any()).all()
    count = len(empty)
    for cat in empty:
        db.session.delete(cat)
    db.session.commit()
    flash(f'Deleted {count} empty categories.', 'success')
    return redirect(url_for('categories.list'))


@bp.route('/seed/suppliers/clear', methods=['POST'])
def clear_suppliers():
    # Only delete suppliers with no items
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