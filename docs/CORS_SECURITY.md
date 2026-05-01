# CORS Security Configuration

This document describes the hardened CORS (Cross-Origin Resource Sharing) configuration implemented in the UAT backend to protect against cross-origin attacks.

## Overview

CORS is a security feature that restricts web pages from making requests to a different domain than the one serving the web page. Proper CORS configuration is critical to prevent unauthorized access to API endpoints.

## Configuration

### Environment Variables

#### `FRONTEND_URL` (Required in Production/Staging)

Comma-separated list of allowed frontend origin URLs.

**Examples:**
```bash
# Single origin
FRONTEND_URL=https://app.example.com

# Multiple origins
FRONTEND_URL=https://app.example.com,https://admin.example.com,https://staging.example.com

# Development (optional - will default to localhost)
FRONTEND_URL=http://localhost:3000,http://localhost:5173
```

**Important:** Leave empty in local development to automatically allow common localhost ports.

#### `ENVIRONMENT` (Optional, default: development)

Controls validation strictness and default behaviors.

Valid values:
- `development` / `dev` / `local` - Relaxed validation, localhost defaults
- `staging` - Strict validation, no defaults
- `production` / `prod` - Strictest validation, HTTPS enforcement

## Security Features

### 1. Explicit Origin Validation

- ❌ **Wildcard (`*`) Blocked in Production**: The wildcard origin allows any website to access your API, which is a security risk.
- ✅ **Explicit URLs Required**: All production deployments must specify exact frontend URLs.

### 2. URL Format Validation

All origin URLs are validated against strict rules:

#### ✅ Allowed Formats
```
https://app.example.com
https://app.example.com:8443
http://localhost:3000
http://127.0.0.1:5173
```

#### ❌ Rejected Formats
```
app.example.com                    # Missing scheme
http://app.example.com             # HTTP in production (except localhost)
https://app.example.com/path       # Contains path
https://app.example.com?query=1    # Contains query string
https://app.example.com#fragment   # Contains fragment
ftp://app.example.com             # Invalid scheme
```

### 3. Environment-Specific Enforcement

#### Production Environment
- `FRONTEND_URL` **must** be set (no defaults)
- Wildcard `*` is **rejected**
- HTTP URLs are **rejected** (except localhost for testing)
- All URLs must use HTTPS

#### Staging Environment
- `FRONTEND_URL` **must** be set (no defaults)
- HTTP URLs are **allowed** (for staging servers)
- Wildcard `*` is **allowed** (if needed for staging)

#### Development Environment
- `FRONTEND_URL` is **optional**
- If not set, defaults to common localhost ports:
  - `http://localhost:3000`
  - `http://localhost:5173`
  - `http://127.0.0.1:3000`
  - `http://127.0.0.1:5173`
- Wildcard `*` is **allowed**

### 4. Startup Validation

The application validates CORS configuration on startup and will **fail to start** if:
- `FRONTEND_URL` is missing in production/staging
- Any URL in the list is malformed
- Production environment uses insecure settings

This ensures misconfiguration is caught early rather than in production.

## Common Use Cases

### Local Development

**Option 1: Use Defaults (Recommended)**
```bash
# Don't set FRONTEND_URL or set it to empty
ENVIRONMENT=development
```

Automatically allows:
- http://localhost:3000
- http://localhost:5173
- http://127.0.0.1:3000
- http://127.0.0.1:5173

**Option 2: Custom Development URLs**
```bash
ENVIRONMENT=development
FRONTEND_URL=http://localhost:8080,http://192.168.1.100:3000
```

### Staging Environment

```bash
ENVIRONMENT=staging
FRONTEND_URL=https://staging.example.com,http://staging-internal.example.com
```

### Production Environment

```bash
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com
```

For multiple production domains:
```bash
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com,https://admin.example.com,https://mobile.example.com
```

## Error Messages

### "FRONTEND_URL must be set in production environment"
**Cause:** `FRONTEND_URL` is empty or not set in production.
**Fix:** Set `FRONTEND_URL` to your frontend domain(s):
```bash
FRONTEND_URL=https://app.example.com
```

