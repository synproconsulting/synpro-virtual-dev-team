# Backend Documentation

Welcome to the SynPro Virtual Dev Team backend documentation.

## Quick Links

### Security & Configuration
- **[CORS Configuration Guide](./CORS_CONFIGURATION.md)** - Complete CORS setup and hardening (SDT1-56)
- **[CORS Quick Reference](./CORS_QUICK_REFERENCE.md)** - Quick commands and troubleshooting
- **[Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)** - Pre-deployment security validation

### Getting Started
- **[.env.example](../.env.example)** - Environment variable template
- **[security_audit.py](../security_audit.py)** - Security configuration audit script

## Documentation Overview

### CORS Configuration (SDT1-56)

The backend implements hardened CORS configuration with the following features:

- ✅ Origin validation with security checks
- ✅ Production hardening (no wildcard by default)
- ✅ Startup validation (fail-fast approach)
- ✅ Comprehensive error messages
- ✅ Audit logging

**Key files:**
- `uat/backend/config.py` - CORS configuration implementation
- `uat/backend/main.py` - CORS middleware integration
- `uat/backend/tests/test_config.py` - Configuration tests

**Documentation:**
- [CORS_CONFIGURATION.md](./CORS_CONFIGURATION.md) - Full guide with examples
- [CORS_QUICK_REFERENCE.md](./CORS_QUICK_REFERENCE.md) - Quick reference card

### JWT Configuration (SDT1-63)

Secure JWT token handling with secret validation:

- ✅ Cryptographically secure secret generation
- ✅ Weak secret detection
- ✅ Entropy validation
- ✅ Production hardening

**Key files:**
- `uat/backend/config.py` - JWT configuration implementation
- `uat/backend/auth.py` - JWT token generation/validation

**Documentation:**
- JWT configuration is covered in [CORS_CONFIGURATION.md](./CORS_CONFIGURATION.md)

### Deployment

Step-by-step deployment guide with security checklist:

- ✅ Environment variable setup
- ✅ Security validation
- ✅ Platform-specific instructions (Railway, Render, Heroku, Docker)
- ✅ Troubleshooting guide

**Documentation:**
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)

## Quick Start

### 1. Set Up Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
# Minimum required
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
JWT_SECRET=<generate-secure-secret>
DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

### 2. Generate Secure Secrets

```bash
# Generate JWT secret
python -c "from config import generate_jwt_secret; print(generate_jwt_secret())"
```

### 3. Validate Configuration

Run the security audit:
```bash
python security_audit.py
```

Run the tests:
```bash
pytest tests/test_config.py -v
```

### 4. Start the Application

```bash
uvicorn main:app --reload
```

Check startup logs for validation messages:
```
✓ CORS configuration validated successfully
✓ JWT configuration validated successfully
```

## Common Tasks

### Update CORS Origins

Single origin:
```bash
export FRONTEND_URL="https://app.example.com"
```

Multiple origins:
```bash
export FRONTEND_URL="https://app.example.com,https://admin.example.com"
```

### Rotate JWT Secret

1. Generate new secret:
   ```bash
   python -c "from config import generate_jwt_secret; print(generate_jwt_secret())"
   ```

2. Update environment variable:
   ```bash
   export JWT_SECRET="<new-secret>"
   ```

3. Restart application

⚠️ **Note:** Rotating JWT_SECRET will invalidate all existing tokens.

### Test CORS Configuration

From browser console:
```javascript
fetch('http://localhost:8000/health', {
  credentials: 'include'
})
.then(r => r.json())
.then(console.log)
```

### Run Security Audit

Check configuration security:
```bash
python security_audit.py
```

## Troubleshooting

### Application Won't Start

**Check logs for:**
- `❌ CORS configuration error: <message>`
- `❌ JWT configuration error: <message>`

**Common fixes:**
- Set required environment variables
- Fix invalid origin URLs
- Generate secure JWT secret

See [CORS_CONFIGURATION.md](./CORS_CONFIGURATION.md) for detailed troubleshooting.

### CORS Errors in Browser

```
Access to fetch at 'https://api.example.com' from origin 'https://app.example.com' 
has been blocked by CORS policy
```

