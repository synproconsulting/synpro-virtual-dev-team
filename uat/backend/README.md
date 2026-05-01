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

---

# Router Modularization (SDT1-47)

## Overview

The main.py file has been refactored to split routes into separate, focused router modules for better code organization and maintainability.

## Router Modules

### Authentication Router (`auth_router.py`)

Handles all authentication-related endpoints:

- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /auth/reset-password` - Initiate password reset
- `POST /auth/confirm-reset` - Confirm password reset with token
- `GET /auth/verify` - Verify JWT token

### Profile Router (`profile_router.py`)

User profile management endpoints (placeholder for future implementation):

- `GET /profile/` - Get user profile information

### Notifications Router (`notifications_router.py`)

Notification management endpoints (placeholder for future implementation):

- `GET /notifications/` - Get user notifications

### Proxy Router (`proxy_router.py`)

API proxy/forwarding endpoints (placeholder for future implementation):

- `GET /proxy/` - Handle proxy requests

### PM Agent Router (`pm_agent_router.py`)

Product Manager Agent endpoints (placeholder for future implementation):

- `GET /pm-agent/` - PM Agent operations

## Main Application (`main.py`)

The main application file now:
- Configures the FastAPI app
- Sets up CORS middleware
- Includes all router modules
- Provides a root health check endpoint

## Migration from Monolithic Structure

The refactoring maintains 100% backward compatibility:
- All existing endpoints work identically
- No changes to request/response formats
- No behavioral changes
- Same authentication mechanisms
- Same error handling

## Testing

Run router-specific tests:

```bash
# Test authentication router
pytest tests/test_auth_router.py -v

# Test router integration
pytest tests/test_routers.py -v

# Test all
pytest tests/ -v
```

## Benefits

1. **Modularity** - Each router is self-contained and focused
2. **Maintainability** - Easier to locate and update specific functionality
3. **Scalability** - Simple to add new routers for new features
4. **Testing** - Each router can be tested independently
5. **Team Collaboration** - Multiple developers can work on different routers simultaneously

## Adding New Routers

To add a new router module:

1. Create a new file in `uat/backend/` (e.g., `new_feature_router.py`)
2. Define your router with appropriate prefix:
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/new-feature", tags=["new-feature"])
   ```
3. Add your endpoints to the router
4. Import and include in `main.py`:
   ```python
   from new_feature_router import router as new_feature_router
   app.include_router(new_feature_router)
   ```

## File Structure

```
uat/backend/
├── main.py                      # Main FastAPI application
├── auth_router.py               # Authentication routes
├── profile_router.py            # Profile management routes
├── notifications_router.py      # Notifications routes
├── proxy_router.py              # Proxy routes
├── pm_agent_router.py          # PM Agent routes
├── database.py                  # Database configuration
├── models.py                    # SQLAlchemy models
├── schemas.py                   # Pydantic schemas
├── repository.py                # Data access layer
├── requirements.txt             # Python dependencies
└── tests/
    ├── test_auth_router.py     # Authentication router tests
    └── test_routers.py         # Integration tests
```

## Backward Compatibility

All endpoints remain accessible at their original URLs:
- `/` - Health check
- `/auth/*` - Authentication endpoints
- `/profile/*` - Profile endpoints (new)
- `/notifications/*` - Notification endpoints (new)
- `/proxy/*` - Proxy endpoints (new)
- `/pm-agent/*` - PM Agent endpoints (new)

Existing client applications require no changes.

---

# Request Logging Middleware and Rate Limiting (SDT1-45)

## Overview

The application now includes comprehensive request logging middleware and rate limiting to improve monitoring, security, and performance.

## Request Logging Middleware

### Features

The `RequestLoggingMiddleware` automatically logs:

- **Request Information**
  - HTTP method and path
  - Client IP address
  - Query parameters
  - Request headers (with sensitive data redacted)

- **Response Information**
  - HTTP status code
  - Processing duration
  - Custom `X-Process-Time` header added to all responses

- **Error Tracking**
  - Failed requests logged with error details
  - Exception information captured

### Sensitive Data Protection

The middleware automatically redacts sensitive headers:
- `Authorization`
- `Cookie`
- `X-Api-Key`
- `X-Auth-Token`

These are replaced with `***REDACTED***` in logs to prevent credential leakage.

### Usage

The middleware is automatically applied to all requests. No changes needed in your endpoint code.

Example log output:
```
INFO: Request started: GET /auth/login from 127.0.0.1
INFO: Request completed: GET /auth/login status=200 duration=0.123s
```

