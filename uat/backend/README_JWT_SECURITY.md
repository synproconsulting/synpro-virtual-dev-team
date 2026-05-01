# JWT Security Implementation (SDT1-63)

This document describes the hardened JWT (JSON Web Token) secret key handling implemented in the UAT backend.

## Overview

The JWT security implementation provides:

- ✅ **Automatic secret validation** on application startup
- ✅ **Zero-downtime key rotation** support
- ✅ **Entropy and complexity checks** for secrets
- ✅ **Comprehensive security logging**
- ✅ **CLI tools** for secret management
- ✅ **Extensive test coverage**

## Quick Start

### 1. Generate a Secure Secret

```bash
# Method 1: Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: Using the CLI tool
python uat/backend/cli_jwt.py generate

# Method 3: Using OpenSSL
openssl rand -base64 32
```

### 2. Configure Environment

Add to your `.env` file:

```bash
JWT_SECRET=<generated-secret-here>
JWT_EXPIRY_HOURS=24
```

### 3. Verify Configuration

```bash
python uat/backend/cli_jwt.py info
```

Expected output:
```
JWT Configuration
✓ JWT_SECRET is configured
  Preview: vK8Qx3Zt...yR9qM2pL4k
  Length: 43 characters
  Entropy: 5.23 bits/char

Token Expiry: 24 hours
ℹ Key rotation not configured (no old secrets)

Algorithm: HS256

✓ Configuration is valid
```

## Features

### Secret Validation

The application automatically validates JWT secrets on startup:

```python
from jwt_config import get_jwt_config, JWTConfigError

try:
    config = get_jwt_config()
    # Application starts successfully
except JWTConfigError as e:
    # Application fails fast with clear error message
    print(f"JWT Configuration Error: {e}")
```

**Validation Checks:**
- ❌ Empty or missing secret
- ❌ Too short (< 32 characters)
- ❌ Common weak patterns ("secret", "dev-secret", "test", etc.)
- ❌ Low character diversity
- ⚠️ Low entropy warning (< 3.5 bits/char)

### Key Rotation

Support for zero-downtime JWT secret rotation:

```bash
# Step 1: Generate new secret
NEW_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Step 2: Update .env with both secrets
JWT_SECRET=$NEW_SECRET
JWT_SECRET_OLD=<current-secret>

# Step 3: Deploy application
# - New tokens use new secret
# - Old tokens still validate

# Step 4: After token expiry period, remove old secret
# JWT_SECRET=<new-secret>
# (remove JWT_SECRET_OLD)
```

See [JWT Security Guide](../../docs/JWT_SECURITY.md) for detailed rotation process.

### Token Creation

```python
from jwt_config import get_jwt_config

config = get_jwt_config()

# Create a token
token = config.create_token(
    user_id="user123",
    email="user@example.com"
)

# Create with extra claims
token = config.create_token(
    user_id="user123",
    email="user@example.com",
    extra_claims={"role": "admin", "tier": "premium"}
)
```

### Token Validation

```python
from jwt_config import get_jwt_config

config = get_jwt_config()

# Method 1: Decode (raises exceptions)
try:
    payload = config.decode_token(token)
    user_id = payload["sub"]
except jwt.ExpiredSignatureError:
    # Token expired
    pass
except jwt.InvalidTokenError:
    # Invalid token
    pass

# Method 2: Validate (returns tuple)
is_valid, payload, error = config.validate_token(token)
if is_valid:
    user_id = payload["sub"]
else:
    print(f"Invalid token: {error}")
```

## CLI Tools

The JWT CLI tool provides utilities for secret management:

### Generate Secret
```bash
python uat/backend/cli_jwt.py generate
```

### Validate Secret
```bash
python uat/backend/cli_jwt.py validate "your-secret-here"
```

### Show Configuration
```bash
python uat/backend/cli_jwt.py info
```

### Create Test Token
```bash
python uat/backend/cli_jwt.py create user123 test@example.com
```

### Decode Token
```bash
python uat/backend/cli_jwt.py decode "eyJhbGc..."
```

See [JWT CLI README](README_JWT_CLI.md) for detailed CLI documentation.

## Testing

### Run Tests

```bash
# Run JWT configuration tests
pytest uat/backend/tests/test_jwt_config.py -v

# Run authentication integration tests
pytest uat/backend/tests/test_auth_jwt.py -v

# Run all tests with coverage
pytest uat/backend/tests/ --cov=uat/backend --cov-report=html
```

### Test Coverage

The implementation includes comprehensive tests:

- ✅ Secret validation (entropy, length, patterns)
- ✅ Secret generation
- ✅ JWT configuration initialization
- ✅ Token creation and expiry
- ✅ Token decoding and validation
- ✅ Key rotation support
- ✅ Error handling
- ✅ Security logging
- ✅ Integration with auth endpoints

