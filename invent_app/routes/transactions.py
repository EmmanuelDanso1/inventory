from flask import Blueprint, render_template, request, redirect, url_for, flash
from invent_app import db
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.normalized.transaction_type import TransactionType
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.supplier import Supplier
from invent_app.forms.transaction_forms import StockInForm, StockOutForm

bp = Blueprint('transactions', __name__)


@bp.route('/')
def list():
    """List all transactions"""
    page = request.args.get('page', 1, type=int)
    type_filter = request.args.get('type', '')
    
    query = db.session.query(Transaction)
    
    if type_filter:
        query = query.join(Transaction.transaction_type)\
            .filter(TransactionType.type_name == type_filter)
    
    transactions = query.order_by(Transaction.transaction_date.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('transactions/list.html', transactions=transactions)


@bp.route('/stock-in', methods=['GET', 'POST'])
def stock_in():
    """Record stock in transaction"""
    form = StockInForm()
    
    # Populate item choices
    form.item_id.choices = [
        (i.item_id, f"{i.item_code} - {i.item_name}")
        for i in db.session.query(Item).order_by(Item.item_name).all()
    ]
    
    # Populate supplier choices
    form.supplier_id.choices = [(0, 'Select Supplier')] + [
        (s.supplier_id, s.supplier_name)
        for s in db.session.query(Supplier).order_by(Supplier.supplier_name).all()
    ]
    
    # Pre-select item if provided in URL
    item_id = request.args.get('item_id', type=int)
    if item_id and request.method == 'GET':
        form.item_id.data = item_id
    
    if form.validate_on_submit():
        # Get STOCK_IN transaction type
        stock_in_type = db.session.query(TransactionType)\
            .filter_by(type_name='STOCK_IN').first()
        
        if not stock_in_type:
            flash('Stock In transaction type not found', 'danger')
            return redirect(url_for('transactions.list'))
        
        # Create transaction
        transaction = Transaction(
            item_id=form.item_id.data,
            type_id=stock_in_type.type_id,
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            supplier_id=form.supplier_id.data if form.supplier_id.data != 0 else None,
            reference_number=form.reference_number.data,
            notes=form.notes.data
        )
        
        # Update item stock
        item = db.session.get(Item, form.item_id.data)
        item.current_stock += form.quantity.data
        
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Stock in recorded: +{form.quantity.data} units', 'success')
        return redirect(url_for('items.detail', id=item.item_id))
    
    return render_template('transactions/stock_in.html', form=form)


@bp.route('/stock-out', methods=['GET', 'POST'])
def stock_out():
    """Record stock out transaction"""
    form = StockOutForm()
    
    # Populate item choices
    form.item_id.choices = [
        (i.item_id, f"{i.item_code} - {i.item_name} (Stock: {i.current_stock})")
        for i in db.session.query(Item).order_by(Item.item_name).all()
    ]
    
    # Pre-select item if provided in URL
    item_id = request.args.get('item_id', type=int)
    if item_id and request.method == 'GET':
        form.item_id.data = item_id
    
    if form.validate_on_submit():
        # Check stock availability
        item = db.session.get(Item, form.item_id.data)
        if item.current_stock < form.quantity.data:
            flash(f'Insufficient stock. Available: {item.current_stock}', 'danger')
            return render_template('transactions/stock_out.html', form=form)
        
        # Get STOCK_OUT transaction type
        stock_out_type = db.session.query(TransactionType)\
            .filter_by(type_name='STOCK_OUT').first()
        
        if not stock_out_type:
            flash('Stock Out transaction type not found', 'danger')
            return redirect(url_for('transactions.list'))
        
        # Create transaction
        transaction = Transaction(
            item_id=form.item_id.data,
            type_id=stock_out_type.type_id,
            quantity=form.quantity.data,
            reference_number=form.reference_number.data,
            notes=form.notes.data
        )
        
        # Update item stock
        item.current_stock -= form.quantity.data
        
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Stock out recorded: -{form.quantity.data} units', 'success')
        return redirect(url_for('items.detail', id=item.item_id))
    
    return render_template('transactions/stock_out.html', form=form)


@bp.route('/<int:id>')
def detail(id):
    """View transaction details"""
    transaction = db.session.get(Transaction, id)
    if not transaction:
        flash('Transaction not found', 'danger')
        return redirect(url_for('transactions.list'))
    
    return render_template('transactions/detail.html', transaction=transaction)

