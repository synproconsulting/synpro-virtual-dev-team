# Token Rotation Runbook

## Overview

This runbook provides step-by-step procedures for rotating authentication tokens, API keys, and secrets used across the SDT1 platform. Regular token rotation is a critical security practice that helps minimize the impact of potential credential compromise.

## Table of Contents

1. [General Principles](#general-principles)
2. [Pre-Rotation Checklist](#pre-rotation-checklist)
3. [Jira API Token Rotation](#jira-api-token-rotation)
4. [OpenAI API Key Rotation](#openai-api-key-rotation)
5. [Database Credentials Rotation](#database-credentials-rotation)
6. [GitHub Token Rotation](#github-token-rotation)
7. [Service-to-Service Tokens](#service-to-service-tokens)
8. [Post-Rotation Verification](#post-rotation-verification)
9. [Emergency Rotation Procedure](#emergency-rotation-procedure)
10. [Troubleshooting](#troubleshooting)

---

## General Principles

### Rotation Schedule
- **High-Risk Tokens** (GitHub, Jira Admin): Every 30 days
- **API Keys** (OpenAI, external services): Every 60 days
- **Database Credentials**: Every 90 days
- **Service Tokens**: Every 30 days
- **Emergency**: Immediately upon suspected compromise

### Best Practices
1. Always create the new token before revoking the old one
2. Test the new token in a non-production environment first
3. Monitor error logs during and after rotation
4. Keep a secure backup of the previous token for 24 hours for rollback
5. Document the rotation in the security audit log
6. Coordinate with the team during business hours when possible

---

## Pre-Rotation Checklist

Before rotating any token, complete this checklist:

- [ ] Notify team in #engineering channel with planned rotation time
- [ ] Confirm backup and rollback procedures are in place
- [ ] Identify all services that use the token
- [ ] Have access to all environments where token is deployed
- [ ] Set up monitoring for increased error rates
- [ ] Schedule rotation during low-traffic period if possible
- [ ] Have incident response contact list ready

---

## Jira API Token Rotation

### Services Affected
- PM Agent
- Orchestrator
- UAT Service
- Control Centre (indirect)

### Prerequisites
- Jira admin access or access to service account
- Access to environment variable management for all services
- kubectl access (for Kubernetes deployments)

### Procedure

#### 1. Generate New Token

```bash
# Navigate to Jira API token management
# URL: https://id.atlassian.com/manage-profile/security/api-tokens
# 1. Click "Create API token"
# 2. Label: "SDT1-Production-[YYYY-MM-DD]"
# 3. Copy the token immediately (it's shown only once)
```

#### 2. Test New Token

```bash
# Test the new token with a simple API call
curl -X GET \
  -H "Authorization: Basic $(echo -n 'email@domain.com:NEW_TOKEN' | base64)" \
  -H "Content-Type: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/myself"

# Expected: 200 OK with user details
```

#### 3. Update Environment Variables

**For Docker/Docker Compose:**
```bash
# Update .env file or environment-specific config
JIRA_API_TOKEN=new_token_here

# Restart services
docker-compose restart pm-agent orchestrator uat-backend
```

**For Kubernetes:**
```bash
# Update secret
kubectl create secret generic jira-api-token \
  --from-literal=token='new_token_here' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployments to pick up new secret
kubectl rollout restart deployment/pm-agent
kubectl rollout restart deployment/orchestrator
kubectl rollout restart deployment/uat-backend

# Monitor rollout
kubectl rollout status deployment/pm-agent
kubectl rollout status deployment/orchestrator
kubectl rollout status deployment/uat-backend
```

**For Environment Variable Services:**
```bash
# If using a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault)
# Update via secrets manager CLI or console

# AWS Secrets Manager example:
aws secretsmanager update-secret \
  --secret-id sdt1/production/jira-api-token \
  --secret-string 'new_token_here'
```

#### 4. Verify Services

```bash
# Check PM Agent
curl http://pm-agent:8000/health
# Check logs for Jira API calls
kubectl logs -f deployment/pm-agent --tail=50

# Check Orchestrator
curl http://orchestrator:8001/health
kubectl logs -f deployment/orchestrator --tail=50

# Check UAT Service
curl http://uat-backend:8002/health
kubectl logs -f deployment/uat-backend --tail=50
```

#### 5. Monitor for Errors

```bash
# Watch for authentication errors (15-minute window)
kubectl logs -f deployment/pm-agent | grep -i "auth\|401\|403"
kubectl logs -f deployment/orchestrator | grep -i "auth\|401\|403"
kubectl logs -f deployment/uat-backend | grep -i "auth\|401\|403"
```

#### 6. Revoke Old Token

```bash
# After 24 hours of successful operation:
# 1. Navigate to https://id.atlassian.com/manage-profile/security/api-tokens
# 2. Find the old token (by label/date)
# 3. Click "Revoke"
# 4. Confirm revocation
```

#### Rollback Procedure

If issues occur:
```bash
# Revert to old token
kubectl create secret generic jira-api-token \
  --from-literal=token='old_token_here' \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/pm-agent deployment/orchestrator deployment/uat-backend
```

---

## OpenAI API Key Rotation

### Services Affected
- PM Agent
- Orchestrator
- Any custom agent services

### Prerequisites
- OpenAI organization admin access
- Access to billing dashboard (to verify usage)

### Procedure

#### 1. Generate New Key

```bash
# Navigate to OpenAI API Keys page
# URL: https://platform.openai.com/api-keys
# 1. Click "Create new secret key"
# 2. Name: "SDT1-Production-[YYYY-MM-DD]"
# 3. Set permissions: Restrict to specific projects if available
# 4. Copy the key immediately
```

#### 2. Test New Key

```bash
# Test with a simple API call
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer NEW_API_KEY"

# Expected: 200 OK with list of models
```

#### 3. Update Environment Variables

**For Docker/Docker Compose:**
```bash
# Update .env file
OPENAI_API_KEY=new_key_here

# Restart services
docker-compose restart pm-agent orchestrator
```

**For Kubernetes:**
```bash
# Update secret
kubectl create secret generic openai-api-key \
  --from-literal=key='new_key_here' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployments
kubectl rollout restart deployment/pm-agent deployment/orchestrator

# Monitor rollout
kubectl rollout status deployment/pm-agent
kubectl rollout status deployment/orchestrator
```

#### 4. Verify API Calls

```bash
# Monitor logs for successful OpenAI API calls
kubectl logs -f deployment/pm-agent | grep -i "openai\|gpt"

# Test a simple operation that uses OpenAI
# (e.g., trigger PM Agent to analyze a ticket)
```

#### 5. Monitor Usage Dashboard

```bash
# Check OpenAI usage dashboard for:
# - API calls from new key
# - No errors related to authentication
# - Expected usage patterns

# URL: https://platform.openai.com/usage
```

#### 6. Revoke Old Key

```bash
# After 24 hours of successful operation:
# 1. Navigate to https://platform.openai.com/api-keys
# 2. Find the old key by name/date
# 3. Click "Delete" or "Revoke"
# 4. Confirm deletion
```

---

## Database Credentials Rotation

### Services Affected
- UAT Backend
- Any service with direct database access

### Prerequisites
- Database admin access
- Downtime window (or blue-green deployment capability)
- Database backup completed and verified

### Procedure

#### 1. Create New Database User

```sql
-- For PostgreSQL
CREATE USER sdt1_app_new WITH PASSWORD 'strong_random_password_here';

-- Grant necessary permissions (match existing user)
GRANT CONNECT ON DATABASE sdt1_production TO sdt1_app_new;
GRANT USAGE ON SCHEMA public TO sdt1_app_new;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sdt1_app_new;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sdt1_app_new;

-- For future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sdt1_app_new;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
  GRANT USAGE, SELECT ON SEQUENCES TO sdt1_app_new;
```

#### 2. Test New Credentials

```bash
# Test connection with new credentials
psql "postgresql://sdt1_app_new:new_password@db-host:5432/sdt1_production" -c "SELECT 1;"

# Expected: Should return 1
```

#### 3. Update Application Configuration

**For Docker/Docker Compose:**
```bash
# Update .env file
DATABASE_URL=postgresql://sdt1_app_new:new_password@db-host:5432/sdt1_production

# Or individual variables
DB_USER=sdt1_app_new
DB_PASSWORD=new_password

# Restart services
docker-compose restart uat-backend
```

**For Kubernetes:**
```bash
# Update secret
kubectl create secret generic db-credentials \
  --from-literal=username='sdt1_app_new' \
  --from-literal=password='new_password' \
  --from-literal=url='postgresql://sdt1_app_new:new_password@db-host:5432/sdt1_production' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployments
kubectl rollout restart deployment/uat-backend

# Monitor rollout
kubectl rollout status deployment/uat-backend
```

#### 4. Verify Database Operations

```bash
# Check application health
curl http://uat-backend:8002/health

# Check logs for database operations
kubectl logs -f deployment/uat-backend | grep -i "database\|sql\|postgres"

# Verify read operations work
# Verify write operations work (create/update test records)
```

#### 5. Monitor for 24 Hours

```bash
# Monitor for any connection errors
kubectl logs deployment/uat-backend --since=1h | grep -i "connection\|auth\|error"

# Check database connection pool status
# Check for any denied permission errors
```

#### 6. Remove Old User

```sql
-- After 24 hours of successful operation:
-- First, check for any active connections from old user
SELECT pid, usename, application_name, client_addr 
FROM pg_stat_activity 
WHERE usename = 'sdt1_app_old';

-- If no active connections, drop the user
DROP USER sdt1_app_old;
```

---

## GitHub Token Rotation

### Services Affected
- Orchestrator (for creating PRs)
- Any CI/CD pipelines
- Automation scripts

### Prerequisites
- GitHub organization admin or personal account access
- Access to all services using the token

### Procedure

#### 1. Generate New Token

```bash
# Navigate to GitHub Settings > Developer settings > Personal access tokens
# URL: https://github.com/settings/tokens
# 
# For Classic Token:
# 1. Click "Generate new token (classic)"
# 2. Note: "SDT1-Production-[YYYY-MM-DD]"
# 3. Select scopes:
#    - repo (full control)
#    - workflow (if needed for GitHub Actions)
# 4. Set expiration: 90 days
# 5. Generate and copy token
#
# For Fine-grained Token (preferred):
# 1. Click "Generate new token"
# 2. Token name: "SDT1-Production-[YYYY-MM-DD]"
# 3. Repository access: Select specific repositories
# 4. Permissions:
#    - Contents: Read and write
#    - Pull requests: Read and write
#    - Metadata: Read-only (automatically included)
# 5. Generate and copy token
```

#### 2. Test New Token

```bash
# Test with GitHub API
curl -H "Authorization: Bearer NEW_TOKEN" \
  https://api.github.com/user

# Expected: 200 OK with user details

# Test repository access
curl -H "Authorization: Bearer NEW_TOKEN" \
  https://api.github.com/repos/your-org/your-repo

# Expected: 200 OK with repo details
```

#### 3. Update Environment Variables

**For Docker/Docker Compose:**
```bash
# Update .env file
GITHUB_TOKEN=new_token_here

# Restart services
docker-compose restart orchestrator
```

**For Kubernetes:**
```bash
# Update secret
kubectl create secret generic github-token \
  --from-literal=token='new_token_here' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployments
kubectl rollout restart deployment/orchestrator

# Monitor rollout
kubectl rollout status deployment/orchestrator
```

**For GitHub Actions:**
```bash
# Update repository secret
# Navigate to: Settings > Secrets and variables > Actions
# Update or create: GITHUB_TOKEN
# Value: new_token_here
```

#### 4. Verify GitHub Operations

```bash
# Test PR creation (if that's the primary use)
# Trigger a workflow that creates a PR
# Monitor orchestrator logs
kubectl logs -f deployment/orchestrator | grep -i "github\|pull request"

# Verify the PR was created successfully
```

#### 5. Revoke Old Token

```bash
# After 24 hours of successful operation:
# 1. Navigate to https://github.com/settings/tokens
# 2. Find the old token by name/date
# 3. Click "Delete"
# 4. Confirm deletion
```

---

## Service-to-Service Tokens

### Services Affected
- Internal API authentication between microservices
- Webhook signatures

### Prerequisites
- Access to both services (client and server)
- Understanding of token format (JWT, symmetric key, etc.)

### Procedure

#### 1. Generate New Token/Secret

**For JWT-based authentication:**
```bash
# Generate new signing key
openssl rand -base64 32 > jwt_secret.txt

# Read the generated secret
NEW_JWT_SECRET=$(cat jwt_secret.txt)
```

**For symmetric API keys:**
```bash
# Generate random API key
NEW_API_KEY=$(openssl rand -hex 32)
echo $NEW_API_KEY
```

#### 2. Update Server-Side First

```bash
# Update the service that validates tokens (server)
# Support BOTH old and new tokens during transition

# Example environment variables:
JWT_SECRET_PRIMARY=new_secret_here
JWT_SECRET_SECONDARY=old_secret_here  # For backward compatibility

# Update and restart server service
kubectl create secret generic service-auth \
  --from-literal=jwt_secret_primary='new_secret' \
  --from-literal=jwt_secret_secondary='old_secret' \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/server-service
kubectl rollout status deployment/server-service
```

#### 3. Update Client-Side

```bash
# Update services that generate tokens (clients)
# Now using the new secret

JWT_SECRET=new_secret_here

kubectl create secret generic client-auth \
  --from-literal=jwt_secret='new_secret' \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/client-service
kubectl rollout status deployment/client-service
```

#### 4. Verify Service Communication

```bash
# Check client logs for successful authentication
kubectl logs -f deployment/client-service | grep -i "auth\|token"

# Check server logs for accepted tokens
kubectl logs -f deployment/server-service | grep -i "auth\|token\|401\|403"

# Test API call from client to server
# Verify 200 OK responses
```

#### 5. Remove Old Secret from Server

```bash
# After 24 hours, remove backward compatibility
kubectl create secret generic service-auth \
  --from-literal=jwt_secret='new_secret' \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/server-service
```

---

## Post-Rotation Verification

After any token rotation, complete these verification steps:

### Immediate Checks (0-2 hours)

```bash
# 1. Health checks pass
curl http://service:port/health
# Expected: 200 OK

# 2. No authentication errors in logs
kubectl logs deployment/service-name --since=1h | grep -i "401\|403\|auth.*error"
# Expected: No results

# 3. Services can communicate
# Test actual operations, not just health checks

# 4. Monitor error rates
# Check your monitoring dashboard (Grafana, CloudWatch, etc.)
# Look for spikes in 4xx/5xx errors
```

### Extended Monitoring (24 hours)

- [ ] No increase in error rates
- [ ] No authentication failures
- [ ] All scheduled jobs completed successfully
- [ ] All integrations working (Jira, GitHub, OpenAI)
- [ ] No reports of issues from team members
- [ ] Monitoring alerts clear

### Security Audit Log

Document the rotation:

```bash
# Create audit log entry
cat >> docs/security-audit-log.md << EOF

## Token Rotation - $(date +%Y-%m-%d)

**Token Type:** [Jira API Token / OpenAI API Key / etc.]
**Rotated By:** [Your Name]
**Services Updated:** 
  - Service 1
  - Service 2
  - Service 3

**Pre-Rotation Testing:** ✓ Completed
**Rollout:** ✓ Successful
**Post-Rotation Verification:** ✓ Passed
**Old Token Revoked:** ✓ After 24 hours
**Issues Encountered:** None / [Description if any]

EOF
```

---

## Emergency Rotation Procedure

Use this procedure when a token has been compromised or accidentally exposed.

### Immediate Actions (0-15 minutes)

1. **Revoke Compromised Token Immediately**
   ```bash
   # Don't wait - revoke NOW via the service's admin console
   # - Jira: https://id.atlassian.com/manage-profile/security/api-tokens
   # - OpenAI: https://platform.openai.com/api-keys
   # - GitHub: https://github.com/settings/tokens
   ```

2. **Notify Team**
   ```bash
   # Post in #engineering and #security channels
   # Include:
   # - What token was compromised
   # - When it was exposed
   # - Where it was exposed (if known)
   # - Current status
   ```

3. **Generate and Deploy New Token**
   ```bash
   # Follow standard procedure but FAST
   # Generate new token
   # Update all services simultaneously
   # Accept brief service disruption if necessary
   ```

### Investigation (parallel with rotation)

1. **Determine Scope**
   - Where was the token exposed? (logs, code repo, screenshot, etc.)
   - Who had access?
   - For how long was it exposed?

2. **Check for Unauthorized Use**
   ```bash
   # Check audit logs for:
   # - Unexpected API calls
   # - Unusual patterns
   # - Access from unknown IP addresses
   # - Timing: activity during off-hours
   ```

3. **Document Incident**
   ```bash
   # Create incident report
   # Include timeline, impact, remediation steps
   ```

### Post-Emergency Steps

1. **Review how token was exposed**
2. **Implement preventive measures**
3. **Update runbooks if needed**
4. **Conduct post-mortem**
5. **Consider additional security measures**

---

## Troubleshooting

### Issue: Service Can't Authenticate After Rotation

**Symptoms:**
- 401 Unauthorized errors
- Authentication failed messages in logs

**Diagnosis:**
```bash
# Check if service picked up new token
kubectl get pods
kubectl describe pod <pod-name> | grep -i secret

# Check if secret was updated
kubectl get secret <secret-name> -o yaml

# Check environment variables in running container
kubectl exec -it <pod-name> -- env | grep TOKEN
```

**Resolution:**
```bash
# If secret wasn't updated:
kubectl apply -f secret.yaml

# If pod didn't restart:
kubectl rollout restart deployment/<deployment-name>

# If still failing, verify token is correct:
# Test token manually with curl as shown in token-specific sections

# If token is invalid:
# - Check for copy-paste errors
# - Verify token hasn't expired
# - Regenerate if necessary
```

### Issue: Service Started Before Secret Updated

**Symptoms:**
- Initial authentication failures
- Failures only on some pods/instances

**Resolution:**
```bash
# Restart the affected pods
kubectl delete pod <pod-name>

# Or restart entire deployment
kubectl rollout restart deployment/<deployment-name>

# Wait for rollout to complete
kubectl rollout status deployment/<deployment-name>
```

### Issue: Some Services Updated, Others Not

**Symptoms:**
- Inconsistent behavior
- Some operations work, others don't

**Diagnosis:**
```bash
# List all deployments that might use the token
kubectl get deployments

# Check each deployment's secret references
kubectl get deployment <name> -o yaml | grep -A 5 secretRef

# Check pod restart times
kubectl get pods -o wide
```

**Resolution:**
```bash
# Update all services systematically
for deployment in pm-agent orchestrator uat-backend; do
  kubectl rollout restart deployment/$deployment
  kubectl rollout status deployment/$deployment
done
```

### Issue: Old Token Still Works After Revocation

**Symptoms:**
- Old token not properly revoked
- Both tokens working

**Diagnosis:**
```bash
# Test both tokens
curl -H "Authorization: Bearer OLD_TOKEN" https://api.service.com/test
curl -H "Authorization: Bearer NEW_TOKEN" https://api.service.com/test

# Both return 200 OK
```

**Resolution:**
```bash
# Verify you revoked the correct token
# Check token management console
# Token IDs, labels, or last-used dates

# If wrong token was revoked:
# - Restore if possible, or regenerate
# - Revoke the correct old token

# If service caches tokens:
# - Check TTL on cached credentials
# - Force cache clear if available
# - Wait for cache expiration
```

### Issue: Rate Limiting After Rotation

**Symptoms:**
- 429 Too Many Requests
- Rate limit exceeded errors

**Diagnosis:**
```bash
# Check if multiple services are using same token
# Each service might be hitting rate limits collectively

# Check API rate limit headers
curl -I -H "Authorization: Bearer TOKEN" https://api.service.com/endpoint
# Look for: X-RateLimit-Remaining, X-RateLimit-Reset
```

**Resolution:**
```bash
# Option 1: Generate separate tokens per service
# (if service supports it)

# Option 2: Implement token sharing properly
# - Use shared secret management
# - Ensure rate limit tracking across services

# Option 3: Implement rate limiting middleware
# in your services to respect API limits
```

### Issue: Token Permissions Changed

**Symptoms:**
- 403 Forbidden on operations that previously worked
- Permission denied errors

**Diagnosis:**
```bash
# Check token scopes/permissions in provider console
# Compare with previous token's permissions

# Test specific operations
curl -H "Authorization: Bearer TOKEN" https://api.service.com/endpoint
# Note which operations fail
```

**Resolution:**
```bash
# Regenerate token with correct permissions
# For GitHub: Select all needed scopes
# For Jira: Use admin account if needed
# For OpenAI: Check project restrictions

# Update token in all services
# Verify operations work
```

---

## Security Audit Log Template

Maintain a log of all token rotations in `docs/security-audit-log.md`:

```markdown
# Security Audit Log

## 2024-01-15 - Jira API Token Rotation

**Type:** Scheduled rotation
**Performed By:** Jane Doe
**Reason:** 30-day rotation policy
**Services Updated:** PM Agent, Orchestrator, UAT Backend
**Downtime:** None
**Issues:** None
**Old Token Revoked:** 2024-01-16 (24 hours post-rotation)

## 2024-01-10 - OpenAI API Key Emergency Rotation

**Type:** Emergency rotation
**Performed By:** John Smith
**Reason:** Key accidentally committed to public repository
**Services Updated:** PM Agent, Orchestrator
**Downtime:** ~2 minutes
**Issues:** Brief service interruption during rotation
**Old Key Revoked:** Immediately
**Post-Incident Actions:** 
- Implemented pre-commit hooks to prevent key commits
- Added secrets scanning to CI/CD
- Conducted team training on secrets management
```

---

## Additional Resources

### Secrets Management Tools
- **HashiCorp Vault**: Enterprise secrets management
- **AWS Secrets Manager**: AWS-native solution
- **Azure Key Vault**: Azure-native solution
- **Google Secret Manager**: GCP-native solution

### Monitoring and Alerting
- Set up alerts for authentication failures
- Monitor API rate limits
- Track token expiration dates
- Alert on suspicious API usage patterns

### Automation Opportunities
- Automated token expiration reminders
- Automated testing of new tokens before deployment
- Automated rollback on failure detection
- Token rotation scripts for common scenarios

### Contact Information
- **Security Team:** security@company.com
- **On-Call Engineer:** Use PagerDuty rotation
- **Emergency Contact:** [Emergency Phone Number]

---

**Last Updated:** 2024-01-15
**Version:** 1.0
**Owner:** Security Team
**Review Cycle:** Quarterly
