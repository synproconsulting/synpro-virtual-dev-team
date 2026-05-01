# CORS Configuration Guide (SDT1-56)

This document describes the hardened CORS configuration implemented in the UAT backend.

## Overview

The CORS (Cross-Origin Resource Sharing) configuration has been hardened to prevent security vulnerabilities and ensure proper validation of allowed origins. The new configuration system validates origins at startup and provides clear error messages for misconfigurations.

## Features

✅ **Origin Validation**: All configured origins are validated for proper URL format  
✅ **Multiple Origins**: Support for comma-separated list of allowed origins  
✅ **Wildcard Protection**: Wildcard (`*`) requires explicit opt-in and warns users  
✅ **Environment Awareness**: Different defaults and validation rules for dev vs. prod  
✅ **Startup Validation**: Configuration errors are caught at application startup  
✅ **Clear Error Messages**: Descriptive errors help identify and fix configuration issues  
✅ **Comprehensive Testing**: Full test coverage for all validation scenarios  

## Environment Variables

### `FRONTEND_URL` (Required)

The primary configuration for CORS origins. Can be:

1. **Single origin**: One frontend URL
   ```bash
   FRONTEND_URL=https://app.example.com
   ```

2. **Multiple origins**: Comma-separated list
   ```bash
   FRONTEND_URL=https://app.example.com,https://admin.example.com,https://staging.example.com
   ```

3. **Wildcard** (not recommended): Allows all origins
   ```bash
   FRONTEND_URL=*
   ALLOW_CORS_WILDCARD=true  # Required to enable wildcard
   ```

### `ALLOW_CORS_WILDCARD` (Optional, default: `false`)

Explicitly allow wildcard CORS configuration. Must be set to `true` to use `*` as origin.

```bash
ALLOW_CORS_WILDCARD=true
```

**⚠️ Security Warning**: Wildcard CORS allows requests from ANY origin, including potentially malicious sites. Only use this in development environments or when you fully understand the security implications.

### `ENVIRONMENT` (Optional, default: `production`)

Specifies the runtime environment. Affects validation behavior:

- **production**: Strict validation, no wildcard without explicit opt-in
- **development**: Defaults to localhost if `FRONTEND_URL` not set

```bash
ENVIRONMENT=development  # or production
```

## Configuration Examples

### Production (Single Frontend)

```bash
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com
```

### Production (Multiple Frontends)

```bash
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com,https://admin.example.com
```

### Production (with Mobile App)

```bash
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com,https://mobile.example.com,capacitor://localhost
```

### Development (Localhost)

```bash
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

### Development (Multiple Local Ports)

```bash
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000
```

### Development (Wildcard - Not Recommended)

```bash
ENVIRONMENT=development
FRONTEND_URL=*
ALLOW_CORS_WILDCARD=true
```

## Valid Origin Formats

Origins must be valid HTTP(S) URLs:

✅ `https://example.com`  
✅ `https://example.com:8080`  
✅ `https://subdomain.example.com`  
✅ `http://localhost:3000`  
✅ `http://127.0.0.1:3000`  
✅ `http://[::1]:3000` (IPv6)  
✅ `capacitor://localhost` (Capacitor mobile apps)  

❌ `example.com` (missing scheme)  
❌ `ftp://example.com` (invalid scheme)  
❌ `http://` (missing domain)  
❌ Just `*` without `ALLOW_CORS_WILDCARD=true`  

## Error Messages

### Missing Configuration

```
CORSConfigError: FRONTEND_URL must be configured. Set FRONTEND_URL to a comma-separated list of allowed origins.
```

**Solution**: Set the `FRONTEND_URL` environment variable.

### Wildcard Not Allowed

```
CORSConfigError: Wildcard '*' origin detected in production environment. Set ALLOW_CORS_WILDCARD=true to explicitly allow this (not recommended).
```

**Solution**: Either:
1. Set specific origins instead of wildcard (recommended)
2. Set `ALLOW_CORS_WILDCARD=true` (only if you understand the risks)

### Invalid Origin Format

```
CORSConfigError: Invalid CORS origin format: example.com
```

