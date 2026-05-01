# JWT Security Guide

## Overview

This document describes the hardened JWT (JSON Web Token) implementation in the SynPro Virtual Dev Team platform (SDT1-63).

## Features

### 1. **Secret Key Validation**

JWT secrets are automatically validated on application startup:

- **Minimum Length**: 32 characters (configurable)
- **Entropy Check**: Minimum 3.5 bits/character Shannon entropy
- **Character Diversity**: At least 25% unique characters
- **Weak Secret Detection**: Common patterns like "secret", "dev-secret", "test-secret" are rejected
- **Production Safety**: Application fails fast if JWT_SECRET is weak or missing

### 2. **Key Rotation Support**

Zero-downtime key rotation is supported:

```bash
# Step 1: Add new secret alongside old one
JWT_SECRET=new_secret_here
JWT_SECRET_OLD=old_secret_here

# Step 2: Deploy - both secrets work
# Existing tokens validate with old secret
# New tokens use new secret

# Step 3: After token expiry period, remove old secret
JWT_SECRET=new_secret_here
# JWT_SECRET_OLD removed
```

**How it works:**
- Tokens are always created with `JWT_SECRET` (primary)
- Validation tries `JWT_SECRET` first, then each secret in `JWT_SECRET_OLD`
- Logs when old secrets are used (helps monitor rotation progress)

### 3. **Secure Defaults**

- Algorithm: `HS256` (HMAC-SHA256)
- Default Expiry: 24 hours (configurable via `JWT_EXPIRY_HOURS`)
- Expiry Validation: Enforces 1-168 hour range (1 hour to 1 week)
- No weak algorithms (RS256, none, etc.)

### 4. **Comprehensive Error Handling**

Clear error messages for different failure modes:
- `Token expired` - Token past expiration time
- `Invalid token` - Malformed or wrong signature
- `Authentication error` - Unexpected errors

### 5. **Security Logging**

All security-relevant events are logged:
- Failed login attempts (WARNING level)
- Successful logins (INFO level)
- Token validation with old secrets (INFO level - indicates rotation)
- JWT configuration errors (ERROR level)

## Configuration

### Required Environment Variables

```bash
# REQUIRED: Primary JWT secret
JWT_SECRET=<strong-random-secret>

# Generate with:
python -c "import secrets; print(secrets.token_urlsafe(32))"
# or
openssl rand -base64 32
```

### Optional Environment Variables

```bash
# Token expiry in hours (default: 24)
JWT_EXPIRY_HOURS=24

# Old secrets for key rotation (comma-separated)
JWT_SECRET_OLD=old_secret_1,old_secret_2
```

## Generating Secure Secrets

### Method 1: Python (Recommended)

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Output example:
```
vK8Qx3ZtN9mP2wR5yJ7sL1nF4hD6gA8cE0bT3xW5yR9qM2pL4k
```

### Method 2: OpenSSL

```bash
openssl rand -base64 32
```

### Method 3: Using jwt_config module

```python
from jwt_config import generate_secure_secret

secret = generate_secure_secret()
print(f"JWT_SECRET={secret}")
```

## Key Rotation Process

### When to Rotate

Rotate JWT secrets when:
- Suspected compromise
- Employee departure who had access
- Regular security maintenance (e.g., annually)
- Regulatory compliance requirements

### Rotation Steps

1. **Generate new secret:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Update environment with both secrets:**
   ```bash
   JWT_SECRET=<new-secret>
   JWT_SECRET_OLD=<old-secret>
   ```

3. **Deploy application:**
   - Application starts accepting both secrets
   - New tokens use new secret
   - Old tokens still validate

4. **Monitor logs:**
   ```
   Token validated with old secret #1 (user: abc123)
   ```
   Track how many users still have old tokens

5. **Wait for token expiry period:**
   - Default: 24 hours
   - Custom: Your `JWT_EXPIRY_HOURS` value
   - Add buffer for safety

6. **Remove old secret:**
   ```bash
   JWT_SECRET=<new-secret>
   # Remove JWT_SECRET_OLD
   ```

7. **Deploy again:**
   - Only new secret is accepted
   - Old tokens will fail validation

### Emergency Rotation

For immediate revocation (e.g., security breach):

```bash
# Remove old secret immediately
JWT_SECRET=<new-secret>
# Don't set JWT_SECRET_OLD
```

**Impact**: All existing tokens become invalid immediately. Users must log in again.

## Token Structure

### Standard Claims

```json
{
  "sub": "user-uuid",           // Subject: User ID
  "email": "user@example.com",  // User email
  "iat": 1234567890,            // Issued At: Unix timestamp
  "exp": 1234654290             // Expiry: Unix timestamp
}
```

