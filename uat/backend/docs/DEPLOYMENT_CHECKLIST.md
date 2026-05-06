# Deployment Checklist

## Overview

This checklist ensures all security configurations are properly set before deploying to production. Complete all items before deployment.

## Pre-Deployment Checklist

### 1. CORS Configuration (SDT1-56)

- [ ] `FRONTEND_URL` environment variable is set
  ```bash
  # Example
  export FRONTEND_URL="https://app.example.com"
  ```

- [ ] All frontend domains are included (comma-separated for multiple)
  ```bash
  # Multiple domains
  export FRONTEND_URL="https://app.example.com,https://admin.example.com"
  ```

- [ ] Origins use HTTPS in production (not HTTP)
  ```bash
  # ✅ Correct
  export FRONTEND_URL="https://app.example.com"
  
  # ❌ Wrong for production
  export FRONTEND_URL="http://app.example.com"
  ```

- [ ] Wildcard `*` is NOT used (unless absolutely necessary)
  ```bash
  # ❌ Avoid in production
  export FRONTEND_URL="*"
  ```

- [ ] If wildcard is required, `ALLOW_CORS_WILDCARD=true` is set
  ```bash
  export ALLOW_CORS_WILDCARD="true"  # Only if necessary
  ```

- [ ] `ENVIRONMENT=production` is set
  ```bash
  export ENVIRONMENT="production"
  ```

**Verification:**
```bash
# Check startup logs for:
# ✓ CORS configuration validated successfully
# CORS configured with N origin(s): <your origins>
```

---

### 2. JWT Configuration (SDT1-63)

- [ ] `JWT_SECRET` environment variable is set
  ```bash
  export JWT_SECRET="<secure-random-secret>"
  ```

- [ ] JWT secret is cryptographically secure (not a weak/default secret)
  - [ ] At least 32 characters long
  - [ ] Contains mixed alphanumeric and special characters
  - [ ] Not a known weak secret (e.g., "secret", "dev-secret", etc.)

- [ ] Generate secure secret if needed:
  ```bash
  python -c "from config import generate_jwt_secret; print(generate_jwt_secret())"
  ```

- [ ] `JWT_EXPIRY_HOURS` is set appropriately (default: 24)
  ```bash
  export JWT_EXPIRY_HOURS="24"
  ```

- [ ] JWT secret is stored securely (not in code/repository)
  - [ ] In environment variables
  - [ ] In secrets manager (AWS Secrets Manager, etc.)
  - [ ] NOT in `.env` files committed to git

**Verification:**
```bash
# Check startup logs for:
# ✓ JWT configuration validated successfully
# ✓ JWT secret configured (N characters, ~M bits entropy)
```

---

### 3. Database Configuration

- [ ] `DATABASE_URL` is set
  ```bash
  export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
  ```

- [ ] Database connection uses SSL in production
  ```bash
  # Add ?sslmode=require if needed
  export DATABASE_URL="postgresql://user:pass@host:5432/dbname?sslmode=require"
  ```

- [ ] Database credentials are secure (not default passwords)

- [ ] Database migrations are up to date
  ```bash
  alembic upgrade head
  ```

---

### 4. External Services

#### Jira Integration

- [ ] `JIRA_API_TOKEN` is set
- [ ] `JIRA_EMAIL` is set
- [ ] `JIRA_SERVER` is set
- [ ] `JIRA_PROJECT_KEY` is set

#### GitHub Integration

- [ ] `GITHUB_TOKEN` is set (with appropriate permissions)
- [ ] `GITHUB_REPO` is set (format: `owner/repo`)

#### Railway Integration

- [ ] `RAILWAY_TOKEN` is set (if using Railway deployment)
- [ ] Railway project/service IDs are configured

#### SonarCloud Integration

- [ ] `SONARCLOUD_TOKEN` is set (if using code quality checks)
- [ ] `SONARCLOUD_ORGANIZATION` is set

---

### 5. Logging and Monitoring

- [ ] `LOG_LEVEL` is set appropriately
  ```bash
  # Production: INFO or WARNING
  export LOG_LEVEL="INFO"
  
  # Development: DEBUG
  export LOG_LEVEL="DEBUG"
  ```

- [ ] Log aggregation is configured (Datadog, CloudWatch, etc.)

- [ ] Error monitoring is configured (Sentry, Rollbar, etc.)

---

### 6. Rate Limiting

- [ ] Rate limiting is enabled (default: on)

- [ ] Rate limits are appropriate for production traffic
  - Check `rate_limiter.py` for current limits
  - Adjust if needed based on expected load

---

### 7. Environment Variables Summary

**Required for Production:**

```bash
# Core
export ENVIRONMENT="production"

# CORS (SDT1-56)
export FRONTEND_URL="https://app.example.com"

# JWT (SDT1-63)
export JWT_SECRET="<secure-random-secret>"
export JWT_EXPIRY_HOURS="24"

# Database
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Jira
export JIRA_API_TOKEN="<jira-token>"
export JIRA_EMAIL="bot@example.com"
export JIRA_SERVER="https://yourcompany.atlassian.net"
export JIRA_PROJECT_KEY="SDT1"

# GitHub
export GITHUB_TOKEN="<github-token>"
export GITHUB_REPO="owner/repo"

# Optional
export LOG_LEVEL="INFO"
```

