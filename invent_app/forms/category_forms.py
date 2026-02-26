from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField,
    SelectField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, Email, ValidationError
)
from invent_app import db

from invent_app.models.normalized.category import Category


class CategoryForm(FlaskForm):
    """Form for creating and editing categories"""
    
    category_name = StringField(
        'Category Name',
        validators=[
            DataRequired(message='Category name is required'),
            Length(max=100, message='Category name must be less than 100 characters')
        ],
        render_kw={'placeholder': 'e.g., Electronics'}
    )
    
    description = TextAreaField(
        'Description',
        validators=[Optional()],
        render_kw={'placeholder': 'Enter category description...', 'rows': 3}
    )
    
    submit = SubmitField('Save Category')
    
    def validate_category_name(self, field):
        """Check if category name is unique"""
        if hasattr(self, '_obj') and self._obj and self._obj.category_name == field.data:
            return
        
        existing = db.session.query(Category).filter_by(category_name=field.data).first()
        if existing:
            raise ValidationError('Category name already exists. Please use a different name.')

