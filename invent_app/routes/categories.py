from flask import Blueprint, render_template, request, redirect, url_for, flash
from invent_app import db
from invent_app.models.normalized.category import Category
from invent_app.forms.category_forms import CategoryForm

bp = Blueprint('categories', __name__)


@bp.route('/')
def list():
    """List all categories"""
    categories = db.session.query(Category)\
        .order_by(Category.category_name)\
        .all()
    
    return render_template('categories/list.html', categories=categories)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new category"""
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            category_name=form.category_name.data,
            description=form.description.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Category "{category.category_name}" created successfully!', 'success')
        return redirect(url_for('categories.list'))
    
    return render_template('categories/manage.html', form=form, action='Create')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit category"""
    category = db.session.get(Category, id)
    if not category:
        flash('Category not found', 'danger')
        return redirect(url_for('categories.list'))
    
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.category_name = form.category_name.data
        category.description = form.description.data
        
        db.session.commit()
        
        flash(f'Category "{category.category_name}" updated successfully!', 'success')
        return redirect(url_for('categories.list'))
    
    return render_template('categories/manage.html', form=form, action='Edit', category=category)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete category"""
    category = db.session.get(Category, id)
    if not category:
        flash('Category not found', 'danger')
        return redirect(url_for('categories.list'))
    
    if category.items:
        flash('Cannot delete category with existing items', 'danger')
        return redirect(url_for('categories.list'))
    
    category_name = category.category_name
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{category_name}" deleted successfully!', 'success')
    return redirect(url_for('categories.list'))