**Fixes:**
1. Add frontend domain to `FRONTEND_URL`
2. Ensure protocol matches (http vs https)
3. Check for port mismatches
4. Restart backend after config changes

See [CORS_QUICK_REFERENCE.md](./CORS_QUICK_REFERENCE.md) for quick fixes.

## Testing

### Run All Tests

```bash
# All backend tests
pytest tests/ -v

# Only configuration tests
pytest tests/test_config.py -v

# With coverage
pytest tests/test_config.py --cov=config --cov-report=html
```

### Manual Testing

Test CORS headers:
```bash
curl -H "Origin: https://app.example.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8000/health \
     -v
```

Expected response headers:
```
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
```

## Security Best Practices

### ✅ DO:

- **Use HTTPS in production**
  ```bash
  FRONTEND_URL="https://app.example.com"  # Not http://
  ```

- **Specify exact origins**
  ```bash
  FRONTEND_URL="https://app1.com,https://app2.com"
  ```

- **Generate strong JWT secrets**
  ```bash
  python -c "from config import generate_jwt_secret; print(generate_jwt_secret())"
  ```

- **Store secrets securely**
  - Use environment variables
  - Use secrets managers (AWS Secrets Manager, Vault)
  - Never commit secrets to git

- **Run security audits before deployment**
  ```bash
  python security_audit.py
  ```

- **Use different secrets per environment**
  - Development secrets != Production secrets
  - Rotate secrets regularly

### ❌ DON'T:

- **Never use wildcard in production** (unless absolutely necessary)
  ```bash
  FRONTEND_URL="*"  # ❌ Dangerous
  ```

- **Never hardcode secrets**
  ```python
  JWT_SECRET = "my-secret"  # ❌ Don't do this
  ```

- **Never commit .env files**
  ```bash
  # Add to .gitignore
  .env
  .env.local
  ```

- **Never use weak secrets**
  ```bash
  JWT_SECRET="secret"  # ❌ Too weak
  JWT_SECRET="dev-secret"  # ❌ Too weak
  ```

## CI/CD Integration

### GitHub Actions

Security checks run automatically on PRs:

```yaml
# .github/workflows/security-audit.yml
- Run configuration tests
- Run security audit
- Check for hardcoded secrets
- Verify documentation
```

View workflow: `.github/workflows/security-audit.yml`

### Pre-commit Hooks

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
cd uat/backend
python security_audit.py
if [ $? -ne 0 ]; then
  echo "❌ Security audit failed. Fix issues before committing."
  exit 1
fi
```

## Related Resources

### Internal Documentation
- [CORS Configuration Guide](./CORS_CONFIGURATION.md) - Full CORS documentation
- [CORS Quick Reference](./CORS_QUICK_REFERENCE.md) - Quick commands
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md) - Deployment guide

### External Resources
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP CORS Best Practices](https://owasp.org/www-community/attacks/CORS_OriginHeaderScrutiny)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

## Support

### Documentation Issues

If documentation is unclear or outdated:
1. Check the latest version in the repository
2. Open a Jira ticket with suggestions
3. Contact the DevOps team

### Configuration Issues

For configuration problems:
1. Run `python security_audit.py` for diagnostics
2. Check [CORS_CONFIGURATION.md](./CORS_CONFIGURATION.md) troubleshooting section
3. Review application startup logs
4. Open a Jira ticket if issue persists

### Security Concerns

For security issues:
1. **DO NOT** open public issues for security vulnerabilities
2. Contact security team directly: security@example.com
3. Follow responsible disclosure process

## Contributing

When updating documentation:

1. **Keep it current** - Update docs when changing implementation
2. **Add examples** - Real-world examples help users
3. **Test instructions** - Verify commands work as documented
4. **Update version** - Increment version number at bottom of docs
5. **Cross-reference** - Link to related documentation

## Version History

| Version | Date | Changes | Ticket |
|---------|------|---------|--------|
| 1.0 | 2024 | Initial security documentation | SDT1-56 |

---

**Last Updated:** 2024  
**Maintained By:** DevOps & Security Team  
**Related Tickets:** SDT1-56 (CORS), SDT1-63 (JWT)