### Configuration

Set the log level via environment variable:
```bash
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Rate Limiting

### Features

The application uses `slowapi` for flexible rate limiting:

- **Per-User Limits** - Authenticated users tracked by user ID
- **Per-IP Limits** - Unauthenticated requests tracked by IP address
- **Configurable Limits** - Set via environment variables
- **Multiple Strategies** - Strict, moderate, and relaxed limits available

### Default Limits

- **Default**: 100 requests per minute (all endpoints)
- **Strict**: 10 requests per minute (sensitive endpoints)
- **Moderate**: 50 requests per minute (standard endpoints)
- **Relaxed**: 200 requests per minute (high-traffic endpoints)

### Applying Rate Limits

#### Using Decorators

```python
from fastapi import APIRouter
from rate_limiter import limiter, rate_limit_strict

router = APIRouter(prefix="/api")

@router.post("/sensitive-operation")
@limiter.limit("10/minute")  # Custom limit
def sensitive_operation():
    return {"status": "ok"}

@router.get("/standard-endpoint")
@limiter.limit("50/minute")
def standard_endpoint():
    return {"data": "..."}
```

#### Using Pre-defined Decorators

```python
from rate_limiter import rate_limit_strict, rate_limit_moderate, rate_limit_relaxed

@router.post("/login")
@rate_limit_strict  # 10/minute
def login():
    pass

@router.get("/data")
@rate_limit_moderate  # 50/minute
def get_data():
    pass

@router.get("/public")
@rate_limit_relaxed  # 200/minute
def public_endpoint():
    pass
```

### Configuration

Configure rate limiting via environment variables:

```bash
# Default rate limit for all endpoints
export RATE_LIMIT_DEFAULT="100/minute"

# Storage backend (memory or Redis)
export RATE_LIMIT_STORAGE_URI="memory://"
# Or for Redis:
export RATE_LIMIT_STORAGE_URI="redis://localhost:6379"
```

### Rate Limit Headers

Responses include rate limit information:
- `X-RateLimit-Limit` - Maximum requests allowed
- `X-RateLimit-Remaining` - Requests remaining in window
- `X-RateLimit-Reset` - When the limit resets

### Rate Limit Exceeded Response

When a client exceeds the rate limit, they receive a `429 Too Many Requests` response:

```json
{
  "error": "Rate limit exceeded",
  "detail": "10 per 1 minute"
}
```

### Per-User vs Per-IP

The rate limiter intelligently chooses the tracking key:

1. **Authenticated requests** - Tracked by user ID from `request.state.user_id`
2. **Unauthenticated requests** - Tracked by IP address

This prevents users from bypassing limits by switching IP addresses.

### Production Recommendations

For production environments:

1. **Use Redis for storage**:
   ```bash
   export RATE_LIMIT_STORAGE_URI="redis://redis-host:6379"
   ```
   
2. **Adjust limits based on your needs**:
   ```bash
   export RATE_LIMIT_DEFAULT="1000/hour"
   ```

3. **Monitor rate limit violations**:
   - Check logs for `429` status codes
   - Set up alerts for excessive violations

4. **Consider different limits per endpoint type**:
   - Authentication: 10/minute
   - API reads: 100/minute
   - API writes: 50/minute
   - Public endpoints: 200/minute

## Testing

### Middleware Tests

Run middleware tests:
```bash
pytest tests/test_middleware.py -v
```

Tests cover:
- Request logging
- Response logging
- Error logging
- Header sanitization
- Processing time tracking

### Rate Limiting Tests

Run rate limiter tests:
```bash
pytest tests/test_rate_limiter.py -v
```

Tests cover:
- Requests under limit (allowed)
- Requests over limit (blocked)
- Independent limits per endpoint
- Rate limit headers
- Key generation (IP vs user ID)

---

# Hardened CORS Configuration (SDT1-56)

## Overview

The CORS (Cross-Origin Resource Sharing) configuration has been significantly hardened to prevent security vulnerabilities and ensure proper validation of allowed origins.

## Key Security Improvements

✅ **Origin Validation** - All configured origins are validated for proper URL format  
✅ **Multiple Origins Support** - Comma-separated list of allowed origins  
✅ **Wildcard Protection** - Wildcard (`*`) requires explicit opt-in and issues warnings  
✅ **Environment Awareness** - Different validation rules for development vs. production  
✅ **Startup Validation** - Configuration errors caught at application startup  
✅ **Clear Error Messages** - Descriptive errors help identify misconfigurations quickly  
✅ **Comprehensive Testing** - Full test coverage for all validation scenarios  

## Quick Start

### Development Environment

```bash
# In .env file
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

