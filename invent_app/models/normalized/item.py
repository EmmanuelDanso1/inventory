"""
Database Models - Normalized Schema (3NF)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import relationship
from invent_app import db

class Item(db.Model):
    """Core inventory items"""
    __tablename__ = 'items'
    
    item_id = Column(Integer, primary_key=True)
    item_code = Column(String(50), nullable=False, unique=True, index=True)
    item_name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey('categories.category_id'), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.supplier_id'), index=True)
    location_id = Column(Integer, ForeignKey('locations.location_id'))
    unit_price = Column(Numeric(10, 2), nullable=False)
    current_stock = Column(Integer, default=0, nullable=False, index=True)
    reorder_level = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship('Category', back_populates='items')
    supplier = relationship('Supplier', back_populates='items')
    location = relationship('Location', back_populates='items')
    transactions = relationship('Transaction', back_populates='item', lazy='dynamic', 
                               order_by='Transaction.transaction_date.desc()')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('current_stock >= 0', name='check_stock_positive'),
        CheckConstraint('unit_price >= 0', name='check_price_positive'),
        CheckConstraint('reorder_level >= 0', name='check_reorder_positive'),
    )
    
    def __repr__(self):
        return f'<Item {self.item_code}: {self.item_name}>'
    
    @property
    def is_low_stock(self):
        """Check if item is below reorder level"""
        return self.current_stock <= self.reorder_level
    
    @property
    def is_out_of_stock(self):
        """Check if item is out of stock"""
        return self.current_stock == 0
    
    @property
    def stock_value(self):
        """Calculate total stock value"""
        return float(self.current_stock * self.unit_price)
    
    @property
    def stock_status(self):
        """Get stock status as string"""
        if self.is_out_of_stock:
            return 'Out of Stock'
        elif self.is_low_stock:
            return 'Low Stock'
        else:
            return 'In Stock'