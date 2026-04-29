"""Database models for UAT backend.

This module defines SQLAlchemy models for the application, including
the Products table for multi-product configuration support.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Product(Base):
    """Product model for multi-product configuration.
    
    This table stores product information including name, description,
    pricing, and configuration details for supporting multiple products
    in the system.
    """
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="USD")
    is_active = Column(Boolean, nullable=False, default=True)
    configuration = Column(Text, nullable=True)  # JSON string for product-specific config
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of Product."""
        return f"<Product(id={self.id}, name='{self.name}', is_active={self.is_active})>"
    
    def to_dict(self) -> dict:
        """Convert Product instance to dictionary.
        
        Returns:
            dict: Dictionary representation of the product
        """
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "price": float(self.price) if self.price else 0.00,
            "currency": self.currency,
            "is_active": self.is_active,
            "configuration": self.configuration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