### Custom Claims

Additional claims can be added:

```python
from jwt_config import get_jwt_config

config = get_jwt_config()
token = config.create_token(
    user_id="abc123",
    email="user@example.com",
    extra_claims={
        "role": "admin",
        "tier": "premium"
    }
)
```

## Security Best Practices

### 1. **Never Hardcode Secrets**

❌ **Bad:**
```python
JWT_SECRET = "my-secret-key"
```

✅ **Good:**
```python
JWT_SECRET = os.environ.get("JWT_SECRET")
```

### 2. **Use Environment Variables**

Store secrets in:
- Environment variables
- Secret management systems (AWS Secrets Manager, HashiCorp Vault, etc.)
- Kubernetes Secrets
- Docker secrets

Never in:
- Source code
- Configuration files in repo
- Logs
- Error messages

### 3. **Validate on Startup**

The application validates JWT configuration on startup and fails fast if invalid:

```python
# This happens automatically when the app starts
from jwt_config import get_jwt_config

config = get_jwt_config()  # Raises JWTConfigError if invalid
```

### 4. **Monitor Token Usage**

Check logs for:
- Failed login attempts
- Token validation failures
- Use of old secrets (during rotation)

### 5. **Short Expiry Times**

Balance security vs. user experience:
- **High security**: 1-4 hours
- **Standard**: 24 hours (default)
- **Low security**: Up to 1 week (max)

Longer tokens = longer window for compromise.

### 6. **HTTPS Only**

Always use HTTPS in production:
- JWT tokens in headers are visible over HTTP
- HTTPS encrypts all traffic including tokens

### 7. **Secure Token Storage (Frontend)**

Client-side token storage options:

| Storage | Security | Notes |
|---------|----------|-------|
| Memory | ✅ Best | Lost on page refresh |
| httpOnly cookie | ✅ Good | Protected from XSS |
| localStorage | ⚠️ Risky | Vulnerable to XSS |
| sessionStorage | ⚠️ Risky | Vulnerable to XSS |

**Recommendation**: Use httpOnly, secure, SameSite cookies.

## Testing

### Unit Tests

```bash
# Run JWT configuration tests
pytest uat/backend/tests/test_jwt_config.py -v

# Run auth integration tests
pytest uat/backend/tests/test_auth_jwt.py -v
```

### Manual Testing

#### Test Valid Token
```bash
# Register/login to get token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}' \
  | jq -r .access_token)

# Use token
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

#### Test Expired Token
```python
# Create expired token for testing
from jwt_config import JWTConfig
from datetime import datetime, timezone, timedelta
import jwt

config = JWTConfig()
payload = {
    "sub": "user123",
    "email": "test@example.com",
    "iat": datetime.now(timezone.utc) - timedelta(hours=25),
    "exp": datetime.now(timezone.utc) - timedelta(hours=1)
}
expired = jwt.encode(payload, config.primary_secret, algorithm="HS256")
print(expired)
```

## Troubleshooting

### Error: "JWT_SECRET environment variable is required"

**Cause**: JWT_SECRET not set

**Solution**:
```bash
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Error: "JWT secret must be at least 32 characters long"

**Cause**: JWT_SECRET is too short

**Solution**: Generate a longer secret (see "Generating Secure Secrets")

### Error: "JWT secret contains weak/common pattern"

**Cause**: Using a common/weak secret like "secret" or "dev-secret"

**Solution**: Generate a cryptographically random secret

### Error: "Token expired"

**Cause**: Token older than JWT_EXPIRY_HOURS

**Solution**: User must log in again to get a new token

### Error: "Invalid token"

**Causes**:
1. Token signed with different secret
2. Token modified/corrupted
3. Malformed token

**Solution**:
1. Check JWT_SECRET matches between token creation and validation
2. During key rotation, ensure JWT_SECRET_OLD is set
3. User must log in again

## Migration Guide

### From Hardcoded Secret

**Before:**
```python
JWT_SECRET = "dev-secret-change-in-production"
```

**After:**
```python
# In environment
JWT_SECRET=vK8Qx3ZtN9mP2wR5yJ7sL1nF4hD6gA8cE0bT3xW5yR9qM2pL4k

# In code
from jwt_config import get_jwt_config
config = get_jwt_config()
token = config.create_token(user_id, email)
```

### From jwt.encode/decode

**Before:**
```python
import jwt

token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
```

**After:**
```python
from jwt_config import get_jwt_config

config = get_jwt_config()
token = config.create_token(user_id, email)
payload = config.decode_token(token)
```

## References

- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

## Support

For security issues, contact the security team immediately. Do not post secrets or tokens in public channels.