### Production Environment

```bash
# In .env file or environment variables
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com
```

### Multiple Frontends

```bash
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com,https://admin.example.com,https://mobile.example.com
```

## Environment Variables

### `FRONTEND_URL` (Required)

The primary CORS configuration. Supports:

1. **Single origin**: `FRONTEND_URL=https://app.example.com`
2. **Multiple origins**: `FRONTEND_URL=https://app.example.com,https://admin.example.com`
3. **Wildcard** (not recommended): `FRONTEND_URL=*` (requires `ALLOW_CORS_WILDCARD=true`)

### `ALLOW_CORS_WILDCARD` (Optional, default: `false`)

Must be set to `true` to allow wildcard CORS configuration.

**⚠️ Security Warning**: Wildcard CORS allows requests from ANY origin. Only use in development.

### `ENVIRONMENT` (Optional, default: `production`)

- **production**: Strict validation, no wildcard without explicit opt-in
- **development**: More lenient, defaults to localhost if `FRONTEND_URL` not set

## Valid Origin Formats

✅ `https://example.com`  
✅ `https://example.com:8080`  
✅ `https://subdomain.example.com`  
✅ `http://localhost:3000`  
✅ `http://127.0.0.1:3000`  

❌ `example.com` (missing scheme)  
❌ `ftp://example.com` (invalid scheme)  
❌ `http://` (missing domain)  

## Common Error Messages

### Missing Configuration
```
CORSConfigError: FRONTEND_URL must be configured
```
**Fix**: Set `FRONTEND_URL` environment variable

### Wildcard Not Allowed
```
CORSConfigError: Wildcard '*' origin detected in production environment
```
**Fix**: Use specific origins or set `ALLOW_CORS_WILDCARD=true`

