# CORS Configuration Guide

## Overview

The UAT backend implements hardened CORS (Cross-Origin Resource Sharing) configuration to protect against unauthorized cross-origin requests while maintaining flexibility for legitimate frontend applications.

## Configuration

CORS is configured via the `FRONTEND_URL` environment variable.

### Single Origin (Recommended for Production)

```bash
FRONTEND_URL=https://app.example.com
```

### Multiple Origins

Separate multiple origins with commas:

```bash
FRONTEND_URL=http://localhost:3000,https://staging.example.com,https://app.example.com
```

### Development Mode (Wildcard)

⚠️ **WARNING: INSECURE - Use only in development**

```bash
FRONTEND_URL=*
```

This allows requests from any origin. **Never use in production.**

### No CORS (Most Secure)

Leave `FRONTEND_URL` empty or unset to block all cross-origin requests:

```bash
# FRONTEND_URL not set
```

This is the most secure configuration but will prevent browser-based frontends from accessing the API.

## URL Requirements

Each origin URL must:

- Include the scheme (`http://` or `https://`)
- Include a valid domain or IP address
- NOT include a path (automatically stripped if present)
- NOT include credentials (username/password)
- NOT include fragments (#) or query strings (?)

### Valid Examples

✅ `http://localhost:3000`  
✅ `https://app.example.com`  
✅ `https://staging.app.example.com`  
✅ `http://127.0.0.1:8080`

### Invalid Examples

❌ `localhost:3000` (missing scheme)  
❌ `example.com` (missing scheme)  
❌ `ftp://example.com` (wrong scheme)  
❌ `http://user:pass@example.com` (includes credentials)  
❌ `http://example.com/api` (includes path - will be stripped)

## Security Features

### 1. URL Validation

All origins are validated for:
- Proper URL structure
- HTTP/HTTPS scheme only
- No embedded credentials
- Valid domain format

Invalid URLs are automatically rejected with a warning logged.

### 2. Automatic Normalization

Origins are automatically normalized:
- Trailing slashes removed
- Whitespace trimmed
- Empty entries filtered

### 3. Security Warnings

The system logs warnings for:
- Wildcard configuration (`*`)
- Invalid URLs in the configuration
- Missing or empty `FRONTEND_URL`

### 4. Secure Defaults

- Empty/unset `FRONTEND_URL` → Block all origins (most secure)
- Invalid URLs → Ignored, not allowed
- No wildcard by default

## Testing

Run the CORS configuration tests:

```bash
cd uat/backend
pytest tests/test_cors_config.py -v
```

Run integration tests:

```bash
pytest tests/test_main.py -v
```

## Troubleshooting

### Browser Shows CORS Error

**Symptom:** Browser console shows CORS policy error

**Solution:** Ensure `FRONTEND_URL` includes the exact origin of your frontend:
- Check the scheme (http vs https)
- Check the port number (must match)
- Check the domain spelling

Example:
```bash
# If frontend runs on http://localhost:3000
FRONTEND_URL=http://localhost:3000

# NOT: http://localhost (missing port)
# NOT: http://127.0.0.1:3000 (different host)
```

### Multiple Frontends Not Working

**Symptom:** One frontend works, others get CORS errors

**Solution:** List ALL frontend origins, comma-separated:

```bash
FRONTEND_URL=http://localhost:3000,https://staging.example.com,https://app.example.com
```

### Warning: "Invalid CORS origins ignored"

**Symptom:** Startup logs show invalid origin warning

**Solution:** Check that each origin:
1. Starts with `http://` or `https://`
2. Has a valid domain
3. Doesn't include paths or credentials

### Production Security Warning

**Symptom:** Logs show "CORS configured with wildcard (*) - INSECURE"

**Solution:** Replace wildcard with specific origins:

```bash
# BAD (development only):
FRONTEND_URL=*

# GOOD (production):
FRONTEND_URL=https://app.example.com
```

## Implementation Details

### Files

- `uat/backend/cors_config.py` - Core CORS parsing and validation logic
- `uat/backend/config.py` - Settings integration
- `uat/backend/main.py` - FastAPI middleware setup
- `uat/backend/tests/test_cors_config.py` - Unit tests
- `uat/backend/tests/test_main.py` - Integration tests

### Functions

- `get_cors_origins()` - Parse and validate origins from `FRONTEND_URL`
- `format_cors_origins_for_middleware()` - Format for FastAPI middleware
- `_is_valid_url()` - Validate individual URL
- `_parse_cors_origins()` - Parse comma-separated origins

## Migration from Previous Version

Previous configuration:

```python
# Old (main.py)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")
allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"]
```

New configuration:

```python
# New (main.py)
from config import settings
cors_origins = settings.get_cors_origins()
allow_origins=cors_origins
```

### Breaking Changes

1. **Empty `FRONTEND_URL` now blocks all origins** (previously allowed all with `*` default)
   - **Action:** Explicitly set `FRONTEND_URL` to your frontend origin(s)

2. **Invalid URLs are now rejected** (previously accepted)
   - **Action:** Ensure all URLs in `FRONTEND_URL` are valid

3. **Paths in URLs are automatically stripped** (previously included)
   - **Action:** Remove paths from URLs if present

### Migration Steps

1. Set `FRONTEND_URL` explicitly in your environment
2. Verify format: `http(s)://domain:port`
3. Test CORS headers in browser dev tools
4. Check backend startup logs for validation warnings

## Best Practices

### Development

```bash
# Local development with React dev server
FRONTEND_URL=http://localhost:3000
```

### Staging

```bash
# Staging environment
FRONTEND_URL=https://staging.app.example.com
```

### Production

```bash
# Production with single frontend
FRONTEND_URL=https://app.example.com

# Production with multiple environments
FRONTEND_URL=https://app.example.com,https://beta.app.example.com
```

### Testing Locally

```bash
# Test multiple frontends locally
FRONTEND_URL=http://localhost:3000,http://localhost:3001
```

## See Also

- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP CORS Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Origin_Resource_Sharing_Cheat_Sheet.html)
