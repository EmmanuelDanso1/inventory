"""
Database Models - Normalized Schema (3NF)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import relationship
from invent_app import db

class Location(db.Model):
    """Storage locations - warehouse, aisle, shelf, bin"""
    __tablename__ = 'locations'
    
    location_id = Column(Integer, primary_key=True)
    warehouse = Column(String(50), nullable=False)
    aisle = Column(String(20))
    shelf = Column(String(20))
    bin = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    items = relationship('Item', back_populates='location', lazy='dynamic')
    
    def __repr__(self):
        return f'<Location {self.warehouse}-{self.aisle}-{self.shelf}>'
    
    def get_full_location(self):
        """Get formatted location string"""
        parts = [self.warehouse]
        if self.aisle:
            parts.append(f"Aisle {self.aisle}")
        if self.shelf:
            parts.append(f"Shelf {self.shelf}")
        if self.bin:
            parts.append(f"Bin {self.bin}")
        return ", ".join(parts)

