from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField,
    SelectField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, Email, ValidationError
)
from invent_app import db

class StockInForm(FlaskForm):
    """Form for recording stock in transactions"""
    
    item_id = SelectField(
        'Item',
        validators=[DataRequired(message='Please select an item')],
        coerce=int
    )
    
    quantity = IntegerField(
        'Quantity',
        validators=[
            DataRequired(message='Quantity is required'),
            NumberRange(min=1, message='Quantity must be at least 1')
        ],
        render_kw={'placeholder': '0', 'min': '1'}
    )
    
    unit_price = DecimalField(
        'Unit Price ($)',
        validators=[
            Optional(),
            NumberRange(min=0, message='Price cannot be negative')
        ],
        places=2,
        render_kw={'placeholder': '0.00', 'step': '0.01'}
    )
    
    supplier_id = SelectField(
        'Supplier',
        validators=[Optional()],
        coerce=int
    )
    
    reference_number = StringField(
        'Reference Number',
        validators=[
            Optional(),
            Length(max=100, message='Reference number must be less than 100 characters')
        ],
        render_kw={'placeholder': 'PO-12345, Invoice-67890, etc.'}
    )
    
    notes = TextAreaField(
        'Notes',
        validators=[Optional()],
        render_kw={'placeholder': 'Additional notes...', 'rows': 3}
    )
    
    submit = SubmitField('Record Stock In')


class StockOutForm(FlaskForm):
    """Form for recording stock out transactions"""
    
    item_id = SelectField(
        'Item',
        validators=[DataRequired(message='Please select an item')],
        coerce=int
    )
    
    quantity = IntegerField(
        'Quantity',
        validators=[
            DataRequired(message='Quantity is required'),
            NumberRange(min=1, message='Quantity must be at least 1')
        ],
        render_kw={'placeholder': '0', 'min': '1'}
    )
    
    reference_number = StringField(
        'Reference Number',
        validators=[
            Optional(),
            Length(max=100, message='Reference number must be less than 100 characters')
        ],
        render_kw={'placeholder': 'SO-12345, Delivery-67890, etc.'}
    )
    
    notes = TextAreaField(
        'Notes',
        validators=[Optional()],
        render_kw={'placeholder': 'Reason for stock out, destination, etc.', 'rows': 3}
    )
    
    submit = SubmitField('Record Stock Out')