**Solution**: Add the scheme (http:// or https://) to the origin URL.

### Mixed Wildcard

```
CORSConfigError: Cannot mix wildcard '*' with specific origins. Use either '*' or a list of specific origins.
```

**Solution**: Use either wildcard alone or a list of specific origins, not both.

## Migration Guide

### From Old Configuration

**Old** (.env):
```bash
FRONTEND_URL=*
```

**New** (.env):
```bash
# Production (recommended)
FRONTEND_URL=https://your-frontend-domain.com

# OR development with wildcard (not recommended)
FRONTEND_URL=*
ALLOW_CORS_WILDCARD=true
ENVIRONMENT=development
```

### Adding Multiple Origins

**Before**:
```bash
FRONTEND_URL=https://app.example.com
```

**After**:
```bash
FRONTEND_URL=https://app.example.com,https://admin.example.com,https://mobile.example.com
```

## Testing CORS Configuration

### Run Tests

```bash
cd uat/backend
pytest tests/test_config.py -v
pytest tests/test_cors_integration.py -v
```

### Manual Testing

1. **Test preflight request**:
   ```bash
   curl -X OPTIONS http://localhost:8000/health \
     -H "Origin: https://your-frontend.com" \
     -H "Access-Control-Request-Method: GET" \
     -v
   ```

2. **Check response headers**:
   Look for:
   - `access-control-allow-origin: https://your-frontend.com`
   - `access-control-allow-credentials: true`
   - `access-control-allow-methods: GET, POST, PUT, DELETE, ...`

3. **Test from browser**:
   Open browser console on your frontend and make a request:
   ```javascript
   fetch('http://localhost:8000/health', {
     credentials: 'include'
   }).then(r => r.json()).then(console.log)
   ```

## Security Best Practices

### ✅ DO

- **Use specific origins**: List all allowed frontend domains explicitly
- **Use HTTPS**: Always use HTTPS in production (except localhost in dev)
- **Set credentials**: Keep `allow_credentials=true` for cookie-based auth
- **Review regularly**: Audit CORS origins when adding new frontends
- **Test thoroughly**: Test CORS with actual frontend apps before deploying

### ❌ DON'T

- **Don't use wildcard in production**: Allows any website to make requests
- **Don't use HTTP in production**: Use HTTPS for all production origins
- **Don't ignore startup errors**: Fix CORS configuration errors immediately
- **Don't add untrusted origins**: Only add origins you control
- **Don't mix schemes**: Keep http:// for dev, https:// for prod

## Troubleshooting

### Application Won't Start

**Symptom**: Application crashes on startup with `CORSConfigError`

**Check**:
1. Is `FRONTEND_URL` set?
2. Are all origins valid URLs with schemes?
3. If using wildcard, is `ALLOW_CORS_WILDCARD=true`?

### Browser Shows CORS Error

**Symptom**: Browser console shows "CORS policy" error

**Check**:
1. Is the frontend origin in `FRONTEND_URL`?
2. Does the origin match exactly (including protocol and port)?
3. Is the backend running and accessible?

**Example**:
```
Frontend: http://localhost:3000
FRONTEND_URL: http://localhost:3001  ❌ (port mismatch)
FRONTEND_URL: http://localhost:3000  ✅ (exact match)
```

### Preflight Request Fails

**Symptom**: OPTIONS request returns error or missing headers

**Check**:
1. Origin is in allowed list
2. Method is in `allow_methods`
3. Backend is receiving the request

### Multiple Frontends, One Fails

**Symptom**: Some frontends work, others don't

**Check**:
1. All origins in comma-separated list
2. No typos in URLs
3. Correct protocol (http vs https)
4. Correct port numbers

## CORS Configuration Reference

The new configuration system provides these settings to FastAPI's CORSMiddleware:

```python
{
    "allow_origins": ["https://example.com"],  # From FRONTEND_URL
    "allow_credentials": True,                  # For cookie-based auth
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": ["*"],                     # All request headers allowed
    "expose_headers": ["*"],                    # All response headers exposed
    "max_age": 600,                             # Cache preflight for 10 minutes
}
```

## Support

For issues or questions about CORS configuration:

1. Check application logs for detailed error messages
2. Run tests: `pytest tests/test_config.py -v`
3. Review this documentation
4. Check the `.env.example` file for configuration examples

## Implementation Details

- **Module**: `uat/backend/config.py`
- **Tests**: `uat/backend/tests/test_config.py`, `uat/backend/tests/test_cors_integration.py`
- **Integration**: `uat/backend/main.py`
- **Ticket**: SDT1-56
