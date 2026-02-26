from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField,
    SelectField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, Email, ValidationError
)
from invent_app import db
from invent_app.models.normalized.location import Location


class LocationForm(FlaskForm):
    """Form for creating and editing storage locations"""
    
    warehouse = StringField(
        'Warehouse',
        validators=[
            DataRequired(message='Warehouse is required'),
            Length(max=50, message='Warehouse name must be less than 50 characters')
        ],
        render_kw={'placeholder': 'e.g., Main Warehouse, Building A'}
    )
    
    aisle = StringField(
        'Aisle',
        validators=[
            Optional(),
            Length(max=20, message='Aisle must be less than 20 characters')
        ],
        render_kw={'placeholder': 'e.g., A1, B2'}
    )
    
    shelf = StringField(
        'Shelf',
        validators=[
            Optional(),
            Length(max=20, message='Shelf must be less than 20 characters')
        ],
        render_kw={'placeholder': 'e.g., S1, S2'}
    )
    
    bin = StringField(
        'Bin',
        validators=[
            Optional(),
            Length(max=20, message='Bin must be less than 20 characters')
        ],
        render_kw={'placeholder': 'e.g., B01, B02'}
    )
    
    submit = SubmitField('Save Location')

