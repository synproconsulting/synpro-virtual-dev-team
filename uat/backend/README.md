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

JWT secret key handling has been significantly hardened to ensure secure token signing and prevent common security vulnerabilities.

## Key Security Improvements

✅ **Required JWT_SECRET in Production** - No default fallback values  
✅ **Automatic Validation** - Secrets validated for length, entropy, and insecure patterns  
✅ **Development Mode** - Auto-generates secure secrets if not provided  
✅ **Helpful Error Messages** - Clear guidance when configuration is incorrect  
✅ **Security Best Practices** - Implements NIST recommendations for HMAC key lengths  
✅ **Secret Generation Tools** - CLI tool for generating secure secrets  
✅ **Comprehensive Testing** - Full test coverage for all validation scenarios  

## Quick Start

### Production Environment

```bash
# Generate a secure secret
python uat/backend/generate_secret.py

# Add to .env file
JWT_SECRET=<generated-secret-here>
ENVIRONMENT=production
JWT_EXPIRY_HOURS=24
JWT_ALGORITHM=HS256
```

### Development Environment

```bash
# In .env file (JWT_SECRET is optional - will auto-generate)
ENVIRONMENT=development
JWT_EXPIRY_HOURS=24
```

## Generating Secure Secrets

### Using the CLI Tool

```bash
# Generate in .env format
python uat/backend/generate_secret.py

# Generate with custom length
python uat/backend/generate_secret.py --length 64

# Generate plain secret
python uat/backend/generate_secret.py --format plain
```

### Using Python

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

### Using OpenSSL

```bash
openssl rand -base64 48
```

## Security Requirements

### Secret Length
- **Minimum**: 32 characters
- **Recommended**: 64+ characters
- **Why**: NIST recommends at least 256 bits for HS256 HMAC keys

### Forbidden Patterns (Production)
- `secret`
- `changeme`
- `dev-secret`
- `default`
- `test`
- `password`
- Other common insecure patterns

### Entropy Requirements
Secrets with low randomness (entropy < 4.0 bits/char) trigger warnings.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | Yes (prod) | None | Cryptographically secure random string |
| `JWT_EXPIRY_HOURS` | No | 24 | Token expiry time in hours |
| `JWT_ALGORITHM` | No | HS256 | Algorithm (HS256, HS384, or HS512) |
| `ENVIRONMENT` | No | production | Environment type |
| `ALLOW_INSECURE_JWT_SECRET` | No | false | Bypass validation (NOT RECOMMENDED) |

## Common Error Messages

### Missing Secret (Production)
```
SecurityConfigError: JWT_SECRET must be set in production environment
```
**Fix**: Generate and set JWT_SECRET

### Insecure Pattern
```
SecurityConfigError: JWT_SECRET contains insecure pattern 'secret'
```
**Fix**: Generate a new secure random secret

### Too Short
```
SecurityConfigError: JWT_SECRET must be at least 32 characters long
```
**Fix**: Use a longer secret (recommended: 64+ characters)

### Invalid Algorithm
```
SecurityConfigError: JWT_ALGORITHM must be one of ['HS256', 'HS384', 'HS512']
```
**Fix**: Use a supported HMAC algorithm

## Testing JWT Security

Run security configuration tests:
```bash
pytest uat/backend/tests/test_security_config.py -v
```

## Documentation

For detailed JWT security documentation, see:
- **[docs/JWT_SECURITY.md](../../docs/JWT_SECURITY.md)** - Complete security guide

## Security Module

The new `security_config.py` module provides:

```python
from security_config import get_jwt_config, generate_secure_secret, SecurityConfigError

# Get validated JWT configuration
jwt_config = get_jwt_config()

# Generate a secure secret
secret = generate_secure_secret()
```

## Migration Guide

If you're using an insecure JWT_SECRET:

1. Generate a new secret:
   ```bash
   python uat/backend/generate_secret.py
   ```

2. Update .env file with new secret

3. Restart application (all users will need to log in again)

4. Notify users of the one-time re-authentication

## Environment Variables Summary

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT Security (SDT1-63)
JWT_SECRET=<generate-with-generate_secret.py>
JWT_EXPIRY_HOURS=24
JWT_ALGORITHM=HS256

# Frontend/CORS (SDT1-56)
FRONTEND_URL=http://localhost:3000
ALLOW_CORS_WILDCARD=false
ENVIRONMENT=development

# Rate Limiting (SDT1-45)
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

1. **Never commit secrets to git** - Use .env files (in .gitignore)
2. **Use environment-specific secrets** - Different secrets for dev/staging/production
3. **Rotate secrets periodically** - Change JWT secrets every 6-12 months
4. **Store secrets securely** - Use secret management tools (AWS Secrets Manager, HashiCorp Vault)
5. **Monitor for leaks** - Use tools like git-secrets or truffleHog
6. **Limit token lifetime** - Use reasonable JWT_EXPIRY_HOURS (24h is good)
7. **Never log sensitive data** - Middleware automatically redacts sensitive headers
8. **Use Redis in production** - Memory storage doesn't scale across instances
9. **Set appropriate rate limits** - Too strict affects UX, too relaxed allows abuse
10. **Use HTTPS** - Always use TLS in production
11. **Validate CORS origins** - Only allow trusted domains
12. **Review security regularly** - Audit configuration when deploying

## Performance Impact

- **Logging Middleware**: Minimal (<1ms per request)
- **Rate Limiting**: ~0.5-2ms per request (memory), ~2-5ms (Redis)
- **CORS Validation**: One-time at startup, no runtime impact
- **JWT Validation**: One-time at startup, no runtime impact
- **Overall**: Negligible impact on response times

## Troubleshooting

### Application Won't Start

**Error:** Security configuration error

**Fix:** Check that JWT_SECRET is set and valid (see error message for specifics)

### Tokens Invalid After Restart

**Cause:** JWT_SECRET changed (auto-generated in dev or rotated)

**Solution:** This is expected. Users need to log in again.

### Warning About Low Entropy

**Warning:** JWT_SECRET has low entropy

**Solution:** Generate a new secret with better randomness using provided tools

## Further Reading

- [NIST SP 800-107](https://csrc.nist.gov/publications/detail/sp/800-107/rev-1/final) - Cryptographic Key Management
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - JSON Web Token
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
