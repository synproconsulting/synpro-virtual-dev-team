# JWT Security Configuration

## Overview

This document describes the hardened JWT secret key handling implemented in SDT1-63. The system enforces secure JWT secret configuration with automatic validation and helpful error messages.

## Key Features

1. **Required JWT_SECRET in Production** - No default fallback values in production environments
2. **Automatic Validation** - Secrets are validated for length, entropy, and insecure patterns
3. **Development Mode** - Auto-generates secure secrets in development if not provided
4. **Helpful Error Messages** - Clear guidance when configuration is incorrect
5. **Security Best Practices** - Implements NIST recommendations for HMAC key lengths

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | Yes (production) | None | Cryptographically secure random string (min 32 chars) |
| `JWT_EXPIRY_HOURS` | No | 24 | Token expiry time in hours |
| `JWT_ALGORITHM` | No | HS256 | Algorithm to use (HS256, HS384, or HS512) |
| `ENVIRONMENT` | No | production | Environment type (development/production) |
| `ALLOW_INSECURE_JWT_SECRET` | No | false | Bypass validation (NOT RECOMMENDED) |

### Production Configuration

In production, you **must** set a secure JWT_SECRET:

```bash
# Generate a secure secret
python uat/backend/generate_secret.py

# Or use Python directly
python -c 'import secrets; print(secrets.token_urlsafe(48))'

# Add to .env file
JWT_SECRET=<generated-secret-here>
ENVIRONMENT=production
```

**Example .env:**
```bash
JWT_SECRET=xKj9mP2nQ7rS4tU8vW1yZ3aB5cD7eF9gH2iJ4kL6mN8oP0qR2sT4uV6wX8yZ0A1bC3dE5fG7hI9jK
ENVIRONMENT=production
JWT_EXPIRY_HOURS=24
JWT_ALGORITHM=HS256
```

### Development Configuration

In development, JWT_SECRET is optional. If not provided, the system will auto-generate a secure random secret:

```bash
ENVIRONMENT=development
# JWT_SECRET is optional - will be auto-generated
```

**Note:** Auto-generated secrets change on each restart, so all tokens will be invalidated on restart.

## Security Requirements

### Secret Length

- **Minimum:** 32 characters
- **Recommended:** 48+ bytes (64+ characters when base64-encoded)
- **Why:** NIST recommends at least 256 bits for HS256 HMAC keys

### Forbidden Patterns

The following patterns are **blocked in production**:
- `secret`
- `changeme`
- `change-in-production`
- `dev-secret`
- `default`
- `test`
- `password`
- `12345`
- `example`
- `placeholder`

### Entropy Requirements

Secrets with low randomness (entropy < 4.0 bits/char) will trigger a warning suggesting regeneration.

## Generating Secure Secrets

### Using the CLI Tool

```bash
# Generate a default secret in .env format
python uat/backend/generate_secret.py

# Generate with custom length
python uat/backend/generate_secret.py --length 64

# Generate in plain format (just the secret)
python uat/backend/generate_secret.py --format plain

# Generate and append to .env file
python uat/backend/generate_secret.py >> .env
```

### Using Python

```python
import secrets

# Generate a URL-safe secret (recommended)
secret = secrets.token_urlsafe(48)
print(f"JWT_SECRET={secret}")

# Or use the security_config module
from security_config import generate_secure_secret
secret = generate_secure_secret()
```

### Using Command Line

```bash
# Python one-liner
python -c 'import secrets; print(secrets.token_urlsafe(48))'

# Using openssl (Unix/Linux/Mac)
openssl rand -base64 48

# Using /dev/urandom (Unix/Linux/Mac)
head -c 48 /dev/urandom | base64
```

## Error Messages

### Missing Secret in Production

