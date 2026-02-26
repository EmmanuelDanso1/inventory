from flask import Blueprint, render_template, request, redirect, url_for, flash
from invent_app import db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.category import Category
from invent_app.models.normalized.supplier import Supplier
from invent_app.models.normalized.location import Location
from invent_app.forms.item_forms import ItemForm

bp = Blueprint('items', __name__)


@bp.route('/')
def list():
    """List all items with pagination and search"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    
    query = db.session.query(Item)
    
    # Apply search filter
    if search:
        query = query.filter(
            (Item.item_name.ilike(f'%{search}%')) |
            (Item.item_code.ilike(f'%{search}%'))
        )
    
    # Apply category filter
    if category_id:
        query = query.filter(Item.category_id == category_id)
    
    # Paginate results
    items = query.order_by(Item.item_name).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    # Get all categories for filter dropdown
    categories = db.session.query(Category).order_by(Category.category_name).all()
    
    return render_template(
        'items/list.html',
        items=items,
        categories=categories
    )


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new item"""
    form = ItemForm()
    
    # Populate select fields
    form.category_id.choices = [
        (c.category_id, c.category_name) 
        for c in db.session.query(Category).order_by(Category.category_name).all()
    ]
    form.supplier_id.choices = [(0, 'Select Supplier')] + [
        (s.supplier_id, s.supplier_name)
        for s in db.session.query(Supplier).order_by(Supplier.supplier_name).all()
    ]
    form.location_id.choices = [(0, 'Select Location')] + [
        (l.location_id, f"{l.warehouse} - {l.aisle}/{l.shelf}")
        for l in db.session.query(Location).all()
    ]
    
    if form.validate_on_submit():
        item = Item(
            item_code=form.item_code.data,
            item_name=form.item_name.data,
            description=form.description.data,
            category_id=form.category_id.data,
            supplier_id=form.supplier_id.data if form.supplier_id.data != 0 else None,
            location_id=form.location_id.data if form.location_id.data != 0 else None,
            unit_price=form.unit_price.data,
            current_stock=form.current_stock.data,
            reorder_level=form.reorder_level.data
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash(f'Item "{item.item_name}" created successfully!', 'success')
        return redirect(url_for('items.detail', id=item.item_id))
    
    return render_template('items/create.html', form=form)


@bp.route('/<int:id>')
def detail(id):
    """View item details"""
    item = db.session.get(Item, id)
    if not item:
        flash('Item not found', 'danger')
        return redirect(url_for('items.list'))
    
    return render_template('items/detail.html', item=item)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit item"""
    item = db.session.get(Item, id)
    if not item:
        flash('Item not found', 'danger')
        return redirect(url_for('items.list'))
    
    form = ItemForm(obj=item)
    
    # Populate select fields
    form.category_id.choices = [
        (c.category_id, c.category_name)
        for c in db.session.query(Category).order_by(Category.category_name).all()
    ]
    form.supplier_id.choices = [(0, 'Select Supplier')] + [
        (s.supplier_id, s.supplier_name)
        for s in db.session.query(Supplier).order_by(Supplier.supplier_name).all()
    ]
    form.location_id.choices = [(0, 'Select Location')] + [
        (l.location_id, f"{l.warehouse} - {l.aisle}/{l.shelf}")
        for l in db.session.query(Location).all()
    ]
    
    if form.validate_on_submit():
        item.item_code = form.item_code.data
        item.item_name = form.item_name.data
        item.description = form.description.data
        item.category_id = form.category_id.data
        item.supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        item.location_id = form.location_id.data if form.location_id.data != 0 else None
        item.unit_price = form.unit_price.data
        item.reorder_level = form.reorder_level.data
        
        db.session.commit()
        
        flash(f'Item "{item.item_name}" updated successfully!', 'success')
        return redirect(url_for('items.detail', id=item.item_id))
    
    return render_template('items/edit.html', form=form, item=item)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete item"""
    item = db.session.get(Item, id)
    if not item:
        flash('Item not found', 'danger')
        return redirect(url_for('items.list'))
    
    # Check if item has transactions
    if item.transactions:
        flash('Cannot delete item with existing transactions', 'danger')
        return redirect(url_for('items.detail', id=id))
    
    item_name = item.item_name
    db.session.delete(item)
    db.session.commit()
    
    flash(f'Item "{item_name}" deleted successfully!', 'success')
    return redirect(url_for('items.list'))