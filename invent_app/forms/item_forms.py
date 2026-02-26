from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField,
    SelectField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, Email, ValidationError
)
from invent_app import db
from invent_app.models.normalized.item import Item

class ItemForm(FlaskForm):
    """Form for creating and editing items"""
    
    item_code = StringField(
        'Item Code',
        validators=[
            DataRequired(message='Item code is required'),
            Length(max=50, message='Item code must be less than 50 characters')
        ],
        render_kw={'placeholder': 'e.g., ITEM-001'}
    )
    
    item_name = StringField(
        'Item Name',
        validators=[
            DataRequired(message='Item name is required'),
            Length(max=200, message='Item name must be less than 200 characters')
        ],
        render_kw={'placeholder': 'e.g., Dell Laptop i7'}
    )
    
    description = TextAreaField(
        'Description',
        validators=[Optional()],
        render_kw={'placeholder': 'Enter item description...', 'rows': 4}
    )
    
    category_id = SelectField(
        'Category',
        validators=[DataRequired(message='Please select a category')],
        coerce=int
    )
    
    supplier_id = SelectField(
        'Supplier',
        validators=[Optional()],
        coerce=int
    )
    
    location_id = SelectField(
        'Location',
        validators=[Optional()],
        coerce=int
    )
    
    unit_price = DecimalField(
        'Unit Price ($)',
        validators=[
            DataRequired(message='Unit price is required'),
            NumberRange(min=0.01, message='Price must be greater than 0')
        ],
        places=2,
        render_kw={'placeholder': '0.00', 'step': '0.01'}
    )
    
    current_stock = IntegerField(
        'Current Stock',
        validators=[
            DataRequired(message='Current stock is required'),
            NumberRange(min=0, message='Stock cannot be negative')
        ],
        default=0,
        render_kw={'placeholder': '0'}
    )
    
    reorder_level = IntegerField(
        'Reorder Level',
        validators=[
            DataRequired(message='Reorder level is required'),
            NumberRange(min=0, message='Reorder level cannot be negative')
        ],
        default=10,
        render_kw={'placeholder': '10'}
    )
    
    submit = SubmitField('Save Item')
    
    def validate_item_code(self, field):
        """Check if item code is unique (for new items)"""
        # Skip validation if editing existing item
        if hasattr(self, '_obj') and self._obj and self._obj.item_code == field.data:
            return
        
        existing = db.session.query(Item).filter_by(item_code=field.data).first()
        if existing:
            raise ValidationError('Item code already exists. Please use a different code.')
