# JWT Secret Key Hardening (SDT1-63)

## Overview

This document describes the JWT secret key hardening implementation that ensures secure JWT token signing in production environments.

## Features

### 1. **Automatic Secret Validation**

The application validates JWT secrets on startup and rejects weak or insecure configurations:

- ✅ Checks secret length (minimum 32 characters)
- ✅ Validates entropy (minimum 128 bits recommended)
- ✅ Detects common weak secrets (e.g., "secret", "password", "test")
- ✅ Identifies default/placeholder values (e.g., "change-me", "dev-secret")
- ✅ Prevents repeated character patterns
- ✅ Fails fast in production if secret is missing or weak

### 2. **Secure Secret Generation**

Built-in utility to generate cryptographically secure secrets:

```bash
# Generate a secure secret (64 bytes = 512 bits)
python generate_jwt_secret.py

# Generate with custom length
python generate_jwt_secret.py --length 32

# Validate an existing secret
python generate_jwt_secret.py --validate "your-secret-here"
```

### 3. **Environment-Aware Configuration**

Different rules for different environments:

| Environment | JWT_SECRET Required | Weak Secrets Allowed | Behavior |
|-------------|---------------------|----------------------|----------|
| **Production** | ✅ Yes | ❌ No | Fails if missing or weak |
| **Development** | ⚠️ Optional | ⚠️ With flag only | Auto-generates if missing |

### 4. **Fail-Fast Security**

The application will not start if the JWT configuration is insecure:

```python
# On startup
JWTConfigError: JWT_SECRET environment variable must be set in production.
Generate a secure secret using: python -c "from config import generate_jwt_secret; print(generate_jwt_secret())"
```

## Configuration

### Required Environment Variables

```bash
# Production
ENVIRONMENT=production
JWT_SECRET=<your-secure-secret>  # Required, must be strong

# Development
ENVIRONMENT=development
JWT_SECRET=<optional>  # If not set, auto-generated
```

### Optional Environment Variables

```bash
# Token expiry time (default: 24 hours)
JWT_EXPIRY_HOURS=24

# Allow weak secrets in development (not recommended)
ALLOW_WEAK_JWT_SECRET=true
```

## Usage Guide

### Generate a New Secret

```bash
# Run the generator
python generate_jwt_secret.py

# Output:
# Generated secure JWT secret (64 bytes, ~512 bits entropy):
# h8Kx2Vp9M3Qr5Ts7Uv9Wx1Yz3Ab5Cd7Ef9Gh1Ij3Kl5Mn7Op9Qr1St3Uv5Wx7Yz9Ab1Cd3Ef5Gh7Ij9==
#
# To use this secret, add it to your environment variables:
# export JWT_SECRET="h8Kx2Vp9M3Qr5Ts7Uv9Wx1Yz3Ab5Cd7Ef9Gh1Ij3Kl5Mn7Op9Qr1St3Uv5Wx7Yz9Ab1Cd3Ef5Gh7Ij9=="
```

### Validate an Existing Secret

```bash
python generate_jwt_secret.py --validate "your-secret-here"

# Output for weak secret:
# ❌ Secret is weak: Secret is too short (minimum 32 characters recommended, got 15)

# Output for strong secret:
# ✓ Secret appears to be strong
```

### Deployment

See full deployment guide:

```bash
python generate_jwt_secret.py --help-deploy
```

## Security Best Practices

### ✅ DO

1. **Generate strong secrets**: Use the provided generator script
2. **Use different secrets per environment**: Dev, staging, and production should have unique secrets
3. **Store securely**: Use environment variables, secrets managers (AWS Secrets Manager, Azure Key Vault)
4. **Rotate regularly**: Change secrets every 90 days
5. **Use sufficient length**: Minimum 32 characters, recommended 64 bytes (512 bits)
6. **Keep secrets secret**: Never log, expose in errors, or commit to git

### ❌ DON'T

1. **Never commit secrets to version control**: Add to `.gitignore`
2. **Never use default values**: "secret", "dev-secret-change-in-production", etc.
3. **Never reuse secrets**: Different apps should have different secrets
4. **Never share via insecure channels**: No email, chat, SMS
5. **Never hardcode**: Always use environment variables
6. **Never use simple passwords**: Use cryptographically random values

## Examples

### Docker Deployment

```dockerfile
# Dockerfile - DO NOT include secrets
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Pass secret at runtime
docker run -e ENVIRONMENT=production \
           -e JWT_SECRET="<your-secure-secret>" \
           -e JWT_EXPIRY_HOURS=24 \
           -p 8000:8000 \
           your-app:latest
```

### Kubernetes Deployment

```yaml
# Create secret (run once)
apiVersion: v1
kind: Secret
metadata:
  name: jwt-secret
type: Opaque
stringData:
  JWT_SECRET: "<your-secure-secret>"
```

```yaml
# Reference in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: your-app:latest
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: JWT_SECRET
        - name: JWT_EXPIRY_HOURS
          value: "24"
```

### Docker Compose

```yaml
# docker-compose.yml
services:
  api:
    build: .
    environment:
      ENVIRONMENT: production
      JWT_SECRET: ${JWT_SECRET}  # From .env file or environment
      JWT_EXPIRY_HOURS: 24
    ports:
      - "8000:8000"
```

```bash
# .env file (add to .gitignore!)
JWT_SECRET=<your-secure-secret>
```

### Local Development