### Invalid Format
```
CORSConfigError: Invalid CORS origin format: example.com
```
**Fix**: Add scheme (http:// or https://)

## Testing CORS

Run CORS tests:
```bash
pytest tests/test_config.py -v
pytest tests/test_cors_integration.py -v
```

Manual test with curl:
```bash
curl -X OPTIONS http://localhost:8000/health \
  -H "Origin: https://your-frontend.com" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

## Documentation

For detailed CORS configuration documentation, see:
- **[CORS_CONFIGURATION.md](CORS_CONFIGURATION.md)** - Complete configuration guide
- **[MIGRATION_CORS.md](MIGRATION_CORS.md)** - Migration guide from old configuration

## Security Best Practices

### ✅ DO
- Use specific origins (list all allowed domains)
- Use HTTPS in production
- Keep `allow_credentials=true` for cookie-based auth
- Review CORS origins regularly
- Test with actual frontend apps

### ❌ DON'T
- Don't use wildcard in production
- Don't use HTTP in production (except localhost in dev)
- Don't ignore startup errors
- Don't add untrusted origins

## Configuration Module

The new `config.py` module provides:

```python
from config import get_cors_config, get_cors_origins, CORSConfigError

# Get validated CORS origins
origins = get_cors_origins()

# Get complete CORS configuration
cors_config = get_cors_config()
```

## Troubleshooting

### Application Won't Start

1. Check `FRONTEND_URL` is set
2. Verify origins are valid URLs with schemes
3. If using wildcard, set `ALLOW_CORS_WILDCARD=true`

### Browser Shows CORS Error

1. Is the frontend origin in `FRONTEND_URL`?
2. Does the origin match exactly (protocol, domain, port)?
3. Is the backend running and accessible?

### Multiple Frontends, One Fails

1. Check all origins are in comma-separated list
2. Verify no typos in URLs
3. Ensure correct protocol and ports

---

# Hardened JWT Secret Key Handling (SDT1-63)

## Overview

JWT (JSON Web Token) secret key handling has been significantly hardened to prevent security vulnerabilities and ensure proper cryptographic security.

## Key Security Improvements

✅ **Strong Secret Validation** - Enforces minimum 32-character (256-bit) secrets  
✅ **Weak Secret Detection** - Rejects known weak/default secrets  
✅ **Environment Awareness** - Required in production, auto-generated in development  
✅ **Key Rotation Support** - Graceful key rotation without service interruption  
✅ **Algorithm Enforcement** - Fixed algorithms prevent algorithm confusion attacks  
✅ **Comprehensive Testing** - Full test coverage including security properties  
✅ **Clear Documentation** - Detailed guide for setup and best practices  

## Quick Start

### Generate a Secure Secret

```bash
# Use the provided script
python scripts/generate_jwt_secret.py

# Or generate directly
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### Development Environment

```bash
# In .env file (optional - will auto-generate if not set)
ENVIRONMENT=development
JWT_SECRET=your-generated-secret-here
JWT_EXPIRY_HOURS=24
```

### Production Environment

```bash
# In .env file or environment variables (REQUIRED)
ENVIRONMENT=production
JWT_SECRET=your-generated-secret-here
JWT_EXPIRY_HOURS=24
JWT_ALGORITHM=HS256
```

## Environment Variables

### `JWT_SECRET` (Required in Production)

The secret key used to sign JWT tokens.

**Requirements:**
- Minimum 32 characters (256 bits)
- Must not be a known weak secret
- Should be cryptographically random

**Generate:**
```bash
python scripts/generate_jwt_secret.py
```

**In Development:**
- Auto-generated if not set (temporary, per-session)
- Set `JWT_SECRET` for consistent tokens across restarts

**In Production:**
- Required - application will fail to start if not configured
- Must meet all security requirements

### `JWT_ALGORITHM` (Optional, default: `HS256`)

JWT signing algorithm.

**Allowed values:**
- `HS256` - HMAC with SHA-256 (default)
- `HS384` - HMAC with SHA-384
- `HS512` - HMAC with SHA-512

### `JWT_EXPIRY_HOURS` (Optional, default: `24`)

Token expiration time in hours.

**Requirements:**
- Must be at least 1 hour
- Values over 168 hours (7 days) generate a warning

### `JWT_SECRET_OLD` (Optional)

Previous JWT secret for key rotation.

**Use during key rotation:**
```bash
export JWT_SECRET_OLD='old-secret'
export JWT_SECRET='new-secret'
```

## Usage

### Basic Token Operations

```python
from jwt_utils import get_jwt_manager

# Get JWT manager instance
jwt_manager = get_jwt_manager()

# Create token
token = jwt_manager.create_token(
    user_id="user123",
    email="user@example.com"
)

# Decode/validate token
payload = jwt_manager.decode_token(token)
user_id = payload["sub"]

# Refresh token
new_token = jwt_manager.refresh_token(token)
```

### With Custom Claims

```python
# Create token with extra claims
token = jwt_manager.create_token(
    user_id="user123",
    email="user@example.com",
    role="admin",
    permissions=["read", "write"]
)

# Claims are preserved in refresh
new_token = jwt_manager.refresh_token(token)
```

### Error Handling

```python
from jwt_utils import JWTValidationError, JWTConfigError

try:
    payload = jwt_manager.decode_token(token)
except JWTValidationError as e:
    # Handle invalid/expired token
    print(f"Token validation failed: {e}")
```

## API Endpoints

### Token Refresh

```bash
POST /auth/refresh
Authorization: Bearer <your-token>
```

**Response:**
```json
{
  "access_token": "new.jwt.token",
  "token_type": "bearer"
}
```

## Security Features

### 1. Strong Secret Validation

- **Minimum 32 characters** (256 bits)
- **Rejects known weak secrets**: "secret", "password", "dev-secret-change-in-production", etc.
- **Pattern detection**: Checks for repetitive or common weak patterns

### 2. Algorithm Security

- **Fixed algorithms**: HS256, HS384, HS512 only
- **Prevents algorithm confusion**: Disallows "none" and asymmetric algorithms
- **Signature verification**: Always enabled, cannot be disabled

### 3. Key Rotation

Set both secrets during rotation:
```bash
export JWT_SECRET='new-secret'
export JWT_SECRET_OLD='old-secret'
```

Tokens signed with either secret are valid during transition.

### 4. Token Expiry

- All tokens have expiration time
- Expired tokens rejected by default
- Use refresh endpoint to extend expiry

## Common Issues

### "JWT_SECRET environment variable is required in production"

**Cause:** JWT_SECRET not set in production.

**Fix:**
```bash
python scripts/generate_jwt_secret.py
export JWT_SECRET='generated-secret'
```

### "JWT secret is too short"

**Cause:** Secret is less than 32 characters.

**Fix:** Generate a longer secret:
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### "Weak or default JWT secret detected"

**Cause:** Using a known weak secret.

**Fix:** Replace with cryptographically random secret.

### "Token has expired"

**Cause:** Token passed expiration time.

**Fix:** Use refresh endpoint:
```bash
POST /auth/refresh
Authorization: Bearer <expired-token>
```

## Testing

Run JWT security tests:
```bash
# All JWT tests
pytest uat/backend/tests/test_jwt_utils.py -v

# With coverage
pytest --cov=uat/backend/jwt_utils uat/backend/tests/test_jwt_utils.py

# Specific test class
pytest uat/backend/tests/test_jwt_utils.py::TestSecurityProperties -v
```

## Documentation

For detailed JWT security documentation, see:
- **[docs/JWT_SECURITY.md](../../docs/JWT_SECURITY.md)** - Complete security guide

## Key Rotation Process

1. **Set old secret:**
   ```bash
   export JWT_SECRET_OLD='current-secret'
   ```

2. **Set new secret:**
   ```bash
   export JWT_SECRET='new-secret'
   ```

3. **Deploy application** - Both secrets work during transition

4. **Wait for old tokens to expire** (default: 24 hours)

5. **Remove old secret:**
   ```bash
   unset JWT_SECRET_OLD
   ```

## Best Practices

### ✅ DO
- Use cryptographically random secrets (32+ characters)
- Rotate keys regularly (e.g., every 90 days)
- Use different secrets for dev/staging/production
- Store secrets securely (vault, secret manager)
- Monitor token validation failures
- Use reasonable expiry times (1-24 hours)

### ❌ DON'T
- Don't use weak or default secrets
- Don't commit secrets to version control
- Don't share secrets via email/chat
- Don't reuse secrets across environments
- Don't set expiry too long (>7 days)
- Don't ignore startup validation errors

## Migration Guide

### From Old Implementation

1. **Generate secret:**
   ```bash
   python scripts/generate_jwt_secret.py
   ```

2. **Set environment variable:**
   ```bash
   export JWT_SECRET='your-generated-secret'
   ```

3. **Update code** (if using JWT directly):
   ```python
   # Old
   import jwt
   token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
   
   # New
   from jwt_utils import get_jwt_manager
   jwt_manager = get_jwt_manager()
   token = jwt_manager.create_token(user_id, email)
   ```

4. **Test thoroughly:**
   ```bash
   pytest uat/backend/tests/test_jwt_utils.py
   ```

## Environment Variables Summary

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Frontend/CORS
FRONTEND_URL=http://localhost:3000
ALLOW_CORS_WILDCARD=false
ENVIRONMENT=development

# JWT (SDT1-63)
JWT_SECRET=your-secure-secret-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
# Optional for key rotation:
# JWT_SECRET_OLD=your-old-secret

# Rate Limiting
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_STORAGE_URI=memory://

# Logging
LOG_LEVEL=INFO

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=SynPro Virtual Dev Team
```

## Security Best Practices

1. **Never log sensitive data** - Middleware automatically redacts sensitive headers
2. **Use Redis in production** - Memory storage doesn't scale across multiple instances
3. **Set appropriate rate limits** - Balance UX and security
4. **Monitor logs** - Set up log aggregation and alerting
5. **Rotate JWT secrets regularly** - Change every 90 days
6. **Use HTTPS** - Always use TLS in production
7. **Validate CORS origins** - Only allow trusted domains
8. **Review CORS regularly** - Audit allowed origins when adding frontends
9. **Use strong JWT secrets** - Minimum 256 bits, cryptographically random
10. **Implement key rotation** - Use JWT_SECRET_OLD during transitions

## Performance Impact

- **Logging Middleware**: Minimal (<1ms per request)
- **Rate Limiting**: ~0.5-2ms (memory), ~2-5ms (Redis)
- **CORS Validation**: One-time at startup, no runtime impact
- **JWT Operations**: ~0.5-1ms (encode/decode)
- **Overall**: Negligible impact on response times

## Troubleshooting

### High Rate Limit Violations

If you see many `429` errors:
1. Check if legitimate users are blocked
2. Adjust limits in environment variables
3. Investigate potential abuse or bot traffic

### Missing Rate Limit Headers

Ensure limiter is properly initialized in `main.py`:
```python
app.state.limiter = limiter
```

### Logs Not Appearing

Check log level configuration:
```bash
export LOG_LEVEL=INFO
```

### CORS Issues

1. Check logs for CORS validation errors
2. Verify `FRONTEND_URL` matches frontend exactly
3. Run `pytest tests/test_config.py -v`
4. See [CORS_CONFIGURATION.md](CORS_CONFIGURATION.md)

### JWT Validation Failures

1. Check `JWT_SECRET` is set correctly
2. Verify secret meets security requirements (32+ chars)
3. Check token hasn't expired
4. Verify algorithm matches (default: HS256)
5. Run `pytest tests/test_jwt_utils.py -v`
