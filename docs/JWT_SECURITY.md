# JWT Security Hardening (SDT1-63)

This document describes the JWT secret key hardening implementation and best practices.

## Overview

The JWT security hardening implementation provides:

- **Strong Secret Validation**: Enforces minimum secret length and rejects known weak secrets
- **Environment-Aware Configuration**: Strict requirements in production, relaxed in development
- **Key Rotation Support**: Allows seamless key rotation without service interruption
- **Algorithm Enforcement**: Prevents algorithm confusion attacks
- **Comprehensive Error Handling**: Clear error messages for misconfigurations

## Configuration

### Required Environment Variables

#### `JWT_SECRET` (Required in Production)

The secret key used to sign JWT tokens.

**Requirements:**
- Minimum 32 characters (256 bits)
- Must not be a known weak secret (e.g., "secret", "password")
- Should be cryptographically random

**Generate a secure secret:**
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

**Example:**
```bash
export JWT_SECRET='your-secure-random-secret-here'
```

**Development Mode:**
- If not set in development, a temporary secret is auto-generated
- The temporary secret only lasts for the current session
- Set `JWT_SECRET` for consistent tokens across restarts

**Production Mode:**
- `JWT_SECRET` is required and must be set
- Application will fail to start if not configured
- Must meet all security requirements

### Optional Environment Variables

#### `JWT_ALGORITHM` (Default: HS256)

The algorithm used to sign JWT tokens.

**Allowed values:**
- `HS256` (HMAC with SHA-256) - Default
- `HS384` (HMAC with SHA-384)
- `HS512` (HMAC with SHA-512)

**Example:**
```bash
export JWT_ALGORITHM='HS256'
```

#### `JWT_EXPIRY_HOURS` (Default: 24)

Token expiry time in hours.

**Requirements:**
- Must be at least 1 hour
- Values over 168 hours (7 days) will generate a warning

**Example:**
```bash
export JWT_EXPIRY_HOURS='24'
```

#### `JWT_SECRET_OLD`

Previous JWT secret for key rotation.

**Use case:**
When rotating keys, set this to your old secret to allow tokens signed with the old key to still be validated during the transition period.

**Example:**
```bash
export JWT_SECRET='new-secret'
export JWT_SECRET_OLD='old-secret'
```

**Process:**
1. Set `JWT_SECRET_OLD` to current `JWT_SECRET`
2. Set `JWT_SECRET` to new secret
3. Deploy application
4. Wait for all old tokens to expire (or refresh them)
5. Remove `JWT_SECRET_OLD`

#### `ENVIRONMENT` (Default: production)

Environment type for configuration validation.

**Values:**
- `production` - Strict validation, no defaults
- `development` - Relaxed validation, auto-generation allowed

**Example:**
```bash
export ENVIRONMENT='development'
```

## Usage

### Basic Usage

```python
from jwt_utils import get_jwt_manager

# Initialize JWT manager (reads from environment)
jwt_manager = get_jwt_manager()

# Create token
token = jwt_manager.create_token(
    user_id="user123",
    email="user@example.com"
)

# Decode token
payload = jwt_manager.decode_token(token)
user_id = payload["sub"]
email = payload["email"]

# Refresh token
new_token = jwt_manager.refresh_token(token)
```

### With Extra Claims

