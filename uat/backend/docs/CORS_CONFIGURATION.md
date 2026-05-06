# CORS Configuration Guide

## Overview

This document describes the hardened CORS (Cross-Origin Resource Sharing) configuration implemented in [SDT1-56]. The configuration provides secure defaults while allowing flexibility for different deployment environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Security Features](#security-features)
- [Common Scenarios](#common-scenarios)
- [Troubleshooting](#troubleshooting)
- [Migration Guide](#migration-guide)

## Quick Start

### Production Deployment

Set the `FRONTEND_URL` environment variable to your frontend domain:

```bash
export FRONTEND_URL="https://app.example.com"
```

For multiple frontend domains:

```bash
export FRONTEND_URL="https://app.example.com,https://admin.example.com"
```

### Development Environment

For local development, the system defaults to `http://localhost:3000` if `ENVIRONMENT=development` and no `FRONTEND_URL` is set:

```bash
export ENVIRONMENT="development"
# Automatically uses http://localhost:3000
```

Or specify your development URL:

```bash
export ENVIRONMENT="development"
export FRONTEND_URL="http://localhost:3000"
```

## Environment Variables

### Core Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FRONTEND_URL` | Yes (production) | `http://localhost:3000` (dev) | Single URL or comma-separated list of allowed origins |
| `ENVIRONMENT` | No | `production` | Set to `development` or `production` |
| `ALLOW_CORS_WILDCARD` | No | `false` | Set to `true` to explicitly allow wildcard `*` origin |

### FRONTEND_URL Format

The `FRONTEND_URL` can be:

1. **Single origin**: `https://app.example.com`
2. **Multiple origins** (comma-separated): `https://app.example.com,https://admin.example.com`
3. **Wildcard** (requires `ALLOW_CORS_WILDCARD=true`): `*`

#### Valid Origin Examples

```bash
# Basic HTTPS
FRONTEND_URL="https://example.com"

# With subdomain
FRONTEND_URL="https://app.example.com"

# With port
FRONTEND_URL="https://example.com:8443"

# HTTP (development only, not recommended for production)
FRONTEND_URL="http://localhost:3000"

# Multiple origins
FRONTEND_URL="https://app.example.com,https://admin.example.com,https://staging.example.com"

# IPv4 (useful for development)
FRONTEND_URL="http://127.0.0.1:3000"

# IPv6 (useful for development)
FRONTEND_URL="http://[::1]:3000"
```

#### Invalid Origin Examples

```bash
# ❌ Missing protocol
FRONTEND_URL="example.com"

# ❌ Invalid protocol
FRONTEND_URL="ftp://example.com"

# ❌ Empty/whitespace only
FRONTEND_URL="   "

# ❌ Wildcard mixed with specific origins
FRONTEND_URL="*,https://example.com"
```

## Security Features

### 1. Origin Validation

All origins are validated to ensure:
- Proper URL format with scheme (http/https)
- Valid domain/netloc component
- No malformed or suspicious URLs

### 2. Production Hardening

In production (`ENVIRONMENT=production`):
- `FRONTEND_URL` must be explicitly set
- Wildcard `*` origin is blocked by default
- Must use `ALLOW_CORS_WILDCARD=true` to explicitly allow wildcard (not recommended)

### 3. Startup Validation

The application validates CORS configuration at startup and will fail to start if:
- `FRONTEND_URL` is missing in production
- Origins are malformed
- Wildcard is used without explicit permission
- Origins list is empty

This "fail fast" approach prevents misconfigurations from reaching production.

### 4. Audit Logging

CORS configuration is logged at startup:
```
INFO: CORS configured with 2 origin(s): https://app.example.com, https://admin.example.com
```

Warnings are logged for potentially insecure configurations:
```
WARNING: ⚠️  CORS wildcard '*' is enabled. This allows requests from ANY origin.
```

## Common Scenarios

### Scenario 1: Single Production Frontend

**Setup:**
```bash
export ENVIRONMENT="production"
export FRONTEND_URL="https://app.example.com"
```

**Result:** Only requests from `https://app.example.com` are allowed.

---

### Scenario 2: Multiple Production Frontends

**Setup:**
```bash
export ENVIRONMENT="production"
export FRONTEND_URL="https://app.example.com,https://admin.example.com,https://mobile.example.com"
```

**Result:** Requests from all three domains are allowed.

---

### Scenario 3: Local Development

**Setup:**
```bash
export ENVIRONMENT="development"
# FRONTEND_URL not set
```

**Result:** Automatically allows `http://localhost:3000`.

---

### Scenario 4: Local Development with Custom Port

**Setup:**
```bash
export ENVIRONMENT="development"
export FRONTEND_URL="http://localhost:5173"
```

**Result:** Allows requests from Vite dev server on port 5173.

---

### Scenario 5: Staging Environment

**Setup:**
```bash
export ENVIRONMENT="production"
export FRONTEND_URL="https://staging.example.com,https://staging-admin.example.com"
```

**Result:** Only staging domains are allowed (production security rules apply).

---

### Scenario 6: Development with Multiple Frontends

**Setup:**
```bash
export ENVIRONMENT="development"
export FRONTEND_URL="http://localhost:3000,http://localhost:3001,http://localhost:5173"
```

**Result:** Allows requests from multiple local development servers.

---

### Scenario 7: Public API (Wildcard - Not Recommended)

**Setup:**
```bash
export ENVIRONMENT="development"  # or production if you really need it
export FRONTEND_URL="*"
export ALLOW_CORS_WILDCARD="true"
```

**Result:** Allows requests from ANY origin. ⚠️ **Use with extreme caution!**

**When to use wildcard:**
- Public APIs that need to be accessible from any domain
- Development/testing environments only
- Never for APIs handling authentication or sensitive data

---

### Scenario 8: Behind a Reverse Proxy

If your backend is behind a reverse proxy (nginx, Cloudflare, etc.), set origins to the domains users actually see:

**Setup:**
```bash
# Users access: https://app.example.com
# Backend runs: http://localhost:8000
export FRONTEND_URL="https://app.example.com"
```

The proxy handles HTTPS termination, but CORS checks the origin from the user's browser.

---

## Troubleshooting

### Error: "FRONTEND_URL must be configured"

**Cause:** `FRONTEND_URL` is not set in production environment.

**Solution:**
```bash
export FRONTEND_URL="https://your-frontend-domain.com"
```

---

### Error: "Wildcard '*' origin detected in production environment"

**Cause:** Using wildcard without explicit permission.

**Solution (development only):**
```bash
export ALLOW_CORS_WILDCARD="true"
export FRONTEND_URL="*"
```

**Better solution:** Specify actual origins instead of wildcard.

---

### Error: "Invalid CORS origin format"

**Cause:** Origin doesn't have proper URL format.

**Solution:** Ensure each origin includes protocol:
```bash
# ❌ Wrong
export FRONTEND_URL="example.com"

# ✅ Correct
export FRONTEND_URL="https://example.com"
```

---

### Error: "Cannot mix wildcard '*' with specific origins"

**Cause:** Trying to use both `*` and specific domains.

**Solution:** Choose one approach:
```bash
# Option 1: Wildcard only
export FRONTEND_URL="*"
export ALLOW_CORS_WILDCARD="true"

# Option 2: Specific origins
export FRONTEND_URL="https://app1.com,https://app2.com"
```

---

### Browser CORS Error: "No 'Access-Control-Allow-Origin' header"

**Possible causes:**

1. **Frontend URL not in allowed list**
   ```bash
   # Add your frontend domain
   export FRONTEND_URL="https://yourapp.com"
   ```

2. **Missing protocol in FRONTEND_URL**
   ```bash
   # ❌ Wrong
   export FRONTEND_URL="localhost:3000"
   
   # ✅ Correct
   export FRONTEND_URL="http://localhost:3000"
   ```

3. **Port mismatch**
   ```bash
   # If frontend runs on port 3001, not 3000
   export FRONTEND_URL="http://localhost:3001"
   ```

4. **HTTPS vs HTTP mismatch**
   ```bash
   # Frontend uses HTTPS
   export FRONTEND_URL="https://localhost:3000"
   ```

---

### Application Fails to Start

**Cause:** Invalid CORS configuration.

**Check logs for:**
```
ERROR: ❌ CORS configuration error: [specific error message]
```

**Solution:** Fix the configuration error mentioned in logs and restart.

---

## Migration Guide

### Migrating from Previous CORS Setup

If you previously had CORS configured differently, follow these steps:

#### Step 1: Identify Current Origins

Check what origins your frontend currently uses. Look in:
- Browser developer tools → Network tab → Request headers → `Origin`
- Your frontend deployment configuration
- DNS records for frontend domains

#### Step 2: Set FRONTEND_URL

Create or update your environment configuration:

```bash
# Single frontend
export FRONTEND_URL="https://your-frontend.com"

# Multiple frontends
export FRONTEND_URL="https://app.example.com,https://admin.example.com"
```

#### Step 3: Set Environment Type

```bash
# Production
export ENVIRONMENT="production"

# Development
export ENVIRONMENT="development"
```

#### Step 4: Test

1. Start the backend with new configuration
2. Check startup logs for CORS configuration messages
3. Test frontend requests to verify CORS headers are correct

#### Step 5: Deploy

Deploy with new environment variables. The application will validate configuration at startup and fail if misconfigured (preventing broken deployments).

### Deployment Checklist

- [ ] Set `FRONTEND_URL` environment variable
- [ ] Set `ENVIRONMENT` environment variable (production/development)
- [ ] Remove any old CORS-related environment variables
- [ ] Test locally before deploying
- [ ] Verify startup logs show correct CORS configuration
- [ ] Test CORS from frontend after deployment
- [ ] Monitor logs for any CORS-related errors

### Railway/Render/Heroku Deployment

```bash
# Railway
railway variables set FRONTEND_URL="https://yourapp.com"
railway variables set ENVIRONMENT="production"

# Render
# Add via dashboard: Settings → Environment → Add Environment Variable

# Heroku
heroku config:set FRONTEND_URL="https://yourapp.com"
heroku config:set ENVIRONMENT="production"
```

---

## Advanced Configuration

### CORS Middleware Configuration

The complete CORS middleware configuration includes:

```python
{
    "allow_origins": [<from FRONTEND_URL>],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": ["*"],
    "expose_headers": ["*"],
    "max_age": 600,  # Cache preflight requests for 10 minutes
}
```

### Credentials Support

`allow_credentials=True` means:
- Cookies are sent with cross-origin requests
- Authorization headers are included
- Frontend must use `credentials: 'include'` in fetch requests

**Example frontend code:**
```javascript
fetch('https://api.example.com/endpoint', {
  credentials: 'include',  // Required for cookies/auth
  headers: {
    'Content-Type': 'application/json',
  },
})
```

### Preflight Caching

`max_age=600` caches preflight (OPTIONS) requests for 10 minutes, reducing overhead for complex requests.

---

## Security Best Practices

### ✅ DO:

- **Always specify exact origins in production**
  ```bash
  export FRONTEND_URL="https://app.example.com"
  ```

- **Use HTTPS in production**
  ```bash
  export FRONTEND_URL="https://app.example.com"  # Not http://
  ```

- **Test CORS configuration before deploying**
  - Verify startup logs
  - Test from actual frontend domain

- **Use different origins for different environments**
  ```bash
  # Production
  FRONTEND_URL="https://app.example.com"
  
  # Staging
  FRONTEND_URL="https://staging.app.example.com"
  
  # Development
  FRONTEND_URL="http://localhost:3000"
  ```

- **Regularly review allowed origins**
  - Remove old/unused domains
  - Audit access logs for unexpected origins

### ❌ DON'T:

- **Never use wildcard in production with sensitive data**
  ```bash
  # ❌ Dangerous for auth/payment APIs
  FRONTEND_URL="*"
  ```

- **Don't include paths in origins**
  ```bash
  # ❌ Wrong
  FRONTEND_URL="https://example.com/app"
  
  # ✅ Correct
  FRONTEND_URL="https://example.com"
  ```

- **Don't use IP addresses in production** (unless necessary)
  ```bash
  # ❌ Avoid
  FRONTEND_URL="http://123.456.789.0"
  
  # ✅ Better
  FRONTEND_URL="https://app.example.com"
  ```

- **Don't bypass CORS validation**
  - Resist temptation to disable security checks
  - Fix the root cause instead

---

## Testing

### Manual Testing

1. **Check startup logs:**
   ```
   INFO: ✓ CORS configuration validated successfully
   INFO: CORS configured with 1 origin(s): https://app.example.com
   ```

2. **Test from browser console:**
   ```javascript
   fetch('https://api.example.com/health', {
     credentials: 'include',
   })
   .then(response => response.json())
   .then(data => console.log('Success:', data))
   .catch(error => console.error('CORS error:', error));
   ```

3. **Check response headers:**
   ```
   Access-Control-Allow-Origin: https://app.example.com
   Access-Control-Allow-Credentials: true
   ```

### Automated Testing

Run the test suite:
```bash
cd uat/backend
pytest tests/test_config.py -v
```

Tests cover:
- ✅ Valid origin formats
- ✅ Invalid origin rejection
- ✅ Wildcard handling
- ✅ Multiple origins
- ✅ Production security rules
- ✅ Development defaults
- ✅ Edge cases

---

## Related Documentation

- [JWT Configuration Guide](./JWT_CONFIGURATION.md) - Token security (SDT1-63)
- [Environment Variables Reference](./ENVIRONMENT_VARIABLES.md)
- [Deployment Guide](./DEPLOYMENT.md)

---

## Support

For issues or questions:
1. Check logs for specific error messages
2. Review this documentation
3. Contact DevOps team
4. Open a ticket in Jira

---

**Document Version:** 1.0  
**Last Updated:** 2024 (SDT1-56)  
**Maintained By:** DevOps & Security Team
