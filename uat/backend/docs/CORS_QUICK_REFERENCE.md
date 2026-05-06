# CORS Configuration - Quick Reference

Quick reference for common CORS configuration scenarios. For detailed documentation, see [CORS_CONFIGURATION.md](./CORS_CONFIGURATION.md).

## Common Commands

### Generate JWT Secret
```bash
python -c "from config import generate_jwt_secret; print(generate_jwt_secret())"
```

### Test CORS Configuration
```bash
# Check startup logs
uvicorn main:app --reload

# Look for:
# ✓ CORS configuration validated successfully
# CORS configured with N origin(s): <your-origins>
```

### Validate Configuration
```bash
# Run tests
pytest tests/test_config.py -v
```

---

## Environment Variable Cheat Sheet

### Minimum Production Setup
```bash
export ENVIRONMENT="production"
export FRONTEND_URL="https://app.example.com"
export JWT_SECRET="<secure-secret>"
```

### Minimum Development Setup
```bash
export ENVIRONMENT="development"
# FRONTEND_URL defaults to http://localhost:3000
```

---

## Quick Troubleshooting

| Error | Quick Fix |
|-------|-----------|
| "FRONTEND_URL must be configured" | `export FRONTEND_URL="https://yourapp.com"` |
| "Wildcard detected in production" | Add `ALLOW_CORS_WILDCARD=true` OR use specific origin |
| "Invalid CORS origin format" | Add protocol: `https://` or `http://` |
| "Cannot mix wildcard with specific origins" | Use either `*` OR specific domains, not both |
| Browser CORS error | Add your domain to FRONTEND_URL |

---

## Configuration Examples

### ✅ Single Production App
```bash
export ENVIRONMENT="production"
export FRONTEND_URL="https://app.example.com"
```

### ✅ Multiple Production Apps
```bash
export ENVIRONMENT="production"
export FRONTEND_URL="https://app.example.com,https://admin.example.com"
```

### ✅ Local Development
```bash
export ENVIRONMENT="development"
export FRONTEND_URL="http://localhost:3000"
```

### ✅ Custom Dev Port (Vite)
```bash
export ENVIRONMENT="development"
export FRONTEND_URL="http://localhost:5173"
```

### ⚠️ Public API (Use with Caution)
```bash
export ENVIRONMENT="development"
export FRONTEND_URL="*"
export ALLOW_CORS_WILDCARD="true"
```

---

## Valid Origin Formats

| Format | Example | Valid? |
|--------|---------|--------|
| HTTPS with domain | `https://app.example.com` | ✅ Yes |
| HTTP localhost | `http://localhost:3000` | ✅ Yes |
| HTTPS with subdomain | `https://admin.app.example.com` | ✅ Yes |
| With port | `https://example.com:8443` | ✅ Yes |
| IPv4 | `http://127.0.0.1:3000` | ✅ Yes |
| IPv6 | `http://[::1]:3000` | ✅ Yes |
| Wildcard | `*` | ⚠️ With flag only |
| No protocol | `example.com` | ❌ No |
| FTP protocol | `ftp://example.com` | ❌ No |
| Empty/whitespace | `   ` | ❌ No |

---

## Platform-Specific Setup

### Railway
```bash
railway variables set FRONTEND_URL="https://yourapp.com"
railway variables set ENVIRONMENT="production"
```

### Render
Dashboard → Environment → Add:
- `FRONTEND_URL` = `https://yourapp.com`
- `ENVIRONMENT` = `production`

### Heroku
```bash
heroku config:set FRONTEND_URL="https://yourapp.com"
heroku config:set ENVIRONMENT="production"
```

### Docker
```bash
docker run -p 8000:8000 \
  -e ENVIRONMENT="production" \
  -e FRONTEND_URL="https://yourapp.com" \
  myapp:latest
```

---

## Testing Commands

### Check Environment Variables
```bash
echo $FRONTEND_URL
echo $ENVIRONMENT
echo $ALLOW_CORS_WILDCARD
```

### Test CORS from Browser
```javascript
fetch('http://localhost:8000/health', {
  credentials: 'include'
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

### Check Response Headers
```bash
curl -H "Origin: https://app.example.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8000/health \
     -v
```

---

## Security Checklist

Production deployment:
- [ ] `FRONTEND_URL` uses HTTPS
- [ ] No wildcard `*` origin
- [ ] All origins explicitly listed
- [ ] `ENVIRONMENT=production`
- [ ] JWT_SECRET is secure
- [ ] Test CORS from actual frontend
- [ ] Monitor logs after deployment

---

## Need More Help?

- 📖 [Full CORS Documentation](./CORS_CONFIGURATION.md)
- 🔐 [JWT Configuration](./JWT_CONFIGURATION.md)
- 🚀 [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- 🧪 Run tests: `pytest tests/test_config.py -v`

---

**Quick Reference v1.0** | SDT1-56
