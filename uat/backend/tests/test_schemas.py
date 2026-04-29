"""Unit tests for Pydantic schemas.

This module contains tests for request/response validation schemas.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError
from schemas import ProductCreate, ProductUpdate, ProductResponse


def test_product_create_valid():
    """Test creating a valid ProductCreate schema."""
    product = ProductCreate(
        name="test_product",
        display_name="Test Product",
        description="A test product",
        price=Decimal("99.99"),
        currency="USD",
        is_active=True,
        configuration='{"key": "value"}',
    )
    
    assert product.name == "test_product"
    assert product.display_name == "Test Product"
    assert product.price == Decimal("99.99")
    assert product.currency == "USD"
    assert product.is_active is True


def test_product_create_defaults():
    """Test default values in ProductCreate schema."""
    product = ProductCreate(
        name="minimal",
        display_name="Minimal Product",
        price=Decimal("10.00"),
    )
    
    assert product.currency == "USD"
    assert product.is_active is True
    assert product.description is None
    assert product.configuration is None


def test_product_create_currency_uppercase():
    """Test that currency code is converted to uppercase."""
    product = ProductCreate(
        name="test",
        display_name="Test",
        price=Decimal("10.00"),
        currency="eur",
    )
    
    assert product.currency == "EUR"


def test_product_create_missing_required_fields():
    """Test that missing required fields raise validation error."""
    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(
            name="test",
            # Missing display_name and price
        )
    
    errors = exc_info.value.errors()
    field_names = {error["loc"][0] for error in errors}
    
    assert "display_name" in field_names
    assert "price" in field_names


def test_product_create_negative_price():
    """Test that negative prices are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(
            name="test",
            display_name="Test",
            price=Decimal("-10.00"),
        )
    
    errors = exc_info.value.errors()
    assert any("price" in str(error["loc"]) for error in errors)


def test_product_create_invalid_currency_length():
    """Test that invalid currency code length is rejected."""
    with pytest.raises(ValidationError):
        ProductCreate(
            name="test",
            display_name="Test",
            price=Decimal("10.00"),
            currency="US",  # Too short
        )
    
    with pytest.raises(ValidationError):
        ProductCreate(
            name="test",
            display_name="Test",
            price=Decimal("10.00"),
            currency="USDD",  # Too long
        )


def test_product_create_empty_name():
    """Test that empty name is rejected."""
    with pytest.raises(ValidationError):
        ProductCreate(
            name="",
            display_name="Test",
            price=Decimal("10.00"),
        )


def test_product_update_partial():
    """Test ProductUpdate with partial data."""
    update = ProductUpdate(
        display_name="Updated Name",
        price=Decimal("150.00"),
    )
    
    assert update.display_name == "Updated Name"
    assert update.price == Decimal("150.00")
    assert update.name is None
    assert update.currency is None


def test_product_update_all_fields():
    """Test ProductUpdate with all fields."""
    update = ProductUpdate(
        name="updated_name",
        display_name="Updated Display Name",
        description="Updated description",
        price=Decimal("200.00"),
        currency="eur",
        is_active=False,
        configuration='{"updated": true}',
    )
    
    assert update.name == "updated_name"
    assert update.display_name == "Updated Display Name"
    assert update.currency == "EUR"  # Should be uppercase
    assert update.is_active is False


def test_product_update_empty():
    """Test ProductUpdate with no fields (all optional)."""
    update = ProductUpdate()
    
    assert update.name is None
    assert update.display_name is None
    assert update.price is None


def test_product_update_currency_uppercase():
    """Test that currency code is converted to uppercase in updates."""
    update = ProductUpdate(currency="gbp")
    
    assert update.currency == "GBP"


def test_product_update_negative_price():
    """Test that negative prices are rejected in updates."""
    with pytest.raises(ValidationError):
        ProductUpdate(price=Decimal("-50.00"))


def test_product_response_valid():
    """Test creating a valid ProductResponse schema."""
    response = ProductResponse(
        id=1,
        name="test_product",
        display_name="Test Product",
        description="A test product",
        price=Decimal("99.99"),
        currency="USD",
        is_active=True,
        configuration='{"key": "value"}',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    assert response.id == 1
    assert response.name == "test_product"
    assert response.display_name == "Test Product"
    assert isinstance(response.created_at, datetime)
    assert isinstance(response.updated_at, datetime)


def test_product_response_missing_required():
    """Test that ProductResponse requires all fields."""
    with pytest.raises(ValidationError) as exc_info:
        ProductResponse(
            name="test",
            display_name="Test",
            price=Decimal("10.00"),
            # Missing id, created_at, updated_at
        )
    
    errors = exc_info.value.errors()
    field_names = {error["loc"][0] for error in errors}
    
    assert "id" in field_names
    assert "created_at" in field_names
    assert "updated_at" in field_names


def test_price_decimal_places():
    """Test that price respects decimal place limits."""
    # Valid: 2 decimal places
    product = ProductCreate(
        name="test",
        display_name="Test",
        price=Decimal("99.99"),
    )
    assert product.price == Decimal("99.99")
    
    # Valid: 1 decimal place
    product = ProductCreate(
        name="test2",
        display_name="Test",
        price=Decimal("99.9"),
    )
    assert product.price == Decimal("99.9")
    
    # Valid: no decimal places
    product = ProductCreate(
        name="test3",
        display_name="Test",
        price=Decimal("99"),
    )
    assert product.price == Decimal("99")


def test_product_name_max_length():
    """Test that name respects maximum length."""
    long_name = "a" * 255
    product = ProductCreate(
        name=long_name,
        display_name="Test",
        price=Decimal("10.00"),
    )
    assert product.name == long_name
    
    # Test exceeding max length
    with pytest.raises(ValidationError):
        ProductCreate(
            name="a" * 256,  # Too long
            display_name="Test",
            price=Decimal("10.00"),
        )
