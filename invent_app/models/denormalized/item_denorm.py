"""
Denormalized Item Model - Single flat table (no joins needed)
Combines items + category + supplier + location into one table
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, CheckConstraint
from invent_app import db


class ItemDenorm(db.Model):
    """Denormalized inventory items - everything in one table"""
    __tablename__ = 'items_denormalized'

    item_id = Column(Integer, primary_key=True)
    item_code = Column(String(50), nullable=False, unique=True, index=True)
    item_name = Column(String(200), nullable=False, index=True)
    description = Column(Text)

    # Category fields (denormalized - no FK)
    category_name = Column(String(100), nullable=False, index=True)

    # Supplier fields (denormalized - no FK)
    supplier_name = Column(String(200))
    supplier_email = Column(String(200))
    supplier_phone = Column(String(50))
    supplier_contact = Column(String(200))

    # Location fields (denormalized - no FK)
    location_name = Column(String(100))
    location_zone = Column(String(50))

    # Item fields
    unit_price = Column(Numeric(10, 2), nullable=False)
    current_stock = Column(Integer, default=0, nullable=False, index=True)
    reorder_level = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('current_stock >= 0', name='check_denorm_stock_positive'),
        CheckConstraint('unit_price >= 0', name='check_denorm_price_positive'),
    )

    def __repr__(self):
        return f'<ItemDenorm {self.item_code}: {self.item_name}>'

    @property
    def stock_status(self):
        if self.current_stock == 0:
            return 'Out of Stock'
        elif self.current_stock <= self.reorder_level:
            return 'Low Stock'
        return 'In Stock'
