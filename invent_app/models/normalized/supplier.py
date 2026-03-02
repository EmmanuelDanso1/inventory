"""
Database Models - Normalized Schema (3NF)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import relationship
from invent_app import db

class Supplier(db.Model):
    """Supplier information"""
    __tablename__ = 'suppliers'
    
    supplier_id = Column(Integer, primary_key=True)
    supplier_name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    items = relationship('Item', back_populates='supplier', lazy='dynamic')
    transactions = relationship('Transaction', back_populates='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.supplier_name}>'