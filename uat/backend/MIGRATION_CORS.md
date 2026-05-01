# CORS Configuration Migration Guide (SDT1-56)

## Quick Start

If your application suddenly fails to start with a CORS error, follow these steps:

### 1. For Development (Local Machine)

Update your `.env` file:

```bash
# Option A: Use localhost (recommended)
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000

# Option B: Use wildcard (less secure but convenient)
ENVIRONMENT=development
FRONTEND_URL=*
ALLOW_CORS_WILDCARD=true
```

### 2. For Production/Staging

Update your `.env` or environment variables:

```bash
ENVIRONMENT=production
FRONTEND_URL=https://your-actual-frontend-domain.com
```

For multiple frontends:

```bash
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com,https://admin.example.com
```

## What Changed?

### Before (Old Behavior)

- `FRONTEND_URL` defaulted to `*` (wildcard) if not set
- No validation of origin URLs
- Security risk: any website could make requests

### After (New Behavior - SDT1-56)

- `FRONTEND_URL` is required (or defaults to localhost in dev)
- All origins are validated for correct format
- Wildcard requires explicit `ALLOW_CORS_WILDCARD=true` flag
- Clear error messages for misconfigurations
- Application won't start with invalid CORS config

## Common Scenarios

### Scenario 1: "My app won't start" (Missing FRONTEND_URL)

**Error Message**:
```
CORSConfigError: FRONTEND_URL must be configured
```

**Fix**:
```bash
# Add to .env
FRONTEND_URL=http://localhost:3000  # for development
# or
FRONTEND_URL=https://your-domain.com  # for production
```

### Scenario 2: "Wildcard not allowed" Error

**Error Message**:
```
CORSConfigError: Wildcard '*' origin detected in production environment
```

**Fix Option 1** (Recommended - Use specific origins):
```bash
FRONTEND_URL=https://your-frontend-domain.com
```

**Fix Option 2** (Not recommended - Allow wildcard):
```bash
FRONTEND_URL=*
ALLOW_CORS_WILDCARD=true
```

### Scenario 3: "Invalid origin format" Error

**Error Message**:
```
CORSConfigError: Invalid CORS origin format: example.com
```

**Problem**: Missing `http://` or `https://`

**Fix**:
```bash
# Wrong
FRONTEND_URL=example.com

# Correct
FRONTEND_URL=https://example.com
```

### Scenario 4: Multiple Frontends

**Before**:
```bash
FRONTEND_URL=https://app.example.com
```

**After** (add more frontends):
```bash
FRONTEND_URL=https://app.example.com,https://admin.example.com,https://mobile.example.com
```

### Scenario 5: Development with Multiple Ports

```bash
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000
```

## Environment-Specific Configuration

### Local Development (.env)

```bash
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

### Docker Compose (docker-compose.yml)

```yaml
services:
  backend:
    environment:
      - ENVIRONMENT=development
      - FRONTEND_URL=http://localhost:3000
```

### Kubernetes (ConfigMap/Secret)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
data:
  ENVIRONMENT: "production"
  FRONTEND_URL: "https://app.example.com,https://admin.example.com"
```

### Heroku

```bash
heroku config:set ENVIRONMENT=production
heroku config:set FRONTEND_URL=https://your-frontend.herokuapp.com
```

### AWS (Environment Variables)

In AWS Console or CLI:
```bash
ENVIRONMENT=production
FRONTEND_URL=https://your-cloudfront-domain.cloudfront.net
```

## Verification

After updating configuration:

### 1. Check Application Starts

```bash
cd uat/backend
uvicorn main:app --reload
```

Look for:
```
✓ CORS configuration validated successfully
CORS middleware configured
```

### 2. Test CORS Request

```bash
curl -X OPTIONS http://localhost:8000/health \
  -H "Origin: https://your-frontend.com" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

Should return:
```
< HTTP/1.1 200 OK
< access-control-allow-origin: https://your-frontend.com
< access-control-allow-credentials: true
```

### 3. Run Tests

```bash
pytest tests/test_config.py -v
```

All tests should pass.

## Rollback (Emergency)

If you need to quickly rollback to the old behavior (not recommended for production):

1. Set wildcard with explicit flag:
   ```bash
   FRONTEND_URL=*
   ALLOW_CORS_WILDCARD=true
   ```

2. This will work but shows security warnings in logs

3. Plan to fix properly with specific origins

## Best Practices Going Forward

1. **Always set FRONTEND_URL**: Don't rely on defaults
2. **Use specific origins**: List exact domains instead of wildcard
3. **Use HTTPS in production**: Always use `https://` for production origins
4. **Document origins**: Keep a list of all allowed origins
5. **Test CORS changes**: Run tests after modifying CORS configuration
6. **Review regularly**: Audit CORS origins periodically

## Getting Help

1. **Read full documentation**: See `CORS_CONFIGURATION.md`
2. **Check logs**: Application logs show detailed CORS errors
3. **Run tests**: `pytest tests/test_config.py -v`
4. **Check examples**: See `.env.example` for configuration examples

## Summary of Changes

| Aspect | Before | After (SDT1-56) |
|--------|--------|-----------------|
| Default | `*` wildcard | No default (required) |
| Validation | None | Full URL validation |
| Wildcard | Always allowed | Requires explicit flag |
| Multiple origins | Not supported | Comma-separated list |
| Error handling | Silent failure | Clear error messages |
| Startup check | No validation | Validates at startup |
| Security | Vulnerable | Hardened |

## Timeline

- **Implemented**: SDT1-56
- **Migration deadline**: Update configurations before next deployment
- **Support period**: Ongoing

---

**Need Help?** Check the logs for specific error messages and refer to `CORS_CONFIGURATION.md` for detailed documentation.
