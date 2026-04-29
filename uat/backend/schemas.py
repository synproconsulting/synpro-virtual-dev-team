"""Pydantic schemas for request/response validation.

This module defines Pydantic models for validating API requests
and serializing responses for the UAT backend.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, condecimal, validator


class ProductBase(BaseModel):
    """Base schema for Product with common attributes."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Unique product identifier name")
    display_name: str = Field(..., min_length=1, max_length=255, description="Display name for the product")
    description: Optional[str] = Field(None, description="Product description")
    price: condecimal(max_digits=10, decimal_places=2) = Field(..., ge=0, description="Product price")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code (ISO 4217)")
    is_active: bool = Field(default=True, description="Whether the product is active")
    configuration: Optional[str] = Field(None, description="JSON configuration for product-specific settings")
    
    @validator('currency')
    def validate_currency_uppercase(cls, v: str) -> str:
        """Ensure currency code is uppercase.
        
        Args:
            v: Currency code string
            
        Returns:
            str: Uppercase currency code
        """
        return v.upper()


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product.
    
    All fields are optional to allow partial updates.
    """
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None
    configuration: Optional[str] = None
    
    @validator('currency')
    def validate_currency_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """Ensure currency code is uppercase.
        
        Args:
            v: Currency code string or None
            
        Returns:
            str or None: Uppercase currency code or None
        """
        return v.upper() if v else None


class ProductResponse(ProductBase):
    """Schema for product response including database fields."""
    
    id: int = Field(..., description="Product ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        orm_mode = True