```
SecurityConfigError: JWT_SECRET must be set in production environment.
Generate a secure secret with: python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

**Solution:** Generate and set JWT_SECRET environment variable.

### Insecure Pattern Detected

```
SecurityConfigError: JWT_SECRET contains insecure pattern 'secret'.
In production, use a cryptographically secure random secret.
```

**Solution:** Generate a new secure random secret.

### Secret Too Short

```
SecurityConfigError: JWT_SECRET must be at least 32 characters long for security.
Current length: 16 characters. Use a cryptographically secure random string.
```

**Solution:** Generate a longer secret (recommended: 64+ characters).

### Invalid Algorithm

```
SecurityConfigError: JWT_ALGORITHM must be one of ['HS256', 'HS384', 'HS512']. Got: RS256
```

**Solution:** Use a supported HMAC algorithm (HS256, HS384, or HS512).

## Validation Bypass (NOT RECOMMENDED)

In rare cases (testing, demo environments), you can bypass validation:

```bash
JWT_SECRET=weak-secret-for-demo
ALLOW_INSECURE_JWT_SECRET=true
ENVIRONMENT=production
```

**WARNING:** This should **NEVER** be used in production environments handling real data.

## Testing

Run the security configuration tests:

```bash
cd uat/backend
pytest tests/test_security_config.py -v
```

Expected output:
```
tests/test_security_config.py::TestEntropyCalculation::test_empty_string_entropy PASSED
tests/test_security_config.py::TestEntropyCalculation::test_high_entropy_string PASSED
tests/test_security_config.py::TestJWTSecretValidation::test_empty_secret_raises_error PASSED
...
```

## Migration Guide

### From Insecure Configuration

If you're currently using an insecure JWT_SECRET:

1. **Generate a new secure secret:**
   ```bash
   python uat/backend/generate_secret.py
   ```

2. **Update your .env file:**
   ```bash
   JWT_SECRET=<new-secure-secret>
   ```

3. **Restart the application:**
   ```bash
   # All existing tokens will be invalidated
   # Users will need to log in again
   ```

4. **Notify users:**
   - Inform users that they'll need to log in again
   - This is a one-time disruption for improved security

### From No JWT_SECRET (Development)

If you're moving from development to production:

1. **Generate a production secret:**
   ```bash
   python uat/backend/generate_secret.py >> .env.production
   ```

2. **Set ENVIRONMENT variable:**
   ```bash
   ENVIRONMENT=production
   ```

3. **Deploy with new configuration**

## Best Practices

1. **Never commit secrets to git** - Use .env files (listed in .gitignore)
2. **Use environment-specific secrets** - Different secrets for dev/staging/production
3. **Rotate secrets periodically** - Change JWT secrets every 6-12 months
4. **Store secrets securely** - Use secret management tools (AWS Secrets Manager, HashiCorp Vault, etc.)
5. **Monitor for leaks** - Use tools like git-secrets or truffleHog
6. **Limit token lifetime** - Use reasonable JWT_EXPIRY_HOURS (default 24h is good)
7. **Document secret rotation** - Have a process for emergency secret rotation

## Secret Rotation Process

If you need to rotate JWT secrets:

1. **Generate new secret:**
   ```bash
   python uat/backend/generate_secret.py
   ```

2. **Update environment configuration:**
   ```bash
   JWT_SECRET=<new-secret>
   ```

3. **Deploy changes:**
   - Use rolling deployment if possible
   - Accept that users will be logged out
   - Plan rotation during low-traffic periods

4. **Monitor for issues:**
   - Watch for increased authentication errors
   - Ensure users can log in successfully

## Troubleshooting

### Application Won't Start

**Error:** `SecurityConfigError: JWT_SECRET must be set in production environment`

**Solution:** Set JWT_SECRET environment variable with a secure random string.

### Tokens Are Invalid After Restart

**Cause:** JWT_SECRET changed (auto-generated in development or rotated)

**Solution:** This is expected behavior. Users need to log in again.

### Warning About Low Entropy

**Warning:** `JWT_SECRET has low entropy (2.50 bits/char)`

**Solution:** Generate a new secret with better randomness using the provided tools.

## References

- [NIST Special Publication 800-107](https://csrc.nist.gov/publications/detail/sp/800-107/rev-1/final) - Recommendation for Applications Using Approved Hash Algorithms
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - JSON Web Token (JWT)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

## Support

For questions or issues:
1. Check this documentation
2. Review error messages carefully
3. Run tests: `pytest tests/test_security_config.py -v`
4. Check application logs for warnings
5. Consult the security team for production deployments
