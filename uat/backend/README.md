# UAT Backend - Products Table

This module implements a multi-product configuration system for the UAT backend application.

## Overview

The products table implementation provides a complete database layer for managing multiple products in the system. It includes:

- **SQLAlchemy ORM models** for database entities
- **Pydantic schemas** for request/response validation
- **Repository pattern** for data access abstraction
- **Database configuration** with connection pooling
- **Comprehensive test suite** using pytest

## Architecture

### Models (`models.py`)

Defines the `Product` model with the following fields:

- `id` - Primary key (auto-increment)
- `name` - Unique product identifier (indexed)
- `display_name` - Human-readable product name
- `description` - Optional product description
- `price` - Product price (Decimal with 2 decimal places)
- `currency` - ISO 4217 currency code (3 characters, default: USD)
- `is_active` - Boolean flag for soft deletes
- `configuration` - JSON string for product-specific settings
- `created_at` - Timestamp of creation
- `updated_at` - Timestamp of last update

### Schemas (`schemas.py`)

Pydantic models for validation:

- `ProductBase` - Base schema with common attributes
- `ProductCreate` - Schema for creating new products (all required fields)
- `ProductUpdate` - Schema for updating products (all fields optional for partial updates)
- `ProductResponse` - Schema for API responses (includes ID and timestamps)

### Repository (`repository.py`)

Data access layer with methods:

- `create_product(product_data)` - Create a new product
- `get_product_by_id(product_id)` - Retrieve product by ID
- `get_product_by_name(name)` - Retrieve product by unique name
- `get_all_products(skip, limit, active_only)` - List products with pagination
- `update_product(product_id, product_data)` - Update existing product
- `delete_product(product_id)` - Hard delete a product
- `deactivate_product(product_id)` - Soft delete (set is_active=False)
- `count_products(active_only)` - Count total products

### Database (`database.py`)

Database configuration and session management:

- `get_database_url()` - Get database URL from environment
- `create_database_engine()` - Create SQLAlchemy engine with connection pooling
- `init_database()` - Initialize database tables
- `get_db()` - FastAPI dependency for database sessions
- `drop_all_tables()` - Drop all tables (testing only)

## Setup

### 1. Install Dependencies

```bash
cd uat/backend
pip install -r requirements.txt
```

### 2. Configure Database

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

Or create a `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 3. Initialize Database

```python
from database import init_database

# Create all tables
init_database()
```

## Usage

### Basic Example

```python
from sqlalchemy.orm import Session
from database import SessionLocal
from repository import ProductRepository
from schemas import ProductCreate, ProductUpdate
from decimal import Decimal

# Create session
db: Session = SessionLocal()

# Initialize repository
repo = ProductRepository(db)

# Create a product
product_data = ProductCreate(
    name="premium_plan",
    display_name="Premium Plan",
    description="Full access to all features",
    price=Decimal("99.99"),
    currency="USD",
    is_active=True,
    configuration='{"features": ["feature1", "feature2"]}'
)

product = repo.create_product(product_data)
print(f"Created product: {product.id}")

# Get product by ID
found = repo.get_product_by_id(product.id)
print(f"Found: {found.display_name}")

# Update product
update_data = ProductUpdate(price=Decimal("89.99"))
updated = repo.update_product(product.id, update_data)
print(f"New price: {updated.price}")

# List all active products
active_products = repo.get_all_products(active_only=True)
for p in active_products:
    print(f"- {p.display_name}: ${p.price}")

# Deactivate (soft delete)
repo.deactivate_product(product.id)

# Close session
db.close()
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db, init_database
from repository import ProductRepository
from schemas import ProductCreate, ProductResponse

app = FastAPI()

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_database()

@app.post("/products", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    repo = ProductRepository(db)
    return repo.create_product(product_data)

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    repo = ProductRepository(db)
    product = repo.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
```

## Testing

Run the test suite:

```bash
cd uat/backend
pytest tests/ -v
```

Run specific test files:

```bash
pytest tests/test_models.py -v
pytest tests/test_schemas.py -v
pytest tests/test_repository.py -v
```

Run with coverage:

```bash
pytest --cov=. --cov-report=html tests/
```

## Test Coverage

The test suite includes:

- **Model tests** (`test_models.py`)
  - Product creation and defaults
  - Unique constraints
  - String representation
  - Dictionary conversion
  - Nullable fields
  - Timestamp updates

- **Schema tests** (`test_schemas.py`)
  - Valid data validation
  - Default values
  - Currency code normalization
  - Field validation (min/max length, numeric constraints)
  - Required vs optional fields
  - Partial updates

- **Repository tests** (`test_repository.py`)
  - CRUD operations
  - Pagination
  - Filtering (active/inactive)
  - Soft delete (deactivation)
  - Hard delete
  - Product counting

## Database Schema

The products table structure:

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    configuration TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_id ON products(id);
```

## Configuration Options

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (required)
  - Format: `postgresql://user:password@host:port/database`
  - The system automatically converts `postgres://` to `postgresql://`

### Connection Pool Settings

Default connection pool configuration (in `database.py`):

- `pool_size=5` - Number of persistent connections
- `max_overflow=10` - Additional connections when pool is full
- `pool_pre_ping=True` - Verify connections before using

## Multi-Product Support

The configuration field allows storing product-specific settings as JSON:

```python
configuration = json.dumps({
    "features": ["analytics", "api_access", "priority_support"],
    "limits": {
        "api_calls_per_day": 10000,
        "users": 50
    },
    "trial_days": 14
})

product = ProductCreate(
    name="enterprise_plan",
    display_name="Enterprise Plan",
    price=Decimal("299.99"),
    configuration=configuration
)
```

## Best Practices

1. **Always use the repository layer** - Don't access models directly
2. **Use soft deletes** - Call `deactivate_product()` instead of `delete_product()`
3. **Validate prices** - Ensure prices are non-negative Decimals
4. **Normalize currency codes** - Always uppercase (handled automatically by schemas)
5. **Close sessions** - Use context managers or FastAPI dependencies
6. **Never commit secrets** - Use environment variables for DATABASE_URL

## Troubleshooting

### Connection Issues

If you get connection errors:

1. Verify `DATABASE_URL` is set correctly
2. Ensure PostgreSQL is running
3. Check firewall/network settings
4. Verify database user has proper permissions

### Import Errors

This module uses flat imports. Ensure you're in the correct directory:

```bash
cd uat/backend
python -c "from models import Product; print('OK')"
```

### Migration from postgres:// to postgresql://

The system automatically handles this conversion in `database.py`:

```python
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
```

## Future Enhancements

Potential improvements:

- Add product categories/tags
- Implement pricing tiers
- Add product images/media
- Implement versioning for configuration changes
- Add audit logging
- Implement product bundles/packages
- Add internationalization for display names

## License

Internal use only - Synpro Consulting

## Support

For questions or issues, contact the development team.
