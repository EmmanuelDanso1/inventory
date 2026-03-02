"""
Database Models - Normalized Schema (3NF)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import relationship
from invent_app import db

class Transaction(db.Model):
    """Stock movement transactions"""
    __tablename__ = 'transactions'
    
    transaction_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.item_id'), nullable=False, index=True)
    type_id = Column(Integer, ForeignKey('transaction_types.type_id'), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    supplier_id = Column(Integer, ForeignKey('suppliers.supplier_id'))
    reference_number = Column(String(100))
    notes = Column(Text)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String(100))
    
    # Relationships
    item = relationship('Item', back_populates='transactions')
    transaction_type = relationship('TransactionType', back_populates='transactions')
    supplier = relationship('Supplier', back_populates='transactions')
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_item_date', 'item_id', 'transaction_date'),
        Index('idx_type_date', 'type_id', 'transaction_date'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
    )
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}: {self.transaction_type.type_name if self.transaction_type else "Unknown"}>'
    
    @property
    def total_value(self):
        """Calculate transaction total value"""
        if self.unit_price:
            return float(self.quantity * self.unit_price)
        return 0.0
    
    @property
    def formatted_date(self):
        """Get formatted transaction date"""
        return self.transaction_date.strftime('%Y-%m-%d %H:%M')