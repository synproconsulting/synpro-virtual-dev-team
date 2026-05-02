# Token Rotation Runbook

## Overview

This runbook provides step-by-step procedures for rotating authentication tokens and API keys used across the SDT1 platform. Regular token rotation is a critical security practice that limits the exposure window for compromised credentials.

## Table of Contents

1. [Token Inventory](#token-inventory)
2. [Rotation Schedule](#rotation-schedule)
3. [Pre-Rotation Checklist](#pre-rotation-checklist)
4. [Rotation Procedures](#rotation-procedures)
5. [Post-Rotation Verification](#post-rotation-verification)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)

---

## Token Inventory

### Critical Tokens

| Token/Key | Service | Used By | Storage Location | Rotation Frequency |
|-----------|---------|---------|------------------|-------------------|
| `JIRA_API_TOKEN` | Jira Cloud | UAT Backend, Agents | Environment vars | 90 days |
| `OPENAI_API_KEY` | OpenAI | Agents, UAT Backend | Environment vars | 90 days |
| `GITHUB_TOKEN` | GitHub API | Agents, UAT Backend | Environment vars | 90 days |
| `JWT_SECRET_KEY` | JWT Auth | UAT Backend | Environment vars | 180 days |
| `DATABASE_PASSWORD` | PostgreSQL | UAT Backend | Environment vars | 90 days |
| `REDIS_PASSWORD` | Redis | UAT Backend | Environment vars | 90 days |

### Service Account Tokens

- **Jira Service Account**: Used for automation, ticket creation, and updates
- **GitHub Service Account**: Used for repository operations and PR management
- **OpenAI Service Account**: Used for LLM operations

---

## Rotation Schedule

### Regular Rotations

- **90-day rotation**: API tokens (Jira, OpenAI, GitHub)
- **180-day rotation**: JWT secret keys
- **30-day rotation**: Development/staging tokens
- **Immediate rotation**: Any suspected compromise

### Notification Timeline

- **T-14 days**: Initial notification to team
- **T-7 days**: Reminder and coordination meeting
- **T-2 days**: Final confirmation
- **T-0**: Rotation execution
- **T+1 day**: Post-rotation review

---

## Pre-Rotation Checklist

### Planning Phase (T-7 days)

- [ ] Identify all services using the token to be rotated
- [ ] Review recent logs for unusual activity
- [ ] Schedule maintenance window (if required)
- [ ] Notify team members and stakeholders
- [ ] Prepare rollback plan
- [ ] Test token rotation in staging environment

### Preparation Phase (T-1 day)

- [ ] Generate new token/credential
- [ ] Verify new token works in isolated test
- [ ] Document current token (last 4 chars only for verification)
- [ ] Backup current environment configuration
- [ ] Ensure monitoring and alerting are active
- [ ] Have incident response team on standby

### Tools & Access Required

- [ ] Access to token generation service (Jira/GitHub/OpenAI dashboard)
- [ ] Access to deployment environment (Kubernetes/Docker)
- [ ] Access to secrets manager or environment configuration
- [ ] Admin access to relevant services
- [ ] Communication channels (Slack, email) ready

---

## Rotation Procedures

### 1. Jira API Token Rotation

#### Generate New Token

1. Log in to Atlassian account: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name: `SDT1-Platform-YYYY-MM-DD`
4. Copy token immediately (it won't be shown again)
5. Store temporarily in password manager

#### Update Deployment

**For Kubernetes:**

```bash
# Backup current secret
kubectl get secret sdt1-secrets -n production -o yaml > backup-secrets-$(date +%Y%m%d).yaml

# Update the secret
kubectl create secret generic sdt1-secrets \
  --from-literal=JIRA_API_TOKEN='<new-token>' \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify secret updated
kubectl get secret sdt1-secrets -n production -o jsonpath='{.data.JIRA_API_TOKEN}' | base64 -d | tail -c 4
```

**For Docker Compose:**

```bash
# Backup current .env
cp .env .env.backup.$(date +%Y%m%d)

# Update token in .env
sed -i.bak "s/JIRA_API_TOKEN=.*/JIRA_API_TOKEN='<new-token>'/" .env

# Restart services
docker-compose restart uat-backend pm-agent dev-agent
```

**Using the rotation script:**

```bash
cd scripts
python3 rotate_token.py --service jira --token '<new-token>' --environment production
```

#### Restart Services

```bash
# Kubernetes
kubectl rollout restart deployment/uat-backend -n production
kubectl rollout restart deployment/pm-agent -n production
kubectl rollout restart deployment/dev-agent -n production

# Verify rollout
kubectl rollout status deployment/uat-backend -n production
```

#### Verify New Token

```bash
# Test Jira API with new token
curl -u <email>:<new-token> \
  -H "Accept: application/json" \
  https://<your-domain>.atlassian.net/rest/api/3/myself
```

#### Revoke Old Token

1. Return to Atlassian API tokens page
2. Find old token (by creation date)
3. Click "Revoke"
4. Confirm revocation

---

### 2. OpenAI API Key Rotation

#### Generate New Key

1. Log in to OpenAI: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Name: `SDT1-Platform-YYYY-MM-DD`
4. Copy key immediately
5. Store temporarily in password manager

#### Update Deployment

```bash
# Backup current secret
kubectl get secret sdt1-secrets -n production -o yaml > backup-secrets-$(date +%Y%m%d).yaml

# Update the secret
kubectl create secret generic sdt1-secrets \
  --from-literal=OPENAI_API_KEY='<new-key>' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart services
kubectl rollout restart deployment/pm-agent -n production
kubectl rollout restart deployment/dev-agent -n production
kubectl rollout restart deployment/uat-backend -n production
```

**Using the rotation script:**

```bash
python3 scripts/rotate_token.py --service openai --token '<new-key>' --environment production
```

#### Verify New Key

```bash
# Test OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer <new-key>" \
  -H "Content-Type: application/json"
```

#### Revoke Old Key

1. Return to OpenAI API keys page
2. Find old key (by creation date)
3. Click "Revoke"
4. Confirm revocation

---

### 3. GitHub Token Rotation

#### Generate New Token

1. Log in to GitHub: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: `SDT1-Platform-YYYY-MM-DD`
4. Set expiration: 90 days
5. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `read:org` (Read org and team membership)
6. Click "Generate token"
7. Copy token immediately

#### Update Deployment

```bash
# Update Kubernetes secret
kubectl create secret generic sdt1-secrets \
  --from-literal=GITHUB_TOKEN='<new-token>' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart services
kubectl rollout restart deployment/dev-agent -n production
kubectl rollout restart deployment/uat-backend -n production
```

**Using the rotation script:**

```bash
python3 scripts/rotate_token.py --service github --token '<new-token>' --environment production
```

#### Verify New Token

```bash
# Test GitHub API
curl -H "Authorization: Bearer <new-token>" \
  https://api.github.com/user
```

#### Revoke Old Token

1. Return to GitHub tokens page
2. Find old token (by name/date)
3. Click "Delete"
4. Confirm deletion

---

### 4. JWT Secret Key Rotation

**⚠️ CRITICAL**: JWT secret rotation requires zero-downtime strategy to avoid invalidating active user sessions.

#### Generate New Secret

```bash
# Generate strong random secret
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### Zero-Downtime Rotation Strategy

This uses a dual-key approach where both old and new keys are valid during transition:

```bash
# Phase 1: Add new key as secondary (services accept both old and new)
kubectl create secret generic sdt1-secrets \
  --from-literal=JWT_SECRET_KEY='<old-key>' \
  --from-literal=JWT_SECRET_KEY_NEW='<new-key>' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart services (they now accept both keys)
kubectl rollout restart deployment/uat-backend -n production

# Wait 5 minutes, verify no auth errors in logs
kubectl logs -f deployment/uat-backend -n production | grep -i "jwt\|auth"

# Phase 2: Switch to new key as primary, old as secondary
kubectl create secret generic sdt1-secrets \
  --from-literal=JWT_SECRET_KEY='<new-key>' \
  --from-literal=JWT_SECRET_KEY_OLD='<old-key>' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart services (they now issue with new, accept both)
kubectl rollout restart deployment/uat-backend -n production

# Phase 3: Remove old key after all tokens expired (wait JWT_EXPIRATION time)
# Wait 24 hours or your JWT expiration time
kubectl create secret generic sdt1-secrets \
  --from-literal=JWT_SECRET_KEY='<new-key>' \
  --dry-run=client -o yaml | kubectl apply -f -

# Final restart
kubectl rollout restart deployment/uat-backend -n production
```

**Using the rotation script:**

```bash
python3 scripts/rotate_token.py --service jwt --token '<new-key>' --environment production --zero-downtime
```

---

### 5. Database Password Rotation

**⚠️ CRITICAL**: Requires careful coordination to avoid service disruption.

#### Prerequisites

- [ ] Maintenance window scheduled
- [ ] Database backup completed
- [ ] Rollback plan ready

#### Rotation Steps

```bash
# 1. Generate new password
NEW_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Connect to database and create new password
psql -h <db-host> -U postgres -c "ALTER USER sdt1_user WITH PASSWORD '$NEW_PASSWORD';"

# 3. Update Kubernetes secret
kubectl create secret generic sdt1-secrets \
  --from-literal=DATABASE_PASSWORD="$NEW_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Restart services with new password
kubectl rollout restart deployment/uat-backend -n production

# 5. Verify connectivity
kubectl exec -it deployment/uat-backend -n production -- \
  python3 -c "from database import test_connection; test_connection()"
```

---

## Post-Rotation Verification

### Immediate Verification (T+0)

#### 1. Service Health Checks

```bash
# Check all deployments are running
kubectl get deployments -n production

# Check pod status
kubectl get pods -n production

# Check recent logs for errors
kubectl logs -l app=uat-backend --tail=100 -n production | grep -i error
kubectl logs -l app=pm-agent --tail=100 -n production | grep -i error
kubectl logs -l app=dev-agent --tail=100 -n production | grep -i error
```

#### 2. Functional Tests

```bash
# Run automated test suite
cd scripts
python3 verify_token_rotation.py --environment production

# Test key endpoints
curl -X POST https://api.sdt1.com/health
curl -X GET https://api.sdt1.com/api/tickets/active
```

#### 3. Monitor for Authentication Errors

```bash
# Watch logs in real-time for auth errors
kubectl logs -f deployment/uat-backend -n production | grep -E "401|403|Unauthorized|Forbidden"

# Check error rates in monitoring dashboard
# (Link to your Grafana/CloudWatch/Datadog dashboard)
```

### Extended Verification (T+1 hour)

- [ ] Verify agent task execution
- [ ] Check Jira ticket creation/updates
- [ ] Verify GitHub PR creation
- [ ] Test OpenAI API calls
- [ ] Review monitoring dashboards for anomalies

### Documentation (T+1 day)

- [ ] Update token rotation log
- [ ] Document any issues encountered
- [ ] Update this runbook with improvements
- [ ] Schedule next rotation

---

## Rollback Procedures

### When to Rollback

- Authentication failures exceeding 5% of requests
- Service unavailability
- Unable to access critical external APIs
- Data integrity issues

### Rollback Steps

#### 1. Immediate Rollback (Restore Old Token)

```bash
# Restore from backup
kubectl apply -f backup-secrets-$(date +%Y%m%d).yaml

# Restart services
kubectl rollout restart deployment/uat-backend -n production
kubectl rollout restart deployment/pm-agent -n production
kubectl rollout restart deployment/dev-agent -n production

# Verify services are healthy
kubectl get pods -n production
```

#### 2. Verify Rollback

```bash
# Check services are running with old token
python3 scripts/verify_token_rotation.py --environment production

# Monitor logs for errors
kubectl logs -f deployment/uat-backend -n production
```

#### 3. Incident Documentation

- Document what went wrong
- Capture error logs
- Schedule post-mortem
- Update runbook with lessons learned

---

## Troubleshooting

### Issue: "401 Unauthorized" Errors After Rotation

**Symptoms**: Services unable to authenticate with external API

**Diagnosis**:
```bash
# Check if secret was updated
kubectl get secret sdt1-secrets -n production -o jsonpath='{.data.JIRA_API_TOKEN}' | base64 -d | tail -c 4

# Check pod environment variables
kubectl exec -it deployment/uat-backend -n production -- env | grep TOKEN
```

**Resolution**:
1. Verify token was generated correctly from source (Jira/GitHub/OpenAI)
2. Verify token was updated in secret store
3. Verify pods were restarted and picked up new secret
4. Test token manually with curl
5. If token is invalid, generate a new one and repeat rotation

### Issue: Services Not Picking Up New Token

**Symptoms**: Services still using old token after restart

**Diagnosis**:
```bash
# Check pod restart time
kubectl get pods -n production -o wide

# Check if secret mounted correctly
kubectl exec -it deployment/uat-backend -n production -- \
  cat /var/run/secrets/app/JIRA_API_TOKEN | tail -c 4
```

**Resolution**:
1. Force pod restart: `kubectl delete pod -l app=uat-backend -n production`
2. Verify secret mount configuration in deployment
3. Check for secret caching issues

### Issue: JWT Token Validation Failures

**Symptoms**: Users getting logged out, "Invalid token" errors

**Diagnosis**:
```bash
# Check JWT secret configuration
kubectl logs deployment/uat-backend -n production | grep "JWT"

# Verify both old and new keys during transition
```

**Resolution**:
1. If in Phase 1/2 of JWT rotation, ensure both keys are configured
2. Verify JWT_SECRET_KEY_OLD is set during transition period
3. Extend transition period if needed
4. Ask affected users to re-login

### Issue: Database Connection Failures

**Symptoms**: "Connection refused" or "Authentication failed" errors

**Diagnosis**:
```bash
# Test database connection
kubectl exec -it deployment/uat-backend -n production -- \
  psql -h <db-host> -U sdt1_user -d sdt1_db -c "SELECT 1;"
```

**Resolution**:
1. Verify password was changed in database
2. Verify password was updated in Kubernetes secret
3. Verify pods restarted after secret update
4. Check database user permissions
5. If all else fails, rollback to old password

### Issue: Rate Limiting After Rotation

**Symptoms**: "429 Too Many Requests" errors

**Diagnosis**:
```bash
# Check API usage/rate limits
curl -H "Authorization: Bearer <token>" \
  https://api.openai.com/v1/usage
```

**Resolution**:
1. New tokens may have different rate limits
2. Wait for rate limit window to reset
3. Implement exponential backoff
4. Contact provider support if limits are too restrictive

---

## Token Rotation Log

Document all token rotations:

| Date | Token Type | Rotated By | Reason | Issues | Notes |
|------|------------|------------|--------|---------|-------|
| YYYY-MM-DD | JIRA_API_TOKEN | Name | Scheduled 90-day | None | Smooth rotation |
| YYYY-MM-DD | OPENAI_API_KEY | Name | Security incident | Brief downtime | Updated runbook |

---

## Automation

### Automated Rotation (Future Enhancement)

Consider implementing automated token rotation using:

- **AWS Secrets Manager** with automatic rotation
- **HashiCorp Vault** with dynamic secrets
- **Kubernetes External Secrets Operator**

### Rotation Reminders

Set up calendar reminders:
- 90 days for API tokens
- 180 days for JWT secrets
- 30 days for development tokens

### Monitoring & Alerts

Configure alerts for:
- Token expiration warnings (14 days before)
- Authentication failure rate spikes
- Service health check failures

---

## Contact Information

### On-Call Rotation

- Primary: [On-call schedule link]
- Secondary: [Backup contact]
- Escalation: [Management contact]

### Service Providers Support

- **Jira/Atlassian**: https://support.atlassian.com
- **OpenAI**: https://help.openai.com
- **GitHub**: https://support.github.com

---

## References

- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- Internal: [Security Policies Document]
- Internal: [Incident Response Playbook]

---

**Last Updated**: 2024-01-XX  
**Next Review**: YYYY-MM-DD  
**Document Owner**: Security Team
