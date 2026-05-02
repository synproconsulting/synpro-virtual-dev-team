# Token Rotation Runbook

**Version:** 1.0  
**Last Updated:** 2024  
**Owner:** DevOps / Security Team  
**Severity:** High - Security Critical  

## Table of Contents

1. [Overview](#overview)
2. [Token Inventory](#token-inventory)
3. [Rotation Schedule](#rotation-schedule)
4. [Pre-Rotation Checklist](#pre-rotation-checklist)
5. [JWT Secret Rotation](#jwt-secret-rotation)
6. [Railway API Token Rotation](#railway-api-token-rotation)
7. [Database Credentials Rotation](#database-credentials-rotation)
8. [SMTP Credentials Rotation](#smtp-credentials-rotation)
9. [Emergency Rotation](#emergency-rotation)
10. [Post-Rotation Validation](#post-rotation-validation)
11. [Rollback Procedures](#rollback-procedures)
12. [Troubleshooting](#troubleshooting)
13. [Audit Log Template](#audit-log-template)

---

## Overview

This runbook provides step-by-step procedures for rotating all authentication tokens, API keys, and credentials used in the SynPro Virtual Dev Team platform. Token rotation is a critical security practice that limits the exposure window if credentials are compromised.

### When to Rotate

**Scheduled Rotation** (Recommended):
- JWT secrets: Every 90 days
- Railway API tokens: Every 90 days
- Database credentials: Every 180 days
- SMTP credentials: Every 180 days

**Emergency Rotation** (Immediate):
- Suspected credential compromise
- Security incident or breach
- Employee/contractor offboarding with access
- Accidental exposure (committed to git, logged, etc.)
- Compliance audit requirement

### Key Principles

1. **Zero Downtime**: All rotations should be performed with zero or minimal downtime
2. **Overlap Period**: Maintain support for both old and new credentials during transition
3. **Validation**: Always validate new credentials before fully cutting over
4. **Documentation**: Document every rotation with date, reason, and who performed it
5. **Communication**: Notify team members of scheduled rotations

---

## Token Inventory

| Token Type | Location | Purpose | Rotation Frequency | Priority |
|------------|----------|---------|-------------------|----------|
| JWT_SECRET | UAT Backend env vars | User session tokens | 90 days | Critical |
| RAILWAY_API_TOKEN | UAT Backend env vars | Railway deployment API | 90 days | High |
| DATABASE_URL | UAT Backend env vars | PostgreSQL connection | 180 days | Critical |
| SMTP_PASSWORD | UAT Backend env vars | Email service | 180 days | Medium |
| Frontend API keys | Control Centre env vars | Backend API access | As needed | Medium |

### Environment Variables Map

```bash
# UAT Backend (.env)
JWT_SECRET=<base64-encoded-secret>
JWT_EXPIRY_HOURS=24
RAILWAY_API_TOKEN=<railway-token>
DATABASE_URL=postgresql://user:password@host:port/dbname
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=email@example.com
SMTP_PASSWORD=<app-password>
SMTP_FROM_EMAIL=email@example.com
SMTP_FROM_NAME=SynPro Virtual Dev Team
ENVIRONMENT=production
FRONTEND_URL=https://app.example.com
```

---

## Rotation Schedule

### Calendar

Create calendar reminders for:

- **Quarterly** (every 3 months):
  - JWT secret rotation
  - Railway API token rotation
  
- **Semi-annually** (every 6 months):
  - Database credential rotation
  - SMTP credential rotation
  
- **Annual** (every 12 months):
  - Full security audit
  - Review and update this runbook

### Timeline Template

Use this template for planned rotations:

```
Week -2: Announce rotation window to team
Week -1: Prepare new credentials, test in staging
Day 0, 02:00 UTC: Execute rotation in production
Day 0, 02:30 UTC: Validation and monitoring
Day +1: Review logs and confirm success
Week +1: Decommission old credentials
```

---

## Pre-Rotation Checklist

Before rotating any token, complete this checklist:

- [ ] **Schedule Maintenance Window**: Choose low-traffic time (e.g., 02:00-04:00 UTC)
- [ ] **Notify Team**: Send notification 2 weeks, 1 week, and 1 day before rotation
- [ ] **Backup Current Configuration**: Export current environment variables
- [ ] **Test New Credentials**: Validate in staging environment first
- [ ] **Review Documentation**: Ensure this runbook is current
- [ ] **Prepare Rollback Plan**: Have old credentials ready to restore
- [ ] **Check Monitoring**: Ensure monitoring/alerting is active
- [ ] **Identify Dependencies**: List all services that use the credential
- [ ] **Create Audit Record**: Document rotation in audit log

### Backup Script

```bash
#!/bin/bash
# backup_env.sh - Backup environment variables

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./env_backups"
mkdir -p "$BACKUP_DIR"

# Backup Railway environment variables
railway variables --json > "$BACKUP_DIR/railway_vars_${DATE}.json"

# Backup local .env (redact sensitive values for git)
cat .env | sed 's/=.*/=***REDACTED***/g' > "$BACKUP_DIR/env_structure_${DATE}.txt"

echo "✓ Backup created at $BACKUP_DIR/railway_vars_${DATE}.json"
echo "⚠️  Keep this backup secure and delete after rotation is validated"
```

---

## JWT Secret Rotation

The JWT secret is used to sign user authentication tokens. Rotating it will invalidate all existing user sessions, requiring users to log in again.

### Impact Assessment

- **User Impact**: High - All users must re-authenticate
- **Downtime**: None (if done correctly)
- **Services Affected**: UAT Backend, all authenticated API endpoints
- **Estimated Duration**: 15-30 minutes

### Prerequisites

- [ ] Python 3.11+ installed
- [ ] Access to production environment variables
- [ ] Maintenance window scheduled
- [ ] User notification sent
- [ ] Backup of current JWT_SECRET

### Step-by-Step Procedure

#### 1. Generate New JWT Secret

```bash
# Navigate to UAT backend directory
cd uat/backend

# Generate a new secure JWT secret
python3 generate_jwt_secret.py

# Output will be something like:
# Generated secure JWT secret (64 bytes, ~512 bits entropy):
# h8Kx2Vp9qY3mN7zL4jR6tP8wE5sA1xC9vB2nM4kQ6hF7gD3jL8pW9rT5yU2iO0aX=
```

**Save this secret securely** - you'll need it in the next steps.

#### 2. Validate New Secret

```bash
# Validate the generated secret
python3 generate_jwt_secret.py --validate "YOUR_NEW_SECRET_HERE"

# Should output:
# ✓ Secret appears to be strong
# Recommendations:
#   - Store securely (e.g., environment variables, secrets manager)
#   - Never commit to version control
#   - Rotate regularly (e.g., every 90 days)
```

#### 3. Update Environment Variable (Staging)

First, test in staging:

```bash
# If using Railway CLI
railway variables --environment staging --set JWT_SECRET="YOUR_NEW_SECRET_HERE"

# Or manually update in Railway dashboard:
# Project > staging environment > Variables > JWT_SECRET
```

#### 4. Test in Staging

```bash
# Test authentication flow
curl -X POST https://staging.example.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "username": "testuser"
  }'

# Should receive a valid JWT token in response
# Verify token works for authenticated endpoints
curl https://staging.example.com/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 5. Schedule Production Update

```bash
# Set the new JWT secret in production
railway variables --environment production --set JWT_SECRET="YOUR_NEW_SECRET_HERE"

# The backend will restart automatically and pick up the new secret
```

#### 6. Monitor Logs

```bash
# Watch for successful startup with new secret
railway logs --environment production --service uat-backend

# Look for:
# "✓ JWT secret configured (XXX characters, ~512 bits entropy)"
```

#### 7. Verify Production

```bash
# Test authentication immediately after rotation
curl -X POST https://app.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test-account@example.com",
    "password": "YourTestPassword123!@#"
  }'

# Should receive a new valid token
```

#### 8. Document Rotation

Update the audit log (see template at end of document):

```
Date: 2024-XX-XX
Token: JWT_SECRET
Performed by: John Doe
Reason: Scheduled 90-day rotation
Old secret (last 8 chars): ...X7D9kL2p
New secret (last 8 chars): ...9rT5yU2i
Status: Success
Downtime: 0 seconds
```

### Rollback Procedure

If issues occur:

```bash
# Restore the old JWT secret
railway variables --environment production --set JWT_SECRET="OLD_SECRET_HERE"

# Monitor logs for successful restart
railway logs --environment production --service uat-backend

# Verify authentication works
curl -X POST https://app.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!@#"}'
```

### Common Issues

**Issue**: Backend fails to start after rotation
- **Cause**: New secret doesn't meet validation requirements
- **Solution**: Validate secret with `generate_jwt_secret.py --validate` before setting

**Issue**: Users still logged in with old tokens
- **Cause**: Token hasn't expired yet (default 24 hours)
- **Solution**: This is expected. Users will need to re-authenticate when token expires or they log out

**Issue**: "Invalid token" errors in logs
- **Cause**: Clients trying to use tokens signed with old secret
- **Solution**: This is expected during rotation. Clients will re-authenticate automatically

---

## Railway API Token Rotation

The Railway API token is used for deployment automation and infrastructure management. Rotating it affects the UAT Deploy tab functionality.

### Impact Assessment

- **User Impact**: Low - Only affects deployment operations
- **Downtime**: None
- **Services Affected**: UAT Backend Railway API integration
- **Estimated Duration**: 10-15 minutes

### Prerequisites

- [ ] Access to Railway dashboard (https://railway.app)
- [ ] Access to production environment variables
- [ ] Backup of current RAILWAY_API_TOKEN

### Step-by-Step Procedure

#### 1. Create New Railway Token

1. Log in to Railway dashboard: https://railway.app
2. Click your profile icon → **Account Settings**
3. Navigate to **Tokens** tab
4. Click **Create New Token**
5. Name: `synpro-vdt-production-YYYY-MM-DD`
6. **Required scopes**:
   - ✓ Read projects, services, deployments
   - ✓ Trigger deployments
   - ✗ Do NOT grant write permissions to variables or infrastructure
7. Click **Create Token**
8. **Copy the token immediately** - it won't be shown again

#### 2. Validate New Token

```bash
# Test the new token with a simple API call
curl -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer YOUR_NEW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ projects { edges { node { id name } } } }"}'

# Should return a list of projects (not an error)
```

#### 3. Update Environment Variable (Staging)

```bash
# Update staging environment first
railway variables --environment staging --set RAILWAY_API_TOKEN="YOUR_NEW_TOKEN"
```

#### 4. Test in Staging

```bash
# Test deployment trigger functionality
curl -X POST https://staging.example.com/api/railway/projects \
  -H "Authorization: Bearer YOUR_STAGING_JWT"

# Should return project list without errors
```

#### 5. Update Production

```bash
# Update production environment
railway variables --environment production --set RAILWAY_API_TOKEN="YOUR_NEW_TOKEN"

# Service will restart automatically
```

#### 6. Verify Production

```bash
# Test deployment operations
curl -X POST https://app.example.com/api/railway/projects \
  -H "Authorization: Bearer YOUR_PRODUCTION_JWT"

# Should return project list successfully
```

#### 7. Revoke Old Token

1. Return to Railway dashboard → **Account Settings** → **Tokens**
2. Find the old token (synpro-vdt-production-YYYY-MM-DD-old)
3. Click **Revoke**
4. Confirm revocation

#### 8. Document Rotation

```
Date: 2024-XX-XX
Token: RAILWAY_API_TOKEN
Performed by: Jane Smith
Reason: Scheduled 90-day rotation
Old token (prefix): rtf_abc123...
New token (prefix): rtf_xyz789...
Status: Success
Old token revoked: Yes
```

### Rollback Procedure

```bash
# Restore old token if new one has issues
railway variables --environment production --set RAILWAY_API_TOKEN="OLD_TOKEN_HERE"

# Do NOT revoke old token until new one is confirmed working
```

### Common Issues

**Issue**: 401 Unauthorized errors after rotation
- **Cause**: Token doesn't have required scopes
- **Solution**: Create new token with all required scopes (see step 1)

**Issue**: Railway API calls fail silently
- **Cause**: Network issues or rate limiting
- **Solution**: Check Railway status page, verify token has correct permissions

---

## Database Credentials Rotation

Database credential rotation is more complex and requires coordination with your database provider.

### Impact Assessment

- **User Impact**: Medium - Brief connection disruption possible
- **Downtime**: 30-60 seconds (connection pool refresh)
- **Services Affected**: All services that connect to the database
- **Estimated Duration**: 1-2 hours

### Prerequisites

- [ ] Access to Railway database dashboard
- [ ] Database connection pool size documented
- [ ] Backup completed within last 24 hours
- [ ] Maintenance window scheduled during low traffic

### Step-by-Step Procedure

#### 1. Create New Database User (Railway PostgreSQL)

If using Railway PostgreSQL:

1. Log in to Railway dashboard
2. Navigate to your project → PostgreSQL service
3. Go to **Variables** tab
4. Note current DATABASE_URL

Railway databases don't support multiple users by default. Instead, you'll:

**Option A: Zero-downtime rotation (Recommended)**

Railway manages PostgreSQL credentials. To rotate:

1. Create a new PostgreSQL service in Railway
2. Migrate data to new service
3. Update DATABASE_URL to point to new service
4. Remove old service

**Option B: Password rotation (if your DB supports it)**

```sql
-- Connect to database as superuser
psql $DATABASE_URL

-- Create new user with same permissions
CREATE USER synpro_new WITH PASSWORD 'NEW_SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE synpro_db TO synpro_new;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO synpro_new;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO synpro_new;

-- Test connection with new credentials
\q
psql postgresql://synpro_new:NEW_SECURE_PASSWORD_HERE@host:port/synpro_db
```

#### 2. Update DATABASE_URL

```bash
# Construct new DATABASE_URL
NEW_DATABASE_URL="postgresql://synpro_new:NEW_SECURE_PASSWORD_HERE@host:port/synpro_db"

# Update staging first
railway variables --environment staging --set DATABASE_URL="$NEW_DATABASE_URL"
```

#### 3. Test in Staging

```bash
# Verify database connectivity
railway logs --environment staging --service uat-backend | grep -i database

# Test basic CRUD operations via API
curl -X POST https://staging.example.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!@#"}'
```

#### 4. Update Production

```bash
# Update production DATABASE_URL
railway variables --environment production --set DATABASE_URL="$NEW_DATABASE_URL"

# Monitor for successful connection
railway logs --environment production --service uat-backend
```

#### 5. Verify Production

```bash
# Test database operations
curl https://app.example.com/api/health

# Check logs for any connection errors
railway logs --environment production --service uat-backend --recent 100
```

#### 6. Decommission Old Credentials

```sql
-- After 24-48 hours of stable operation, remove old user
psql $DATABASE_URL

-- Verify no active connections from old user
SELECT * FROM pg_stat_activity WHERE usename = 'synpro_old';

-- Drop old user
DROP USER synpro_old;
```

#### 7. Document Rotation

```
Date: 2024-XX-XX
Token: DATABASE_URL credentials
Performed by: DevOps Team
Reason: Scheduled 180-day rotation
Old user: synpro_old
New user: synpro_new
Status: Success
Downtime: 45 seconds
```

### Rollback Procedure

```bash
# Restore old DATABASE_URL immediately if issues occur
railway variables --environment production --set DATABASE_URL="$OLD_DATABASE_URL"

# Monitor for successful reconnection
railway logs --environment production --service uat-backend
```

### Common Issues

**Issue**: Connection pool exhaustion after rotation
- **Cause**: Old connections not released
- **Solution**: Restart application to force new connection pool

**Issue**: Permission denied errors
- **Cause**: New user missing required permissions
- **Solution**: Grant all necessary permissions (see step 1)

---

## SMTP Credentials Rotation

SMTP credentials are used for sending password reset emails.

### Impact Assessment

- **User Impact**: Low - Only affects password reset emails
- **Downtime**: None
- **Services Affected**: UAT Backend email service
- **Estimated Duration**: 15 minutes

### Prerequisites

- [ ] Access to email service provider (Gmail, SendGrid, etc.)
- [ ] Test email account for validation

### Step-by-Step Procedure

#### 1. Generate New App Password (Gmail Example)

For Gmail:

1. Log in to Google Account: https://myaccount.google.com
2. Navigate to **Security** → **2-Step Verification**
3. Scroll to **App passwords**
4. Click **Generate new app password**
5. Name: `SynPro VDT Production - YYYY-MM-DD`
6. Copy the generated password (16 characters, no spaces)

For other providers:
- **SendGrid**: Generate new API key in dashboard
- **AWS SES**: Create new SMTP credentials in IAM
- **Mailgun**: Generate new SMTP credentials in settings

#### 2. Update Environment Variables (Staging)

```bash
# Update SMTP password in staging
railway variables --environment staging --set SMTP_PASSWORD="YOUR_NEW_APP_PASSWORD"

# If changing email address too:
railway variables --environment staging --set SMTP_USERNAME="new-email@example.com"
railway variables --environment staging --set SMTP_FROM_EMAIL="new-email@example.com"
```

#### 3. Test in Staging

```bash
# Trigger a password reset email
curl -X POST https://staging.example.com/api/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "your-test-email@example.com"}'

# Check your test email inbox for the reset email
```

#### 4. Update Production

```bash
# Update production SMTP credentials
railway variables --environment production --set SMTP_PASSWORD="YOUR_NEW_APP_PASSWORD"
```

#### 5. Verify Production

```bash
# Test password reset flow in production
curl -X POST https://app.example.com/api/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "your-test-email@example.com"}'

# Verify email received successfully
```

#### 6. Revoke Old Credentials

For Gmail:
1. Return to Google Account → **App passwords**
2. Find old password (`SynPro VDT Production - OLD_DATE`)
3. Click **Remove**

#### 7. Document Rotation

```
Date: 2024-XX-XX
Token: SMTP_PASSWORD (Gmail App Password)
Performed by: Security Team
Reason: Scheduled 180-day rotation
Old password: (revoked)
New password: (active)
Status: Success
Test email sent: Yes
```

### Rollback Procedure

```bash
# Restore old SMTP credentials if issues occur
railway variables --environment production --set SMTP_PASSWORD="OLD_APP_PASSWORD"
```

### Common Issues

**Issue**: "Username and Password not accepted" error
- **Cause**: App password may have spaces or typos
- **Solution**: Regenerate and ensure no spaces in password

**Issue**: Emails not being received
- **Cause**: SMTP server blocking or rate limiting
- **Solution**: Check spam folder, verify SMTP_HOST and SMTP_PORT settings

---

## Emergency Rotation

When a credential is compromised or suspected to be compromised, immediate action is required.

### Immediate Actions (Within 1 Hour)

1. **Identify Scope**
   - Which credential(s) are compromised?
   - What systems/services are affected?
   - What data could be accessed?

2. **Contain the Breach**
   ```bash
   # Immediately revoke compromised token (example for Railway)
   railway variables --environment production --set RAILWAY_API_TOKEN="TEMPORARY_SAFE_TOKEN"
   
   # For JWT secret (will force all users to re-authenticate)
   python3 generate_jwt_secret.py
   railway variables --environment production --set JWT_SECRET="NEW_EMERGENCY_SECRET"
   ```

3. **Notify Stakeholders**
   - Send immediate notification to security team
   - Alert affected users if necessary
   - Document incident in security log

4. **Monitor for Abuse**
   ```bash
   # Check logs for unauthorized access
   railway logs --environment production --recent 1000 | grep -i "unauthorized\|forbidden\|403\|401"
   
   # Check for unusual API calls
   railway logs --environment production | grep -i "railway\|deployment"
   ```

### Emergency Rotation Checklist

- [ ] **0-15 minutes**: Identify compromised credential
- [ ] **15-30 minutes**: Generate and deploy new credential
- [ ] **30-45 minutes**: Verify new credential working
- [ ] **45-60 minutes**: Revoke old credential
- [ ] **1-2 hours**: Full system audit and log review
- [ ] **2-4 hours**: Document incident and lessons learned
- [ ] **24 hours**: Review and update security procedures

### Post-Incident Review Template

```markdown
# Security Incident Report: Emergency Token Rotation

**Date**: YYYY-MM-DD
**Incident ID**: INC-YYYYMMDD-XXX
**Severity**: Critical/High/Medium/Low
**Status**: Resolved/Ongoing

## Incident Summary
[Brief description of what happened]

## Timeline
- HH:MM - Discovery
- HH:MM - Initial containment
- HH:MM - Credential rotated
- HH:MM - Verification complete
- HH:MM - Incident resolved

## Compromised Credentials
- JWT_SECRET: [Yes/No]
- RAILWAY_API_TOKEN: [Yes/No]
- DATABASE_URL: [Yes/No]
- SMTP_PASSWORD: [Yes/No]

## Root Cause
[What led to the compromise?]

## Impact Assessment
- Systems affected: [List]
- Data accessed: [Description]
- User impact: [Description]

## Remediation Steps Taken
1. [Action 1]
2. [Action 2]
3. [...]

## Lessons Learned
[What can we improve?]

## Action Items
- [ ] [Action item 1] - Owner: [Name] - Due: [Date]
- [ ] [Action item 2] - Owner: [Name] - Due: [Date]

## Sign-off
Prepared by: [Name]
Reviewed by: [Name]
Approved by: [Name]
Date: YYYY-MM-DD
```

---

## Post-Rotation Validation

After any token rotation, perform these validation steps:

### Automated Validation Script

```bash
#!/bin/bash
# validate_rotation.sh - Post-rotation validation script

set -e

echo "🔍 Validating token rotation..."

# Configuration
API_BASE_URL="${API_BASE_URL:-https://app.example.com}"
TEST_EMAIL="rotation-test@example.com"
TEST_PASSWORD="RotationTest123!@#"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Health check
echo -n "1. Health check... "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/health")
if [ "$HEALTH" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ (HTTP $HEALTH)${NC}"
    exit 1
fi

# Test 2: User registration (JWT validation)
echo -n "2. User registration (JWT)... "
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token // empty')
if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi

# Test 3: Authenticated request
echo -n "3. Authenticated request... "
ME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/auth/me" \
    -H "Authorization: Bearer $TOKEN")
if [ "$ME_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ (HTTP $ME_RESPONSE)${NC}"
    exit 1
fi

# Test 4: Password reset (SMTP validation)
echo -n "4. Password reset email... "
RESET_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/auth/password-reset/request" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\"}")
if [ "$RESET_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ (HTTP $RESET_RESPONSE)${NC}"
    exit 1
fi

# Test 5: Railway API (if token present)
if [ -n "$RAILWAY_API_TOKEN" ]; then
    echo -n "5. Railway API access... "
    RAILWAY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST https://backboard.railway.app/graphql/v2 \
        -H "Authorization: Bearer $RAILWAY_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"query":"{ projects { edges { node { id } } } }"}')
    if [ "$RAILWAY_RESPONSE" = "200" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ (HTTP $RAILWAY_RESPONSE)${NC}"
        exit 1
    fi
else
    echo "5. Railway API access... ${RED}⊘ (token not set)${NC}"
fi

# Cleanup test user
echo -n "6. Cleanup... "
# Note: You may need to add a cleanup endpoint or manually remove test user
echo -e "${GREEN}✓${NC}"

echo ""
echo -e "${GREEN}✓ All validation checks passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Monitor logs for 24 hours: railway logs --environment production"
echo "  2. Check error rate in monitoring dashboard"
echo "  3. Update audit log with rotation details"
echo "  4. Schedule next rotation date in calendar"
```

### Manual Validation Checklist

- [ ] **API Health**: `/api/health` returns 200 OK
- [ ] **User Registration**: Can create new user account
- [ ] **User Login**: Can log in with existing account
- [ ] **JWT Validation**: Authenticated requests work
- [ ] **Token Expiry**: Old tokens are rejected (after JWT rotation)
- [ ] **Password Reset**: Email is received successfully
- [ ] **Railway API**: Deployment operations work (if rotated)
- [ ] **Database**: CRUD operations complete successfully
- [ ] **Logs**: No error spikes in application logs
- [ ] **Monitoring**: No alert triggers post-rotation

### Monitoring Checklist (First 24 Hours)

```bash
# Monitor error rates
railway logs --environment production | grep -i "error\|exception\|failed" | wc -l

# Monitor authentication attempts
railway logs --environment production | grep -i "auth\|login\|token" | tail -n 50

# Monitor database connections
railway logs --environment production | grep -i "database\|postgres\|connection"

# Monitor Railway API calls (if rotated)
railway logs --environment production | grep -i "railway"
```

---

## Rollback Procedures

### General Rollback Principles

1. **Speed over perfection**: Restore service quickly, investigate later
2. **Document the rollback**: Record what was rolled back and why
3. **Analyze the failure**: Understand root cause before re-attempting
4. **Test the fix**: Validate in staging before re-attempting in production

### Quick Rollback Commands

```bash
# Restore any environment variable
railway variables --environment production --set VARIABLE_NAME="OLD_VALUE"

# Verify rollback
railway logs --environment production --service uat-backend | tail -n 20

# Test the service
curl https://app.example.com/api/health
```

### Rollback Decision Matrix

| Symptom | Likely Cause | Rollback Action | Priority |
|---------|--------------|-----------------|----------|
| 500 errors on startup | Invalid secret format | Rollback immediately | P0 |
| 401 errors increasing | Token validation failing | Investigate first, rollback if >10% | P1 |
| Database connection errors | Invalid DATABASE_URL | Rollback immediately | P0 |
| Email not sending | SMTP credentials invalid | Rollback or fix forward | P2 |
| Railway API 401 | Invalid API token | Rollback or generate new | P1 |

### Post-Rollback Actions

1. **Analyze logs** to understand why rotation failed
2. **Test the new credential** in isolation (staging environment)
3. **Review procedure** - was a step missed or incorrect?
4. **Schedule retry** - allow time for investigation and fixes
5. **Update runbook** - document what went wrong and how to prevent

---

## Troubleshooting

### Common Error Messages

#### "JWT_SECRET must be set in production"

**Cause**: JWT_SECRET environment variable is missing or empty

**Solution**:
```bash
# Generate new secret
python3 uat/backend/generate_jwt_secret.py

# Set the variable
railway variables --environment production --set JWT_SECRET="GENERATED_SECRET"
```

#### "Insecure JWT secret detected"

**Cause**: JWT_SECRET doesn't meet security requirements (too short, weak entropy)

**Solution**:
```bash
# Validate current secret
python3 uat/backend/generate_jwt_secret.py --validate "$JWT_SECRET"

# Generate compliant secret
python3 uat/backend/generate_jwt_secret.py --length 64
```

#### "GraphQL errors: Invalid authorization token"

**Cause**: RAILWAY_API_TOKEN is invalid or expired

**Solution**:
1. Check token in Railway dashboard → Account Settings → Tokens
2. Verify token has correct scopes
3. Generate new token if necessary

#### "Connection to database failed"

**Cause**: Invalid DATABASE_URL or network issues

**Solution**:
```bash
# Test database connection
psql "$DATABASE_URL" -c "SELECT 1"

# Verify URL format: postgresql://user:password@host:port/database
echo "$DATABASE_URL" | grep -E "^postgresql://"
```

#### "SMTP authentication failed"

**Cause**: Invalid SMTP credentials

**Solution**:
```bash
# Test SMTP connection (Python)
python3 -c "
import smtplib
import os
smtp = smtplib.SMTP(os.environ['SMTP_HOST'], int(os.environ['SMTP_PORT']))
smtp.starttls()
smtp.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
print('✓ SMTP authentication successful')
"
```

### Debug Mode

Enable debug logging temporarily:

```bash
# Increase log verbosity
railway variables --environment production --set LOG_LEVEL="DEBUG"

# Watch logs in real-time
railway logs --environment production --service uat-backend --follow

# Restore normal logging after debugging
railway variables --environment production --set LOG_LEVEL="INFO"
```

### Contact Information

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Production outage | ops-oncall@example.com | 15 minutes |
| Security incident | security@example.com | 30 minutes |
| Railway API issues | Railway Support | 1-2 hours |
| Database issues | dba@example.com | 1 hour |
| General questions | devops@example.com | 4 hours |

---

## Audit Log Template

Maintain a record of all token rotations in a secure location (e.g., internal wiki, secure git repository).

### CSV Format

```csv
Date,Token Type,Performed By,Reason,Status,Downtime (seconds),Notes
2024-01-15,JWT_SECRET,John Doe,Scheduled 90-day rotation,Success,0,No issues
2024-01-15,RAILWAY_API_TOKEN,Jane Smith,Scheduled 90-day rotation,Success,0,No issues
2024-02-03,JWT_SECRET,Security Team,Emergency - suspected compromise,Success,15,Investigated logs - no breach confirmed
2024-03-20,DATABASE_URL,DevOps,Scheduled 180-day rotation,Success,45,Brief connection interruption
```

### Detailed Entry Template

```markdown
## Token Rotation Log Entry

**Date**: 2024-XX-XX HH:MM UTC
**Token Type**: [JWT_SECRET | RAILWAY_API_TOKEN | DATABASE_URL | SMTP_PASSWORD]
**Environment**: [production | staging | development]
**Performed By**: [Full Name] ([email@example.com])

### Reason
[Scheduled rotation | Security incident | Employee offboarding | Other]

### Procedure Followed
[Standard | Emergency | Custom]

### Timeline
- HH:MM - Rotation initiated
- HH:MM - New credential deployed
- HH:MM - Validation complete
- HH:MM - Old credential revoked (if applicable)
- HH:MM - Incident closed

### Old Credential
- Last 8 characters: ...XXXXXXXX
- Created: YYYY-MM-DD
- Revoked: YYYY-MM-DD HH:MM UTC

### New Credential
- Last 8 characters: ...YYYYYYYY
- Created: YYYY-MM-DD HH:MM UTC
- Expires: YYYY-MM-DD (if applicable)

### Impact
- User impact: [None | Low | Medium | High]
- Downtime: X seconds
- Services affected: [List]
- Errors observed: [None | Description]

### Status
[Success | Rolled back | Failed]

### Issues Encountered
[None | Description of issues]

### Lessons Learned
[What went well, what could be improved]

### Next Rotation Scheduled
YYYY-MM-DD

### Approvals
- Performed by: [Name]
- Reviewed by: [Name]
- Approved by: [Name]
```

### Retention Policy

- **Audit logs**: Retain for 7 years (compliance requirement)
- **Backup credentials**: Delete after 30 days of successful rotation
- **Revoked tokens**: Keep record of revocation date, but not token value

---

## Appendix A: Security Best Practices

1. **Never commit secrets to version control**
   - Use `.env` files (in `.gitignore`)
   - Use environment variables
   - Use secrets management systems (AWS Secrets Manager, HashiCorp Vault, etc.)

2. **Use strong, randomly generated secrets**
   - Minimum 32 characters (64 recommended)
   - High entropy (use `generate_jwt_secret.py`)
   - Unique per environment (dev, staging, production)

3. **Implement rotation schedules**
   - Set calendar reminders
   - Automate where possible
   - Document in audit log

4. **Follow principle of least privilege**
   - Grant minimum required scopes/permissions
   - Review and revoke unused tokens
   - Separate tokens per service/environment

5. **Monitor and alert**
   - Set up alerts for authentication failures
   - Monitor for unusual API usage patterns
   - Log all token rotations

6. **Secure storage**
   - Use secrets management systems in production
   - Encrypt secrets at rest
   - Restrict access to secrets (need-to-know basis)

7. **Incident response**
   - Have emergency rotation procedures ready
   - Practice incident response drills
   - Document all security incidents

---

## Appendix B: Automation Opportunities

Consider automating token rotation with these approaches:

### 1. Automated JWT Rotation (Advanced)

```python
#!/usr/bin/env python3
"""
automated_jwt_rotation.py - Automate JWT secret rotation with zero downtime
Requires support for multiple concurrent JWT secrets (not currently implemented)
"""

import os
import sys
from datetime import datetime, timedelta
from config import generate_jwt_secret

def should_rotate(last_rotation_date: datetime, rotation_days: int = 90) -> bool:
    """Check if rotation is due."""
    next_rotation = last_rotation_date + timedelta(days=rotation_days)
    return datetime.now() >= next_rotation

def rotate_jwt_secret():
    """
    Automated JWT secret rotation.
    
    Strategy:
    1. Generate new secret
    2. Add to list of valid secrets (JWT_SECRET_PRIMARY, JWT_SECRET_SECONDARY)
    3. Start signing with new secret, validating with both
    4. After 24 hours, remove old secret
    """
    # Generate new secret
    new_secret = generate_jwt_secret()
    
    # Get current secrets
    current_primary = os.environ.get("JWT_SECRET_PRIMARY")
    current_secondary = os.environ.get("JWT_SECRET_SECONDARY")
    
    # Promote current primary to secondary, new secret becomes primary
    # This allows validating tokens signed with either secret
    print(f"Rotating JWT secrets...")
    print(f"New primary: {new_secret[-8:]}")
    print(f"New secondary: {current_primary[-8:] if current_primary else 'none'}")
    
    # In production, use Railway API to update variables
    # railway variables --set JWT_SECRET_PRIMARY="$new_secret"
    # railway variables --set JWT_SECRET_SECONDARY="$current_primary"
    
    # Schedule removal of secondary secret after 24 hours
    # (Use cron job, AWS Lambda, or similar)

if __name__ == "__main__":
    # Example: Run daily via cron, only rotates if due
    last_rotation = datetime(2024, 1, 1)  # Read from config
    if should_rotate(last_rotation):
        rotate_jwt_secret()
```

### 2. Railway Variables Automation

```python
#!/usr/bin/env python3
"""
railway_var_manager.py - Manage Railway environment variables programmatically
"""

import subprocess
import json

def get_railway_variables(environment: str = "production") -> dict:
    """Get current Railway variables."""
    result = subprocess.run(
        ["railway", "variables", "--environment", environment, "--json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def set_railway_variable(name: str, value: str, environment: str = "production"):
    """Set a Railway variable."""
    subprocess.run(
        ["railway", "variables", "--environment", environment, "--set", f"{name}={value}"],
        check=True
    )
    print(f"✓ Set {name} in {environment}")

# Usage:
# vars = get_railway_variables("production")
# set_railway_variable("JWT_SECRET", generate_jwt_secret(), "production")
```

### 3. Monitoring and Alerting

```bash
#!/bin/bash
# monitor_token_rotation.sh - Alert when token rotation is due

# Configuration
ROTATION_DAYS=90
ALERT_EMAIL="security@example.com"

# Check last rotation date (read from audit log or config)
LAST_ROTATION=$(date -d "2024-01-01" +%s)
CURRENT_DATE=$(date +%s)
DAYS_SINCE_ROTATION=$(( ($CURRENT_DATE - $LAST_ROTATION) / 86400 ))

if [ $DAYS_SINCE_ROTATION -ge $ROTATION_DAYS ]; then
    echo "⚠️  JWT secret rotation is overdue by $(($DAYS_SINCE_ROTATION - $ROTATION_DAYS)) days"
    
    # Send alert (example with mail command)
    echo "JWT secret rotation is due. Last rotation: $DAYS_SINCE_ROTATION days ago" \
        | mail -s "Action Required: Token Rotation Due" $ALERT_EMAIL
fi
```

---

## Appendix C: Compliance and Audit Requirements

### Regulatory Requirements

Different regulations have different requirements for credential rotation:

| Regulation | Requirement | Our Policy |
|------------|-------------|------------|
| SOC 2 | Regular rotation recommended | 90 days (JWT, Railway) |
| PCI DSS | 90 days minimum | 90 days (critical) |
| HIPAA | Every 90 days recommended | 90-180 days by type |
| GDPR | Regular rotation for encryption keys | 90-180 days |
| ISO 27001 | Documented rotation policy | This runbook |

### Audit Trail Requirements

For compliance audits, ensure you have:

1. **Complete rotation history** (see Audit Log Template)
2. **Evidence of rotation** (change logs, tickets, emails)
3. **Access control records** (who performed rotation)
4. **Incident documentation** (emergency rotations)
5. **Policy documentation** (this runbook)

### Annual Review Checklist

Perform annually:

- [ ] Review rotation schedule - is it still appropriate?
- [ ] Update this runbook with lessons learned
- [ ] Audit all current credentials - are they all documented?
- [ ] Verify monitoring and alerting is working
- [ ] Test emergency rotation procedure
- [ ] Review and update contact information
- [ ] Train new team members on procedures
- [ ] Verify backup and rollback procedures work

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-XX-XX | DevOps Team | Initial version |

---

## Sign-off

**Document Owner**: DevOps / Security Team  
**Last Reviewed**: YYYY-MM-DD  
**Next Review Due**: YYYY-MM-DD  
**Approved By**: [Name, Title]  

---

**End of Runbook**

*For questions or updates to this runbook, contact: devops@example.com*