```bash
# .env file (add to .gitignore!)
ENVIRONMENT=development
# JWT_SECRET is optional in development - will auto-generate if missing
# Or set your own:
# JWT_SECRET=<generated-dev-secret>
```

## API Integration

### Using the Hardened Configuration

```python
from config import get_jwt_config

# Get validated JWT configuration
jwt_config = get_jwt_config()
# Returns: {
#   "secret": "<validated-secret>",
#   "expiry_hours": 24,
#   "algorithm": "HS256"
# }

# Use in JWT creation
import jwt
from datetime import datetime, timedelta, timezone

payload = {
    "sub": user_id,
    "email": email,
    "iat": datetime.now(timezone.utc),
    "exp": datetime.now(timezone.utc) + timedelta(hours=jwt_config["expiry_hours"]),
}
token = jwt.encode(payload, jwt_config["secret"], algorithm=jwt_config["algorithm"])
```

## Error Messages

### Production Errors

```
❌ JWT_SECRET environment variable must be set in production.
   → Set the JWT_SECRET environment variable with a secure secret
   → Generate one using: python generate_jwt_secret.py

❌ Insecure JWT secret detected in production: Secret is too short
   → Your secret must be at least 32 characters
   → Generate a new one using: python generate_jwt_secret.py

❌ Insecure JWT secret detected in production: Secret is in the list of commonly used weak secrets
   → You're using a common/default secret
   → Generate a secure one using: python generate_jwt_secret.py

❌ Insecure JWT secret detected in production: Secret has low entropy (64 bits, recommended minimum: 128 bits)
   → Your secret is too predictable
   → Use: python generate_jwt_secret.py
```

### Development Warnings

```
⚠️  No JWT_SECRET configured in development environment.
    Generating a temporary secret (tokens will be invalid after restart).
    → Set JWT_SECRET in .env for persistent tokens

⚠️  Weak JWT secret in use: Secret is too short
    This should only be used in development environments.
    → Set ALLOW_WEAK_JWT_SECRET=true to suppress this warning
    → Or generate a strong secret: python generate_jwt_secret.py
```

## Testing

Run the JWT configuration tests:

```bash
# Run all JWT config tests
pytest tests/test_jwt_config.py -v

# Run specific test class
pytest tests/test_jwt_config.py::TestGetJWTSecret -v

# Run with coverage
pytest tests/test_jwt_config.py --cov=config --cov-report=html
```

## Migration Guide

### Migrating from Hardcoded Secrets

**Before (SDT1-63):**
```python
# ❌ Insecure - hardcoded default
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
```

**After (SDT1-63):**
```python
# ✅ Secure - validated configuration
from config import get_jwt_config
jwt_config = get_jwt_config()
JWT_SECRET = jwt_config["secret"]
```

### Steps to Migrate

1. **Generate a new secret for each environment:**
   ```bash
   python generate_jwt_secret.py
   ```

2. **Update environment variables:**
   ```bash
   export JWT_SECRET="<generated-secret>"
   export ENVIRONMENT="production"
   ```

3. **Update your code:**
   ```python
   # Replace direct environment access
   from config import get_jwt_config
   jwt_config = get_jwt_config()
   ```

4. **Test the configuration:**
   ```bash
   python -c "from config import get_jwt_config; print('✓ Config OK')"
   ```

5. **Deploy and verify:**
   - Check application logs for "✓ JWT configuration validated successfully"
   - Verify tokens are being issued correctly

## Troubleshooting

### Issue: Application won't start in production

**Error:** `JWTConfigError: JWT_SECRET environment variable must be set in production`

**Solution:**
```bash
# Generate a secret
python generate_jwt_secret.py

# Set the environment variable
export JWT_SECRET="<generated-secret>"

# Restart the application
```

### Issue: "Insecure JWT secret detected"

**Solution:**
```bash
# Generate a new, secure secret
python generate_jwt_secret.py

# Replace the old secret
export JWT_SECRET="<new-secure-secret>"
```

### Issue: Need to use a weak secret in development

**Solution (not recommended):**
```bash
export ENVIRONMENT=development
export JWT_SECRET="your-weak-secret"
export ALLOW_WEAK_JWT_SECRET=true
```

### Issue: Tokens invalid after restart in development

**Cause:** Auto-generated secret changes on each restart

**Solution:**
```bash
# Generate and save a persistent secret
python generate_jwt_secret.py > .jwt_secret

# Add to .env
echo "JWT_SECRET=$(cat .jwt_secret)" >> .env

# Add .env to .gitignore
echo ".env" >> .gitignore
echo ".jwt_secret" >> .gitignore
```

## Security Checklist

Before deploying to production:

- [ ] JWT_SECRET is set to a cryptographically secure value
- [ ] Secret is at least 32 characters (64 bytes/512 bits recommended)
- [ ] Secret is stored securely (not in code, committed to git, or in logs)
- [ ] ENVIRONMENT is set to "production"
- [ ] Different secrets are used for dev/staging/production
- [ ] Secret rotation schedule is established (every 90 days recommended)
- [ ] Backup/recovery process for secrets is documented
- [ ] Team members know not to share secrets via insecure channels
- [ ] Application starts successfully with valid configuration
- [ ] Tokens are being issued and validated correctly

## References

- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Secrets Management Best Practices](https://owasp.org/www-project-secrets-management/)

## Related Tickets

- SDT1-63: Harden JWT secret key handling (this ticket)
- SDT1-56: Harden CORS FRONTEND_URL configuration (similar pattern)
