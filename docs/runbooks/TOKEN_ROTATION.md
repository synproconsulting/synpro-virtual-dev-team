# Token Rotation Runbook

## Overview

This runbook provides step-by-step procedures for rotating sensitive tokens and secrets used in the PM Agent system. Regular token rotation is a critical security practice that limits the impact of potential credential compromise.

## Table of Contents

1. [JWT Secret Rotation](#jwt-secret-rotation)
2. [Database Credentials Rotation](#database-credentials-rotation)
3. [Railway API Token Rotation](#railway-api-token-rotation)
4. [SMTP Credentials Rotation](#smtp-credentials-rotation)
5. [Jira API Token Rotation](#jira-api-token-rotation)
6. [Emergency Rotation Procedures](#emergency-rotation-procedures)
7. [Rotation Schedule](#rotation-schedule)
8. [Verification & Testing](#verification--testing)
9. [Rollback Procedures](#rollback-procedures)

---

## JWT Secret Rotation

### When to Rotate
- **Scheduled**: Every 90 days
- **Emergency**: Immediately if compromised or suspected compromise
- **After**: Security incidents, employee departures with system access

### Impact Assessment
- **User Impact**: All active user sessions will be invalidated
- **Downtime**: None (zero-downtime rotation possible)
- **Rollback Window**: 24 hours recommended

### Prerequisites
- [ ] Access to production environment variables
- [ ] Access to staging environment for testing
- [ ] Communication plan for user notification
- [ ] Backup of current JWT_SECRET value

### Procedure

#### Phase 1: Preparation (T-24h)

1. **Generate New JWT Secret**
   ```bash
   cd scripts
   python generate_secrets.py --type jwt
   ```
   
   Or manually:
   ```bash
   python -c "from uat.backend.config import generate_jwt_secret; print(generate_jwt_secret())"
   ```

2. **Store New Secret Securely**
   - Save to password manager (1Password, LastPass, etc.)
   - Mark with rotation date and purpose
   - Share with authorized team members only

3. **Test in Staging**
   ```bash
   # Update staging environment
   export JWT_SECRET="<new-secret>"
   
   # Restart staging services
   ./scripts/rotate_token.py --env staging --token-type jwt --validate
   ```

4. **Notify Users**
   - Send email notification 24h before rotation
   - Inform users they'll need to re-login
   - Provide exact rotation time window

#### Phase 2: Rotation (T=0)

1. **Update Production Environment Variable**
   
   **Railway/Kubernetes:**
   ```bash
   # Using Railway CLI
   railway variables set JWT_SECRET="<new-secret>" -e production
   
   # Or using kubectl
   kubectl create secret generic jwt-secret \
     --from-literal=JWT_SECRET="<new-secret>" \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

2. **Perform Zero-Downtime Rotation**
   ```bash
   # Deploy with new secret (rolling restart)
   ./scripts/rotate_token.py --env production --token-type jwt --execute --zero-downtime
   ```

3. **Monitor Service Health**
   ```bash
   # Check service status
   ./scripts/health_check.py --service backend --timeout 300
   
   # Monitor logs for errors
   railway logs -e production --tail 100
   ```

4. **Verify Token Generation**
   ```bash
   # Test token issuance
   curl -X POST https://api.yourapp.com/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test@example.com","password":"test123"}'
   
   # Verify token with new secret
   ./scripts/verify_jwt.py --token "<jwt-token>" --env production
   ```

#### Phase 3: Validation (T+30min)

1. **User Session Testing**
   - [ ] New logins work correctly
   - [ ] Old tokens are rejected with 401 Unauthorized
   - [ ] Token refresh endpoint works
   - [ ] Protected endpoints validate new tokens

2. **Monitor Error Rates**
   ```bash
   # Check error logs
   grep "JWT" /var/log/backend/*.log | grep -i "error\|invalid"
   
   # Or via logging service
   railway logs -e production | grep "JWT.*error"
   ```

3. **Database Verification**
   ```bash
   # Check for authentication errors in DB logs
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM auth_logs WHERE error_type = 'jwt_invalid' AND created_at > NOW() - INTERVAL '1 hour';"
   ```

#### Phase 4: Cleanup (T+24h)

1. **Archive Old Secret**
   ```bash
   # Move old secret to secure archive
   ./scripts/archive_secret.py --type jwt --secret "<old-secret>" --rotation-date "$(date -I)"
   ```

2. **Update Documentation**
   - [ ] Record rotation date in security log
   - [ ] Update last rotation date in this runbook
   - [ ] Schedule next rotation (90 days)

3. **Remove Old Secret from Active Storage**
   - Remove from Railway variables history (if possible)
   - Mark as revoked in password manager
   - Update team documentation

### Validation Checklist

After rotation, verify:
- [ ] New users can register and receive valid tokens
- [ ] Existing users can log in with new tokens
- [ ] API endpoints accept new tokens
- [ ] Old tokens are properly rejected
- [ ] Token expiry times are correct
- [ ] No JWT-related errors in logs
- [ ] Session management works correctly

### Rollback Procedure

If issues occur within the rollback window:

1. **Immediate Rollback**
   ```bash
   # Restore old JWT secret
   railway variables set JWT_SECRET="<old-secret>" -e production
   
   # Or using script
   ./scripts/rotate_token.py --env production --token-type jwt --rollback
   ```

2. **Restart Services**
   ```bash
   railway up -e production --restart
   ```

3. **Verify Rollback**
   - Test with recently issued tokens
   - Check user login functionality
   - Monitor error logs

4. **Post-Mortem**
   - Document what went wrong
   - Update runbook with lessons learned
   - Plan retry with fixes

---

## Database Credentials Rotation

### When to Rotate
- **Scheduled**: Every 180 days
- **Emergency**: Immediately if compromised
- **After**: Staff changes, security audits

### Impact Assessment
- **User Impact**: Potential 2-5 minute service interruption
- **Downtime**: Brief connection loss during credential switchover
- **Rollback Window**: 1 hour

### Prerequisites
- [ ] Database admin access
- [ ] Access to all services using the database
- [ ] Backup of current database
- [ ] Maintenance window scheduled

### Procedure

#### Phase 1: Preparation

1. **Create New Database User/Password**
   ```sql
   -- Connect to database as admin
   psql $DATABASE_URL
   
   -- Create new user with same privileges
   CREATE USER pm_agent_new WITH PASSWORD '<new-secure-password>';
   
   -- Grant same permissions as old user
   GRANT CONNECT ON DATABASE pm_agent_db TO pm_agent_new;
   GRANT USAGE ON SCHEMA public TO pm_agent_new;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pm_agent_new;
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pm_agent_new;
   
   -- Grant default privileges for future tables
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pm_agent_new;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO pm_agent_new;
   ```

2. **Test New Credentials in Staging**
   ```bash
   # Build new connection string
   NEW_DB_URL="postgresql://pm_agent_new:<new-password>@host:5432/pm_agent_db"
   
   # Test connection
   psql "$NEW_DB_URL" -c "SELECT 1;"
   
   # Run application tests with new credentials
   export DATABASE_URL="$NEW_DB_URL"
   pytest uat/backend/tests/
   ```

3. **Generate Secret Rotation Script**
   ```bash
   ./scripts/rotate_token.py --env production --token-type database --dry-run
   ```

#### Phase 2: Rotation

1. **Enable Maintenance Mode (Optional)**
   ```bash
   # Put service in read-only mode
   railway variables set MAINTENANCE_MODE="true" -e production
   ```

2. **Update DATABASE_URL Environment Variable**
   ```bash
   # Update all services that use the database
   railway variables set DATABASE_URL="$NEW_DB_URL" -e production
   ```

3. **Rolling Restart Services**
   ```bash
   # Restart backend services one by one
   kubectl rollout restart deployment/pm-agent-backend
   kubectl rollout status deployment/pm-agent-backend --timeout=300s
   ```

4. **Disable Maintenance Mode**
   ```bash
   railway variables unset MAINTENANCE_MODE -e production
   ```

#### Phase 3: Validation

1. **Test Database Connectivity**
   ```bash
   # Test read operations
   curl https://api.yourapp.com/health/db
   
   # Test write operations (create a test record)
   ./scripts/db_health_check.py --env production --test-writes
   ```

2. **Monitor Connection Pool**
   ```sql
   -- Check active connections
   SELECT 
     usename,
     application_name,
     client_addr,
     state,
     COUNT(*) 
   FROM pg_stat_activity 
   WHERE datname = 'pm_agent_db'
   GROUP BY usename, application_name, client_addr, state;
   ```

3. **Verify No Old Connections**
   ```sql
   -- Should return 0 rows
   SELECT COUNT(*) FROM pg_stat_activity 
   WHERE usename = 'pm_agent_old' AND datname = 'pm_agent_db';
   ```

#### Phase 4: Cleanup (T+1h)

1. **Revoke Old User Access**
   ```sql
   -- Remove all privileges from old user
   REVOKE ALL PRIVILEGES ON DATABASE pm_agent_db FROM pm_agent_old;
   REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM pm_agent_old;
   REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM pm_agent_old;
   
   -- Optionally drop the old user (after verifying new user works)
   -- DROP USER pm_agent_old;  -- Wait 24h before executing this
   ```

2. **Archive Old Credentials**
   ```bash
   ./scripts/archive_secret.py --type database --secret "$OLD_DB_PASSWORD"
   ```

### Rollback Procedure

```bash
# Restore old DATABASE_URL
railway variables set DATABASE_URL="<old-database-url>" -e production

# Restart services
railway up -e production --restart

# Verify old credentials work
./scripts/db_health_check.py --env production
```

---

## Railway API Token Rotation

### When to Rotate
- **Scheduled**: Every 60 days
- **Emergency**: Immediately if exposed in logs, code, or public repositories
- **After**: CI/CD compromise, unauthorized access

### Impact Assessment
- **User Impact**: None (internal token only)
- **Downtime**: None
- **Affected Services**: Deployment automation, orchestrator agents

### Prerequisites
- [ ] Railway account access
- [ ] Access to CI/CD environment variables
- [ ] List of all services using Railway token

### Procedure

1. **Generate New Railway Token**
   - Go to https://railway.app/account/tokens
   - Click "Create Token"
   - Name: `PM-Agent-Production-<date>`
   - Scope: Select only required projects
   - Copy token immediately (shown only once)

2. **Update Environment Variables**
   ```bash
   # Update in CI/CD (GitHub Actions)
   gh secret set RAILWAY_API_TOKEN --body "<new-token>"
   
   # Update in local development environments
   # Notify team to update their .env files
   ```

3. **Update Application Configuration**
   ```bash
   # If Railway token is used at runtime (not just deployment)
   railway variables set RAILWAY_API_TOKEN="<new-token>" -e production
   ```

4. **Test Automation**
   ```bash
   # Test deployment script
   ./scripts/deploy.py --env staging --dry-run
   
   # Test orchestrator agent if it uses Railway API
   pytest agents/tests/test_railway_integration.py
   ```

5. **Revoke Old Token**
   - Go to https://railway.app/account/tokens
   - Find old token
   - Click "Revoke"
   - Confirm revocation

6. **Monitor for Errors**
   ```bash
   # Check for 401 Unauthorized errors in logs
   railway logs -e production | grep "401\|unauthorized"
   ```

### Validation
- [ ] Automated deployments work
- [ ] No 401 errors in Railway API calls
- [ ] Old token is revoked and non-functional

---

## SMTP Credentials Rotation

### When to Rotate
- **Scheduled**: Every 180 days
- **Emergency**: If email bounce rate increases unexpectedly
- **After**: Email provider compromise, phishing campaigns

### Prerequisites
- [ ] Email provider admin access (Gmail, SendGrid, etc.)
- [ ] Access to update SMTP configuration
- [ ] Test email recipient addresses

### Procedure

1. **Generate New SMTP Credentials**
   
   **Gmail App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other" → "PM Agent Backend"
   - Click "Generate"
   - Copy 16-character password
   
   **SendGrid:**
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Name: `pm-agent-smtp-<date>`
   - Permissions: "Mail Send" only
   - Copy API key

2. **Update Environment Variables**
   ```bash
   railway variables set SMTP_PASSWORD="<new-password>" -e production
   railway variables set SMTP_USERNAME="<username>" -e production  # if changed
   ```

3. **Test Email Sending**
   ```bash
   # Send test email
   ./scripts/test_smtp.py --env production --recipient "test@yourcompany.com"
   ```

4. **Verify Email Delivery**
   - Check test email inbox
   - Verify DKIM/SPF signatures
   - Check spam score

5. **Revoke Old Credentials**
   - Delete old app password or API key from provider

6. **Monitor Email Metrics**
   ```bash
   # Check email logs for failures
   grep "smtp" /var/log/backend/*.log | grep -i "error\|fail"
   ```

### Validation
- [ ] Password reset emails are delivered
- [ ] Welcome emails are delivered
- [ ] No emails in spam folder
- [ ] Bounce rate is normal (<2%)
- [ ] No SMTP authentication errors in logs

---

## Jira API Token Rotation

### When to Rotate
- **Scheduled**: Every 90 days
- **Emergency**: If token appears in logs or unauthorized Jira activity detected
- **After**: Team member with Jira access leaves

### Prerequisites
- [ ] Jira admin or service account access
- [ ] Access to services that use Jira API
- [ ] List of Jira projects used by PM Agent

### Procedure

1. **Generate New Jira API Token**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Label: `PM-Agent-Production-<YYYY-MM-DD>`
   - Copy token (shown only once)

2. **Update Environment Variables**
   ```bash
   # Update Jira token
   railway variables set JIRA_API_TOKEN="<new-token>" -e production
   
   # If using email/token combo
   railway variables set JIRA_EMAIL="<jira-service-account-email>" -e production
   ```

3. **Test Jira Integration**
   ```bash
   # Test Jira API access
   ./scripts/test_jira_connection.py --env production
   
   # Test PM Agent Jira operations
   pytest agents/tests/test_pm_agent.py -k jira
   ```

4. **Revoke Old Token**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Find old token (by label)
   - Click "Revoke"
   - Confirm

5. **Monitor Jira API Usage**
   ```bash
   # Check for API errors
   railway logs -e production | grep -i "jira.*error\|jira.*401"
   ```

### Validation
- [ ] PM Agent can read Jira issues
- [ ] PM Agent can create/update issues
- [ ] No 401/403 errors in Jira API calls
- [ ] Jira webhooks still work (if configured)
- [ ] Custom fields (execution_order, story_points) are accessible

---

## Emergency Rotation Procedures

### Indicators for Emergency Rotation

Execute emergency rotation immediately if:
- Token appears in public repository
- Token appears in application logs
- Suspicious activity detected using the token
- Security breach or unauthorized access
- Token accidentally shared via insecure channel (Slack, email)

### Emergency Response Steps

1. **Immediate Actions (0-15 minutes)**
   ```bash
   # Revoke compromised token immediately
   ./scripts/rotate_token.py --env production --token-type <type> --emergency
   
   # Enable additional monitoring
   ./scripts/enable_security_monitoring.py --mode enhanced
   ```

2. **Impact Assessment (15-30 minutes)**
   - Review audit logs for unauthorized access
   - Identify affected systems and data
   - Determine scope of potential compromise
   
   ```bash
   # Check recent API calls with compromised token
   ./scripts/audit_token_usage.py --token-id <id> --hours 72
   ```

3. **Communication (30-60 minutes)**
   - Notify security team
   - Notify affected users if data was accessed
   - File incident report

4. **Full Rotation (1-4 hours)**
   - Follow standard rotation procedures for affected token
   - Rotate any related tokens as a precaution
   - Update all systems using the token

5. **Post-Incident (24-48 hours)**
   - Complete incident report
   - Implement preventive measures
   - Update security policies
   - Train team on lessons learned

### Emergency Contact Information

```
Security Team Lead: security@yourcompany.com
On-Call Engineer: oncall@yourcompany.com
Incident Hotline: +1-XXX-XXX-XXXX
```

---

## Rotation Schedule

### Recommended Rotation Frequencies

| Token/Secret Type | Rotation Frequency | Last Rotated | Next Rotation |
|-------------------|-------------------|--------------|---------------|
| JWT Secret | 90 days | YYYY-MM-DD | YYYY-MM-DD |
| Database Password | 180 days | YYYY-MM-DD | YYYY-MM-DD |
| Railway API Token | 60 days | YYYY-MM-DD | YYYY-MM-DD |
| SMTP Credentials | 180 days | YYYY-MM-DD | YYYY-MM-DD |
| Jira API Token | 90 days | YYYY-MM-DD | YYYY-MM-DD |

### Automation

Set up automated reminders:

```bash
# Add to crontab for monthly rotation check
0 9 1 * * /path/to/scripts/check_rotation_schedule.py --notify
```

Or use calendar reminders:
- Create recurring calendar events
- Set reminders 7 days before rotation due
- Include runbook link in calendar event

---

## Verification & Testing

### Pre-Rotation Testing Checklist

Before rotating any token in production:

- [ ] Test new token in staging environment
- [ ] Verify all services can access resources with new token
- [ ] Run automated test suite with new token
- [ ] Test rollback procedure in staging
- [ ] Verify monitoring and alerting works

### Post-Rotation Validation

After rotating any token:

```bash
# Run comprehensive health check
./scripts/health_check.py --comprehensive --env production

# Run smoke tests
pytest uat/backend/tests/smoke/ -v

# Check service metrics
./scripts/check_metrics.py --window 1h --compare-baseline
```

### Monitoring During Rotation

```bash
# Start real-time monitoring
./scripts/monitor_rotation.py --token-type <type> --duration 30m

# Monitor key metrics:
# - Error rate
# - Response time
# - Active connections
# - Authentication failures
```

---

## Rollback Procedures

### General Rollback Steps

1. **Detect Issue**
   - Monitor error rates during rotation
   - Set alert thresholds for automatic detection

2. **Decide to Rollback**
   - Error rate > 5% increase
   - Critical functionality broken
   - Data integrity concerns

3. **Execute Rollback**
   ```bash
   # Use rollback script
   ./scripts/rotate_token.py --token-type <type> --rollback
   
   # Or manual rollback
   railway variables set <TOKEN_NAME>="<old-value>" -e production
   railway up -e production --restart
   ```

4. **Verify Rollback Success**
   ```bash
   # Check error rates return to normal
   ./scripts/check_metrics.py --window 15m
   
   # Test critical functionality
   ./scripts/smoke_test.py --env production
   ```

5. **Post-Mortem**
   - Document what went wrong
   - Identify root cause
   - Update runbook
   - Plan retry with fixes

### Rollback Window Guidelines

| Token Type | Max Rollback Window |
|-----------|-------------------|
| JWT Secret | 24 hours |
| Database Password | 1 hour |
| Railway API Token | 7 days |
| SMTP Credentials | 7 days |
| Jira API Token | 7 days |

---

## Troubleshooting

### Common Issues

#### Issue: Services can't connect after rotation

**Symptoms:** 401 Unauthorized, connection refused errors

**Solution:**
```bash
# Verify environment variable was updated
railway variables --env production | grep <TOKEN_NAME>

# Check service has restarted and picked up new variable
kubectl get pods -o wide
kubectl logs <pod-name> | tail -50

# Force restart if needed
railway up -e production --restart
```

#### Issue: Old tokens still work after rotation

**Symptoms:** Old credentials not properly revoked

**Solution:**
```bash
# Verify old token was revoked at source
# For JWT: Old tokens will remain valid until they expire
# For API tokens: Check provider dashboard

# Force immediate revocation (JWT)
# Add old JWT secret to revocation list
./scripts/revoke_jwt_secrets.py --secret "<old-secret>"
```

#### Issue: Token rotation script fails

**Symptoms:** Script exits with error, partial rotation

**Solution:**
```bash
# Check script logs
cat logs/rotation-<timestamp>.log

# Verify prerequisites
./scripts/rotate_token.py --token-type <type> --check-prerequisites

# Manual rotation if automation fails
# Follow manual procedure in this runbook
```

---

## Appendix

### A. Token Generation Commands

```bash
# JWT Secret (64 bytes, base64)
python -c "from uat.backend.config import generate_jwt_secret; print(generate_jwt_secret())"

# Or using secrets module
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Database Password (32 characters, alphanumeric + symbols)
python -c "import secrets, string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(32)))"

# Generic secure random string
openssl rand -base64 48
```

### B. Security Best Practices

1. **Never commit secrets to version control**
   - Use `.env` files (in `.gitignore`)
   - Use environment variables
   - Use secret management services (Vault, AWS Secrets Manager)

2. **Use unique tokens for each environment**
   - Development tokens != Staging tokens != Production tokens
   - Separate tokens for separate purposes

3. **Implement least privilege**
   - Grant only necessary permissions
   - Use service-specific tokens when possible

4. **Monitor token usage**
   - Log all token authentications
   - Alert on unusual patterns
   - Regular audit reviews

5. **Secure token storage**
   - Encrypt tokens at rest
   - Use secure password managers
   - Never share tokens via insecure channels

### C. Related Documentation

- [Security Policies](./SECURITY.md)
- [Incident Response Plan](./INCIDENT_RESPONSE.md)
- [Access Control Procedures](./ACCESS_CONTROL.md)
- [Backup and Recovery](./BACKUP_RECOVERY.md)

### D. Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-XX | 1.0 | Initial runbook creation | Team |

---

## Questions or Issues?

If you encounter problems not covered in this runbook:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review recent rotation logs: `logs/rotation-*.log`
3. Contact the security team: security@yourcompany.com
4. For emergencies: Call the incident hotline

**Remember:** When in doubt, prioritize security over convenience. It's better to rotate a token unnecessarily than to leave a compromised token active.
