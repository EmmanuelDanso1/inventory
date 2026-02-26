from flask import Blueprint, render_template, request, redirect, url_for, flash
from invent_app import db
from invent_app.models.normalized.supplier import Supplier
from invent_app.forms.supplier_forms import SupplierForm

bp = Blueprint('suppliers', __name__)


@bp.route('/')
def list():
    """List all suppliers"""
    suppliers = db.session.query(Supplier)\
        .order_by(Supplier.supplier_name)\
        .all()
    
    return render_template('suppliers/list.html', suppliers=suppliers)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new supplier"""
    form = SupplierForm()
    
    if form.validate_on_submit():
        supplier = Supplier(
            supplier_name=form.supplier_name.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash(f'Supplier "{supplier.supplier_name}" created successfully!', 'success')
        return redirect(url_for('suppliers.list'))
    
    return render_template('suppliers/manage.html', form=form, action='Create')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit supplier"""
    supplier = db.session.get(Supplier, id)
    if not supplier:
        flash('Supplier not found', 'danger')
        return redirect(url_for('suppliers.list'))
    
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        supplier.supplier_name = form.supplier_name.data
        supplier.contact_person = form.contact_person.data
        supplier.email = form.email.data
        supplier.phone = form.phone.data
        supplier.address = form.address.data
        
        db.session.commit()
        
        flash(f'Supplier "{supplier.supplier_name}" updated successfully!', 'success')
        return redirect(url_for('suppliers.list'))
    
    return render_template('suppliers/manage.html', form=form, action='Edit', supplier=supplier)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete supplier"""
    supplier = db.session.get(Supplier, id)
    if not supplier:
        flash('Supplier not found', 'danger')
        return redirect(url_for('suppliers.list'))
    
    if supplier.items or supplier.transactions:
        flash('Cannot delete supplier with existing items or transactions', 'danger')
        return redirect(url_for('suppliers.list'))
    
    supplier_name = supplier.supplier_name
    db.session.delete(supplier)
    db.session.commit()
    
    flash(f'Supplier "{supplier_name}" deleted successfully!', 'success')
    return redirect(url_for('suppliers.list'))