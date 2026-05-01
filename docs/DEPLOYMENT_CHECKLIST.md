# Deployment Checklist - CORS Security Update

This checklist ensures smooth deployment of the hardened CORS configuration (SDT1-56).

## Pre-Deployment

### 1. Environment Variables Audit

Review and update environment variables in all deployment environments:

#### Development/Local
- [ ] `ENVIRONMENT=development` (or leave unset)
- [ ] `FRONTEND_URL` - optional, leave empty for localhost defaults
- [ ] Verify JWT_SECRET is set (required)

#### Staging
- [ ] `ENVIRONMENT=staging`
- [ ] `FRONTEND_URL` - **must be set** to staging frontend URL(s)
- [ ] Example: `FRONTEND_URL=https://staging.example.com`
- [ ] Verify JWT_SECRET is set (required)

#### Production
- [ ] `ENVIRONMENT=production`
- [ ] `FRONTEND_URL` - **must be set** to production frontend URL(s)
- [ ] Example: `FRONTEND_URL=https://app.example.com`
- [ ] **Verify HTTPS is used** (not HTTP)
- [ ] **Verify no wildcard** (`*`) is used
- [ ] Verify JWT_SECRET is set (required)

### 2. Configuration Files

Update deployment configuration files:

#### Docker Compose
```yaml
# docker-compose.yml
environment:
  - ENVIRONMENT=production
  - FRONTEND_URL=https://app.example.com
  - JWT_SECRET=${JWT_SECRET}
```

#### Kubernetes
```yaml
# deployment.yaml
env:
  - name: ENVIRONMENT
    value: "production"
  - name: FRONTEND_URL
    value: "https://app.example.com"
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: jwt-secret
```

#### Environment File (.env)
```bash
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com
JWT_SECRET=your-secret-key
```

- [ ] Docker compose files updated
- [ ] Kubernetes manifests updated
- [ ] .env files updated for each environment
- [ ] CI/CD pipeline environment variables updated

### 3. Code Review

- [ ] All changes reviewed in PR
- [ ] Tests passing (`pytest tests/test_cors_config.py`)
- [ ] No hardcoded URLs in source code
- [ ] Config properly imported from `config.py`

## Deployment Process

### Step 1: Deploy to Development
- [ ] Pull latest code
- [ ] Run tests: `pytest`
- [ ] Start application: `uvicorn main:app`
- [ ] Verify startup log: "✓ CORS configured with allowed origins: [...]"
- [ ] Test frontend connectivity
- [ ] Check browser console for CORS errors

### Step 2: Deploy to Staging
- [ ] Set `ENVIRONMENT=staging`
- [ ] Set `FRONTEND_URL` to staging URL(s)
- [ ] Deploy application
- [ ] Verify startup log shows correct origins
- [ ] Test all frontend features
- [ ] Verify API calls from frontend succeed
- [ ] Check application logs for CORS-related errors

### Step 3: Deploy to Production
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `FRONTEND_URL` to production URL(s)
- [ ] **Double-check HTTPS is used**
- [ ] **Verify no wildcard (*) is present**
- [ ] Deploy application
- [ ] Verify startup log: "✓ CORS configured with allowed origins: ['https://...']"
- [ ] Smoke test critical user flows
- [ ] Monitor error logs for CORS issues
- [ ] Monitor application metrics

## Post-Deployment Validation

### Automated Tests
```bash
# Run health check
curl https://api.example.com/health

# Test CORS preflight
curl -X OPTIONS https://api.example.com/api/endpoint \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

Expected response headers:
```
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
```

### Manual Validation
- [ ] Frontend loads without errors
- [ ] Login flow works
- [ ] API calls succeed
- [ ] No CORS errors in browser console
- [ ] Application logs show no configuration errors

### Security Validation
- [ ] Wildcard origin not in use
- [ ] HTTPS enforced in production
- [ ] Only legitimate domains allowed
- [ ] Credentials included in CORS policy

## Rollback Plan

If issues occur after deployment:

### Option 1: Quick Fix (Environment Variable)
```bash
# Temporarily allow additional origin if needed
FRONTEND_URL=https://app.example.com,https://backup.example.com
```

### Option 2: Revert Deployment
1. Revert to previous application version
2. Restore previous environment configuration
3. Verify application starts successfully
4. Fix issues in development
5. Re-deploy with fixes

## Troubleshooting

### Application Won't Start

**Symptom:** Application crashes on startup with configuration error

**Check:**
```bash
# View application logs
docker logs <container-id>
# or
kubectl logs <pod-name>
```

**Common Issues:**
- `FRONTEND_URL` not set in production
- Invalid URL format in `FRONTEND_URL`
- Missing `JWT_SECRET`

**Quick Fix:**
```bash
# Set missing variable
export FRONTEND_URL=https://app.example.com
# Restart application
```

### CORS Errors After Deployment

**Symptom:** Browser console shows CORS policy errors

**Check:**
1. Verify frontend URL matches exactly (including protocol, subdomain, port)
2. Check application logs for configured origins
3. Test with curl:
   ```bash
   curl -H "Origin: https://app.example.com" https://api.example.com/health -v
   ```

**Common Issues:**
- Frontend URL doesn't match configured origin
- Multiple domains, but only one configured
- HTTP vs HTTPS mismatch

**Quick Fix:**
```bash
# Add missing origin
FRONTEND_URL=https://app.example.com,https://www.example.com
```

### Performance Issues

**Symptom:** Slow API responses after deployment

**Check:**
- CORS middleware is efficient and shouldn't impact performance
- Check for unrelated issues (database, network, etc.)

## Communication Plan

### Before Deployment
- [ ] Notify team of deployment window
- [ ] Share expected downtime (if any)
- [ ] Provide rollback timeline

### During Deployment
- [ ] Update status page
- [ ] Monitor logs and metrics
- [ ] Keep team informed of progress

### After Deployment
- [ ] Confirm successful deployment
- [ ] Share validation results
- [ ] Document any issues encountered
- [ ] Update team on next steps

## Success Criteria

Deployment is considered successful when:

- [ ] ✅ Application starts without errors
- [ ] ✅ Startup log shows correct CORS origins
- [ ] ✅ Frontend can access API without CORS errors
- [ ] ✅ All user flows work correctly
- [ ] ✅ No security warnings in logs
- [ ] ✅ Production uses HTTPS only (no HTTP)
- [ ] ✅ No wildcard origin in production
- [ ] ✅ All tests pass
- [ ] ✅ No performance degradation

## Sign-Off

- [ ] Developer: Code changes complete and tested
- [ ] QA: Staging validation passed
- [ ] DevOps: Configuration updated in all environments
- [ ] Security: Configuration reviewed and approved
- [ ] Product: Feature verified in production

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Related Ticket:** SDT1-56
