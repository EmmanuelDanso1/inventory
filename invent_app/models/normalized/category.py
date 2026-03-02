"""
Database Models - Normalized Schema (3NF)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import relationship
from invent_app import db

class Category(db.Model):
    """Product categories"""
    __tablename__ = 'categories'
    
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    items = relationship('Item', back_populates='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.category_name}>'