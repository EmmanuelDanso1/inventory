"""
Denormalized Transaction Model - Single flat table
Combines transaction + item + type + supplier into one table
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, CheckConstraint, Index
from invent_app import db


class TransactionDenorm(db.Model):
    """Denormalized transactions - everything in one table"""
    __tablename__ = 'transactions_denormalized'

    transaction_id = Column(Integer, primary_key=True)

    # Item fields (denormalized - no FK)
    item_code = Column(String(50), nullable=False, index=True)
    item_name = Column(String(200), nullable=False)
    category_name = Column(String(100))
    supplier_name = Column(String(200))

    # Transaction fields
    transaction_type = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    reference_number = Column(String(100))
    notes = Column(Text)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String(100))

    __table_args__ = (
        Index('idx_denorm_item_date', 'item_code', 'transaction_date'),
        Index('idx_denorm_type_date', 'transaction_type', 'transaction_date'),
        CheckConstraint('quantity > 0', name='check_denorm_qty_positive'),
    )

    def __repr__(self):
        return f'<TransactionDenorm {self.transaction_id}: {self.transaction_type}>'

    @property
    def total_value(self):
        if self.unit_price:
            return float(self.quantity * self.unit_price)
        return 0.0