```python
# Create token with custom claims
token = jwt_manager.create_token(
    user_id="user123",
    email="user@example.com",
    role="admin",
    permissions=["read", "write", "delete"]
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

## Security Features

### 1. Secret Validation

**Minimum Length:**
- Secrets must be at least 32 characters (256 bits)
- This prevents brute-force attacks on weak secrets

**Known Weak Secrets:**
The following secrets are automatically rejected:
- `dev-secret-change-in-production`
- `secret`
- `secret123`
- `changeme`
- `password`
- `jwt_secret`
- `your-secret-key`
- `my-secret`
- `test-secret`

**Pattern Detection:**
In production, secrets are checked for:
- Repetitive patterns (e.g., "aaaaaaa...")
- Common weak patterns (e.g., "12345", "qwerty")

### 2. Algorithm Enforcement

**Fixed Algorithm:**
- Algorithm is specified in configuration
- Cannot be changed by client
- Prevents algorithm confusion attacks

**Disallowed Algorithms:**
- `none` - Prevents bypass attacks
- Asymmetric algorithms (RS256, ES256, etc.) - Use HS256/384/512 with shared secret

### 3. Signature Verification

**Always Enabled:**
- Signature verification cannot be disabled
- Tokens signed with wrong secret are rejected
- Tampered tokens are detected and rejected

### 4. Expiry Enforcement

**Token Expiry:**
- All tokens have expiration time
- Expired tokens are rejected by default
- Refresh endpoint allows extending expiry

### 5. Key Rotation

**Gradual Rotation:**
- Set `JWT_SECRET_OLD` to old secret
- Tokens signed with either secret are valid
- Remove old secret after transition period

## Common Issues

### Issue: "JWT_SECRET environment variable is required in production"

**Cause:** `JWT_SECRET` is not set in production environment.

**Solution:**
```bash
# Generate a secure secret
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Set the environment variable
export JWT_SECRET='generated-secret-here'
```

### Issue: "JWT secret is too short"

**Cause:** Secret is less than 32 characters.

**Solution:** Generate a longer secret:
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### Issue: "Weak or default JWT secret detected"

**Cause:** Using a known weak secret like "secret" or "dev-secret-change-in-production".

**Solution:** Replace with a cryptographically random secret.

### Issue: "Token has expired"

**Cause:** Token has passed its expiration time.

**Solution:** Use the refresh endpoint to get a new token:
```python
POST /auth/refresh
Authorization: Bearer <expired-token>
```

### Issue: "Invalid token"

**Possible causes:**
1. Token was tampered with
2. Token was signed with wrong secret
3. Token is malformed

**Solution:** Check token generation and ensure correct secret is configured.

## Best Practices

### 1. Secret Generation

**Always use cryptographically random secrets:**
```bash
# Good
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Bad
echo "my-secret-123"
```

### 2. Secret Storage

**Never commit secrets to version control:**
```bash
# Use environment variables
export JWT_SECRET='...'

# Or use secret management services
# - AWS Secrets Manager
# - HashiCorp Vault
# - Azure Key Vault
```

### 3. Token Expiry

**Use reasonable expiry times:**
- Short-lived tokens (1-24 hours) for web applications
- Use refresh tokens for long-lived sessions
- Consider user activity when setting expiry

### 4. Key Rotation

**Rotate keys regularly:**
1. Schedule key rotation (e.g., every 90 days)
2. Use `JWT_SECRET_OLD` during transition
3. Monitor token validation errors
4. Remove old secret after all tokens expire

### 5. Monitoring

**Monitor for security events:**
- Failed token validations
- Expired tokens
- Invalid signatures
- Algorithm confusion attempts

## Testing

Run JWT security tests:
```bash
# Run all JWT tests
pytest uat/backend/tests/test_jwt_utils.py

# Run with coverage
pytest --cov=uat/backend/jwt_utils uat/backend/tests/test_jwt_utils.py

# Run specific test class
pytest uat/backend/tests/test_jwt_utils.py::TestSecurityProperties
```

## Migration Guide

### Migrating from Old Implementation

If you're migrating from the previous JWT implementation:

1. **Install dependencies** (already in requirements.txt):
   ```bash
   pip install pyjwt==2.8.0
   ```

2. **Generate a secure secret:**
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

3. **Set environment variables:**
   ```bash
   export JWT_SECRET='your-generated-secret'
   export ENVIRONMENT='production'
   ```

4. **Update code** (if using JWT directly):
   ```python
   # Old
   import jwt
   token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
   
   # New
   from jwt_utils import get_jwt_manager
   jwt_manager = get_jwt_manager()
   token = jwt_manager.create_token(user_id, email)
   ```

5. **Test thoroughly:**
   ```bash
   pytest uat/backend/tests/test_jwt_utils.py
   pytest uat/backend/tests/test_auth.py  # If exists
   ```

## References

- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

## Support

For issues or questions about JWT security:
1. Check this documentation
2. Review test cases in `test_jwt_utils.py`
3. Check application logs for detailed error messages
4. Contact the development team
