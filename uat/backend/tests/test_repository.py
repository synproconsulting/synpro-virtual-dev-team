"""Unit tests for repository layer.

This module contains tests for the ProductRepository and other repository classes.
"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product
from repository import ProductRepository
from schemas import ProductCreate, ProductUpdate


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing.
    
    Yields:
        Session: SQLAlchemy session for testing
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def product_repo(in_memory_db):
    """Create ProductRepository instance for testing.
    
    Args:
        in_memory_db: Database session fixture
        
    Returns:
        ProductRepository: Repository instance
    """
    return ProductRepository(in_memory_db)


def test_create_product(product_repo):
    """Test creating a product through repository."""
    product_data = ProductCreate(
        name="test_product",
        display_name="Test Product",
        description="A test product",
        price=Decimal("99.99"),
        currency="USD",
        is_active=True,
    )
    
    product = product_repo.create_product(product_data)
    
    assert product.id is not None
    assert product.name == "test_product"
    assert product.display_name == "Test Product"
    assert product.price == Decimal("99.99")


def test_get_product_by_id(product_repo):
    """Test retrieving a product by ID."""
    product_data = ProductCreate(
        name="findme",
        display_name="Find Me Product",
        price=Decimal("50.00"),
    )
    
    created = product_repo.create_product(product_data)
    found = product_repo.get_product_by_id(created.id)
    
    assert found is not None
    assert found.id == created.id
    assert found.name == "findme"


def test_get_product_by_id_not_found(product_repo):
    """Test retrieving a non-existent product by ID."""
    found = product_repo.get_product_by_id(99999)
    
    assert found is None


def test_get_product_by_name(product_repo):
    """Test retrieving a product by name."""
    product_data = ProductCreate(
        name="unique_name",
        display_name="Unique Product",
        price=Decimal("30.00"),
    )
    
    created = product_repo.create_product(product_data)
    found = product_repo.get_product_by_name("unique_name")
    
    assert found is not None
    assert found.id == created.id
    assert found.name == "unique_name"


def test_get_product_by_name_not_found(product_repo):
    """Test retrieving a non-existent product by name."""
    found = product_repo.get_product_by_name("nonexistent")
    
    assert found is None


def test_get_all_products(product_repo):
    """Test retrieving all products."""
    for i in range(5):
        product_data = ProductCreate(
            name=f"product_{i}",
            display_name=f"Product {i}",
            price=Decimal("10.00"),
        )
        product_repo.create_product(product_data)
    
    products = product_repo.get_all_products()
    
    assert len(products) == 5


def test_get_all_products_pagination(product_repo):
    """Test pagination when retrieving products."""
    for i in range(10):
        product_data = ProductCreate(
            name=f"product_{i}",
            display_name=f"Product {i}",
            price=Decimal("10.00"),
        )
        product_repo.create_product(product_data)
    
    # Get first 5
    products_page_1 = product_repo.get_all_products(skip=0, limit=5)
    assert len(products_page_1) == 5
    
    # Get next 5
    products_page_2 = product_repo.get_all_products(skip=5, limit=5)
    assert len(products_page_2) == 5
    
    # Ensure they're different
    page_1_ids = {p.id for p in products_page_1}
    page_2_ids = {p.id for p in products_page_2}
    assert page_1_ids.isdisjoint(page_2_ids)


def test_get_all_products_active_only(product_repo):
    """Test filtering products by active status."""
    # Create active products
    for i in range(3):
        product_data = ProductCreate(
            name=f"active_{i}",
            display_name=f"Active {i}",
            price=Decimal("10.00"),
            is_active=True,
        )
        product_repo.create_product(product_data)
    
    # Create inactive products
    for i in range(2):
        product_data = ProductCreate(
            name=f"inactive_{i}",
            display_name=f"Inactive {i}",
            price=Decimal("10.00"),
            is_active=False,
        )
        product_repo.create_product(product_data)
    
    all_products = product_repo.get_all_products()
    active_products = product_repo.get_all_products(active_only=True)
    
    assert len(all_products) == 5
    assert len(active_products) == 3


def test_update_product(product_repo):
    """Test updating a product."""
    product_data = ProductCreate(
        name="update_test",
        display_name="Original Name",
        price=Decimal("100.00"),
    )
    
    created = product_repo.create_product(product_data)
    
    update_data = ProductUpdate(
        display_name="Updated Name",
        price=Decimal("150.00"),
    )
    
    updated = product_repo.update_product(created.id, update_data)
    
    assert updated is not None
    assert updated.display_name == "Updated Name"
    assert updated.price == Decimal("150.00")
    assert updated.name == "update_test"  # Unchanged


def test_update_product_not_found(product_repo):
    """Test updating a non-existent product."""
    update_data = ProductUpdate(display_name="New Name")
    
    result = product_repo.update_product(99999, update_data)
    
    assert result is None


def test_delete_product(product_repo):
    """Test deleting a product."""
    product_data = ProductCreate(
        name="delete_test",
        display_name="Delete Me",
        price=Decimal("10.00"),
    )
    
    created = product_repo.create_product(product_data)
    product_id = created.id
    
    result = product_repo.delete_product(product_id)
    
    assert result is True
    assert product_repo.get_product_by_id(product_id) is None


def test_delete_product_not_found(product_repo):
    """Test deleting a non-existent product."""
    result = product_repo.delete_product(99999)
    
    assert result is False


def test_deactivate_product(product_repo):
    """Test soft deleting (deactivating) a product."""
    product_data = ProductCreate(
        name="deactivate_test",
        display_name="Deactivate Me",
        price=Decimal("10.00"),
        is_active=True,
    )
    
    created = product_repo.create_product(product_data)
    
    deactivated = product_repo.deactivate_product(created.id)
    
    assert deactivated is not None
    assert deactivated.is_active is False


def test_deactivate_product_not_found(product_repo):
    """Test deactivating a non-existent product."""
    result = product_repo.deactivate_product(99999)
    
    assert result is None


def test_count_products(product_repo):
    """Test counting products."""
    for i in range(7):
        product_data = ProductCreate(
            name=f"count_{i}",
            display_name=f"Count {i}",
            price=Decimal("10.00"),
        )
        product_repo.create_product(product_data)
    
    count = product_repo.count_products()
    
    assert count == 7


def test_count_products_active_only(product_repo):
    """Test counting only active products."""
    for i in range(4):
        product_data = ProductCreate(
            name=f"active_count_{i}",
            display_name=f"Active {i}",
            price=Decimal("10.00"),
            is_active=True,
        )
        product_repo.create_product(product_data)
    
    for i in range(3):
        product_data = ProductCreate(
            name=f"inactive_count_{i}",
            display_name=f"Inactive {i}",
            price=Decimal("10.00"),
            is_active=False,
        )
        product_repo.create_product(product_data)
    
    total_count = product_repo.count_products()
    active_count = product_repo.count_products(active_only=True)
    
    assert total_count == 7
    assert active_count == 4
