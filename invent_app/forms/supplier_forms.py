from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField,
    SelectField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, Email, ValidationError
)
from invent_app import db

from _invent_app.models.normalized.supplier import Supplier


class SupplierForm(FlaskForm):
    """Form for creating and editing suppliers"""
    
    supplier_name = StringField(
        'Supplier Name',
        validators=[
            DataRequired(message='Supplier name is required'),
            Length(max=200, message='Supplier name must be less than 200 characters')
        ],
        render_kw={'placeholder': 'e.g., Tech Supplies Inc.'}
    )
    
    contact_person = StringField(
        'Contact Person',
        validators=[
            Optional(),
            Length(max=100, message='Contact person name must be less than 100 characters')
        ],
        render_kw={'placeholder': 'e.g., John Doe'}
    )
    
    email = StringField(
        'Email',
        validators=[
            Optional(),
            Email(message='Please enter a valid email address'),
            Length(max=100, message='Email must be less than 100 characters')
        ],
        render_kw={'placeholder': 'supplier@example.com'}
    )
    
    phone = StringField(
        'Phone',
        validators=[
            Optional(),
            Length(max=20, message='Phone number must be less than 20 characters')
        ],
        render_kw={'placeholder': '+1 (555) 123-4567'}
    )
    
    address = TextAreaField(
        'Address',
        validators=[Optional()],
        render_kw={'placeholder': 'Enter supplier address...', 'rows': 3}
    )
    
    submit = SubmitField('Save Supplier')
    
    def validate_supplier_name(self, field):
        """Check if supplier name is unique"""
        if hasattr(self, '_obj') and self._obj and self._obj.supplier_name == field.data:
            return
        
        existing = db.session.query(Supplier).filter_by(supplier_name=field.data).first()
        if existing:
            raise ValidationError('Supplier name already exists. Please use a different name.')