## Security Best Practices

### 1. Never Hardcode Secrets

❌ **Bad:**
```python
JWT_SECRET = "my-secret-key"
```

✅ **Good:**
```python
JWT_SECRET = os.environ.get("JWT_SECRET")
```

### 2. Use Strong Secrets

Generate secrets with high entropy:

```bash
# ✅ Good - cryptographically random
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ❌ Bad - weak pattern
JWT_SECRET=dev-secret-change-in-production
```

### 3. Rotate Regularly

Rotate JWT secrets:
- On suspected compromise
- When employees with access leave
- Annually as part of security maintenance

### 4. Use Short Expiry Times

Balance security vs. UX:
- **High security**: 1-4 hours
- **Standard**: 24 hours (default)
- **Maximum**: 168 hours (1 week)

### 5. Monitor Logs

Watch for security events:
- Failed login attempts
- Token validation failures
- Use of old secrets during rotation

## Environment Variables

### Required

- `JWT_SECRET` - Primary JWT secret (min 32 chars, high entropy)

### Optional

- `JWT_EXPIRY_HOURS` - Token expiry in hours (default: 24)
- `JWT_SECRET_OLD` - Comma-separated old secrets for rotation

### Example .env

```bash
# Required
JWT_SECRET=vK8Qx3ZtN9mP2wR5yJ7sL1nF4hD6gA8cE0bT3xW5yR9qM2pL4k

# Optional
JWT_EXPIRY_HOURS=24
JWT_SECRET_OLD=old_secret_1,old_secret_2
```

## Architecture

### Module Structure

```
uat/backend/
├── jwt_config.py              # Core JWT configuration module
├── auth.py                    # Authentication endpoints (uses jwt_config)
├── cli_jwt.py                 # CLI tool for secret management
├── tests/
│   ├── test_jwt_config.py     # Unit tests for jwt_config
│   └── test_auth_jwt.py       # Integration tests for auth
└── README_JWT_SECURITY.md     # This file
```

### Key Components

1. **jwt_config.py** - Core module
   - `JWTConfig` - Main configuration class
   - `get_jwt_config()` - Singleton instance
   - `generate_secure_secret()` - Secret generation
   - Validation functions

2. **auth.py** - Authentication
   - `create_jwt()` - Token creation helper
   - `decode_jwt()` - Token validation helper
   - Uses `get_jwt_config()` internally

3. **cli_jwt.py** - Management CLI
   - Secret generation
   - Secret validation
   - Configuration inspection
   - Token creation/decoding

## Troubleshooting

### Error: "JWT_SECRET environment variable is required"

**Solution:**
```bash
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Error: "JWT secret must be at least 32 characters long"

**Solution:** Generate a longer secret:
```bash
python uat/backend/cli_jwt.py generate
```

### Error: "JWT secret contains weak/common pattern"

**Solution:** Don't use common patterns like "secret", "dev", "test":
```bash
python uat/backend/cli_jwt.py generate
```

### Error: "Token expired"

**Cause:** Token older than JWT_EXPIRY_HOURS

**Solution:** User must log in again to get new token

### Error: "Invalid token"

**Causes:**
1. Token signed with different secret
2. Token modified/corrupted
3. Malformed token

**Solution:**
1. Check JWT_SECRET matches between environments
2. During rotation, set JWT_SECRET_OLD
3. User must log in again

## Documentation

- [JWT Security Guide](../../docs/JWT_SECURITY.md) - Comprehensive security documentation
- [JWT CLI Tool](README_JWT_CLI.md) - CLI tool documentation
- [.env.example](../../.env.example) - Environment variable examples

## Migration from Old Implementation

### Before (Weak)

```python
# auth.py - OLD
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")

token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
```

### After (Hardened)

```python
# auth.py - NEW
from jwt_config import get_jwt_config

jwt_config = get_jwt_config()  # Validates on initialization

token = jwt_config.create_token(user_id, email)
payload = jwt_config.decode_token(token)
```

### Migration Steps

1. Generate strong secret:
   ```bash
   python uat/backend/cli_jwt.py generate
   ```

2. Update .env:
   ```bash
   JWT_SECRET=<new-strong-secret>
   ```

3. Application code is already updated (auth.py uses jwt_config)

4. Restart application:
   - Validates secret on startup
   - Fails fast if secret is weak

## Support

For security issues or questions:
- Check [JWT Security Guide](../../docs/JWT_SECURITY.md)
- Review test cases for examples
- Contact security team for sensitive issues

⚠️ **Never post secrets or tokens in public channels or issue trackers**