### "Wildcard '*' origin is not allowed in production"
**Cause:** `FRONTEND_URL=*` in production environment.
**Fix:** Specify explicit frontend URLs instead of wildcard.

### "URL must include scheme (http:// or https://)"
**Cause:** URL is missing the protocol prefix.
**Fix:** Add `https://` or `http://` prefix:
```bash
# Wrong
FRONTEND_URL=app.example.com

# Correct
FRONTEND_URL=https://app.example.com
```

### "CORS origin should not include path"
**Cause:** URL contains a path component.
**Fix:** Remove the path, use only the origin:
```bash
# Wrong
FRONTEND_URL=https://app.example.com/dashboard

# Correct
FRONTEND_URL=https://app.example.com
```

### "uses http scheme in production. Use https for security"
**Cause:** Using HTTP in production (except localhost).
**Fix:** Use HTTPS for production domains:
```bash
# Wrong
FRONTEND_URL=http://app.example.com

# Correct
FRONTEND_URL=https://app.example.com
```

## Testing

Run the CORS configuration tests:

```bash
cd uat/backend
pytest tests/test_cors_config.py -v
```

Expected output:
```
test_cors_config.py::TestCORSConfiguration::test_validate_origin_url_valid_https PASSED
test_cors_config.py::TestCORSConfiguration::test_validate_origin_url_valid_http_localhost PASSED
...
```

## Migration Guide

### Upgrading from Previous Configuration

**Before (Insecure):**
```python
# main.py
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    ...
)
```

**After (Secure):**
```python
# main.py
from config import settings

allowed_origins = settings.get_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    ...
)
```

**Required Changes:**

1. **Set `FRONTEND_URL` in production:**
   ```bash
   FRONTEND_URL=https://your-frontend-domain.com
   ```

2. **Set `ENVIRONMENT` variable:**
   ```bash
   ENVIRONMENT=production
   ```

3. **Update deployment configs** (Docker, k8s, etc.) to include these variables.

4. **Test locally** before deploying:
   ```bash
   ENVIRONMENT=production FRONTEND_URL=https://test.com python -m uvicorn main:app
   ```
   Should start successfully with log: "✓ CORS configured with allowed origins: ['https://test.com']"

## Security Best Practices

1. **Never use `*` wildcard in production** - Always specify explicit origins
2. **Use HTTPS in production** - HTTP is vulnerable to man-in-the-middle attacks
3. **Minimize allowed origins** - Only include domains that legitimately need API access
4. **Keep domains up to date** - Remove origins when services are decommissioned
5. **Use environment variables** - Never hardcode origins in source code
6. **Validate on deployment** - Ensure application starts successfully with production config
7. **Monitor CORS errors** - Log and alert on rejected CORS requests
8. **Regular security audits** - Review allowed origins periodically

## Troubleshooting

### CORS Errors in Browser Console

**Error:** "Access to fetch at 'https://api.example.com' from origin 'https://app.example.com' has been blocked by CORS policy"

**Diagnosis:**
1. Check that `FRONTEND_URL` includes `https://app.example.com`
2. Verify the frontend is using the exact URL (check protocol, subdomain, port)
3. Check application startup logs for "✓ CORS configured with allowed origins"

**Debug:**
```bash
# Check current configuration
curl https://api.example.com/health -H "Origin: https://app.example.com" -v
```

Look for `Access-Control-Allow-Origin` header in response.

### Application Won't Start

**Error:** "ERROR: Configuration validation failed: CORS configuration error: FRONTEND_URL must be set in production"

**Fix:** Set the required environment variable:
```bash
export FRONTEND_URL=https://app.example.com
```

Or in your deployment configuration (docker-compose.yml, k8s manifest, etc.).

## Additional Resources

- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP: CORS Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/CORS_Cheat_Sheet.html)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)

## Support

For questions or issues with CORS configuration, contact the security team or file an issue in the repository.
