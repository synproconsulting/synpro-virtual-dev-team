"""Repository layer for database operations.

This module provides data access layer for products and other entities,
abstracting database operations from business logic.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Product
from schemas import ProductCreate, ProductUpdate


class ProductRepository:
    """Repository for Product database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product.
        
        Args:
            product_data: Product creation data
            
        Returns:
            Product: Created product instance
            
        Raises:
            IntegrityError: If product name already exists
        """
        product = Product(**product_data.dict())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product or None: Product instance if found
        """
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def get_product_by_name(self, name: str) -> Optional[Product]:
        """Get product by name.
        
        Args:
            name: Product name
            
        Returns:
            Product or None: Product instance if found
        """
        return self.db.query(Product).filter(Product.name == name).first()
    
    def get_all_products(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        active_only: bool = False
    ) -> List[Product]:
        """Get all products with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Filter for active products only
            
        Returns:
            List[Product]: List of product instances
        """
        query = self.db.query(Product)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    def update_product(
        self, 
        product_id: int, 
        product_data: ProductUpdate
    ) -> Optional[Product]:
        """Update an existing product.
        
        Args:
            product_id: Product ID to update
            product_data: Updated product data
            
        Returns:
            Product or None: Updated product instance if found
        """
        product = self.get_product_by_id(product_id)
        
        if not product:
            return None
        
        update_data = product_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product (hard delete).
        
        Args:
            product_id: Product ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        product = self.get_product_by_id(product_id)
        
        if not product:
            return False
        
        self.db.delete(product)
        self.db.commit()
        return True
    
    def deactivate_product(self, product_id: int) -> Optional[Product]:
        """Soft delete: deactivate a product.
        
        Args:
            product_id: Product ID to deactivate
            
        Returns:
            Product or None: Deactivated product instance if found
        """
        product = self.get_product_by_id(product_id)
        
        if not product:
            return None
        
        product.is_active = False
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def count_products(self, active_only: bool = False) -> int:
        """Count total products.
        
        Args:
            active_only: Count only active products
            
        Returns:
            int: Total product count
        """
        query = self.db.query(Product)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        return query.count()