---

## Deployment Steps

### Step 1: Local Testing

1. Set all required environment variables locally
2. Start the application:
   ```bash
   cd uat/backend
   uvicorn main:app --reload
   ```
3. Check startup logs for validation messages
4. Test critical endpoints:
   - `GET /health` - Health check
   - `POST /auth/login` - Authentication
   - CORS from frontend domain

### Step 2: Staging Deployment

1. Deploy to staging environment first
2. Set staging-specific environment variables:
   ```bash
   export ENVIRONMENT="production"  # Use production rules
   export FRONTEND_URL="https://staging.app.example.com"
   ```
3. Run smoke tests:
   - Authentication flow
   - CORS from staging frontend
   - Database connectivity
   - External service integrations
4. Monitor logs for errors

### Step 3: Production Deployment

1. **Set all production environment variables**
2. **Double-check CORS and JWT configuration**
3. Deploy application
4. Verify startup logs:
   ```
   ✓ Database configured
   ✓ CORS configuration validated successfully
   ✓ JWT configuration validated successfully
   ```
5. Test from production frontend
6. Monitor error rates and logs

### Step 4: Post-Deployment

- [ ] Verify frontend can connect to backend
- [ ] Test authentication flow
- [ ] Check error monitoring dashboard
- [ ] Review application logs
- [ ] Monitor performance metrics
- [ ] Test critical user flows

---

## Rollback Plan

If deployment fails:

1. **Check logs** for specific error messages
2. **Common issues:**
   - Missing environment variables
   - Invalid CORS configuration
   - Weak JWT secret
   - Database connection issues
3. **Rollback application** to previous version if needed
4. **Fix configuration** and redeploy

---

## Security Validation

### Automated Checks

Run security tests before deployment:

```bash
# Backend tests
cd uat/backend
pytest tests/test_config.py -v

# Check for secrets in code
git secrets --scan

# Check dependencies for vulnerabilities
pip-audit
```

### Manual Security Review

- [ ] No secrets in code or repository
- [ ] All environment variables use secure values
- [ ] CORS only allows trusted origins
- [ ] JWT secret is strong and unique
- [ ] HTTPS is used for all production URLs
- [ ] Database uses SSL
- [ ] API tokens have minimal required permissions

---

## Environment-Specific Configurations

### Development

```bash
export ENVIRONMENT="development"
export FRONTEND_URL="http://localhost:3000"
export JWT_SECRET="<any-secret-for-dev>"
export LOG_LEVEL="DEBUG"
# Other vars as needed
```

### Staging

```bash
export ENVIRONMENT="production"  # Use production security rules
export FRONTEND_URL="https://staging.app.example.com"
export JWT_SECRET="<staging-secret>"
export LOG_LEVEL="INFO"
# Production-like configuration
```

### Production

```bash
export ENVIRONMENT="production"
export FRONTEND_URL="https://app.example.com"
export JWT_SECRET="<production-secret>"
export LOG_LEVEL="INFO"
# All required environment variables
```

---

## Troubleshooting

### Application Won't Start

**Check logs for:**
- `❌ CORS configuration error: <message>`
- `❌ JWT configuration error: <message>`

**Common fixes:**
- Set missing environment variables
- Fix invalid origin URLs
- Generate new JWT secret

### CORS Errors in Browser

**Symptoms:**
```
Access to fetch at 'https://api.example.com' from origin 'https://app.example.com' 
has been blocked by CORS policy
```

**Fixes:**
1. Add frontend domain to `FRONTEND_URL`
2. Ensure protocol matches (http vs https)
3. Check for port mismatches
4. Restart backend after config changes

### Authentication Errors

**Symptoms:**
- Tokens not working after restart
- 401 Unauthorized errors

**Fixes:**
1. Ensure `JWT_SECRET` is set and persistent
2. Check JWT expiry settings
3. Verify token generation/validation logic

---

## Platform-Specific Deployment

### Railway

```bash
# Set environment variables
railway variables set ENVIRONMENT="production"
railway variables set FRONTEND_URL="https://yourapp.com"
railway variables set JWT_SECRET="<generate-secure-secret>"
# ... other variables

# Deploy
railway up
```

### Render

1. Go to Dashboard → Service → Environment
2. Add all required environment variables
3. Deploy from GitHub
4. Check logs in dashboard

### Heroku

```bash
# Set environment variables
heroku config:set ENVIRONMENT="production"
heroku config:set FRONTEND_URL="https://yourapp.com"
heroku config:set JWT_SECRET="<generate-secure-secret>"
# ... other variables

# Deploy
git push heroku main
```

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t backend:latest .

# Run with environment variables
docker run -p 8000:8000 \
  -e ENVIRONMENT="production" \
  -e FRONTEND_URL="https://app.example.com" \
  -e JWT_SECRET="<secure-secret>" \
  # ... other -e flags
  backend:latest
```

---

## Contact

For deployment issues:
- **DevOps Team**: devops@example.com
- **Security Team**: security@example.com
- **Jira**: Create ticket in SDT1 project

---

**Document Version:** 1.0  
**Last Updated:** 2024 (SDT1-56, SDT1-63)  
**Maintained By:** DevOps Team
