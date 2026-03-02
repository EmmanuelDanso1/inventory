"""
Database Models - Normalized Schema (3NF)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import relationship
from invent_app import db

class TransactionType(db.Model):
    """Transaction types lookup table"""
    __tablename__ = 'transaction_types'
    
    type_id = Column(Integer, primary_key=True)
    type_name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    
    # Relationships
    transactions = relationship('Transaction', back_populates='transaction_type', lazy='dynamic')
    
    def __repr__(self):
        return f'<TransactionType {self.type_name}>'