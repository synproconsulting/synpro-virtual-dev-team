# Token Rotation Runbook

## Overview

This runbook describes the procedure for rotating API tokens and secrets used by the PM Agent system. Regular token rotation is a critical security practice that limits the window of exposure if credentials are compromised.

**When to use this runbook:**
- Scheduled quarterly token rotation (recommended)
- After suspected credential exposure
- When team members with access to tokens leave the organization
- During security audits
- After a security incident

**Estimated time:** 30-45 minutes per environment

## Tokens and Secrets Inventory

The PM Agent system uses the following tokens and secrets:

### External API Tokens
1. **Jira API Token** (`JIRA_API_TOKEN`)
   - Used for: Reading/writing Jira tickets, reading custom fields
   - Scope: Full Jira API access
   - Location: Environment variables, AWS Secrets Manager

2. **OpenAI API Key** (`OPENAI_API_KEY`)
   - Used for: LLM completions, embeddings
   - Scope: OpenAI API access
   - Location: Environment variables, AWS Secrets Manager

3. **GitHub Personal Access Token** (`GITHUB_TOKEN`)
   - Used for: Repository operations, PR creation, code reading
   - Scope: `repo`, `workflow` permissions
   - Location: Environment variables, AWS Secrets Manager

### Internal Tokens
4. **Database Password** (`DATABASE_PASSWORD` in `DATABASE_URL`)
   - Used for: PostgreSQL connections
   - Location: Environment variables, AWS Secrets Manager

5. **JWT Secret Key** (`JWT_SECRET_KEY`)
   - Used for: Authentication token signing
   - Location: Environment variables, AWS Secrets Manager

6. **API Keys** (if applicable)
   - Custom API keys for service-to-service authentication
   - Location: Environment variables, AWS Secrets Manager

## Prerequisites

Before starting token rotation:

- [ ] Access to AWS Secrets Manager (or your secrets management system)
- [ ] Admin access to Jira, GitHub, OpenAI accounts
- [ ] SSH/kubectl access to production and staging environments
- [ ] Permissions to update environment variables in deployment systems
- [ ] Communication plan ready (notify team of planned downtime if required)
- [ ] Backup of current tokens in secure location
- [ ] At least two people on call (one primary, one backup)

## Pre-Rotation Checklist

1. **Schedule maintenance window** (if zero-downtime is not available)
   - Notify users 24-48 hours in advance
   - Choose low-traffic time window
   - Prepare status page updates

2. **Document current token metadata**
   ```bash
   # Create a secure note with token creation dates and last rotation
   echo "Rotation Date: $(date)" >> token-rotation-log.txt
   echo "Rotated by: $(whoami)" >> token-rotation-log.txt
   ```

3. **Verify backup and rollback procedures**
   - Test that current tokens are securely backed up
   - Confirm rollback process is understood

4. **Health check current system**
   ```bash
   # Verify all services are healthy before rotation
   curl https://api.yourdomain.com/health
   ```

## Rotation Procedures

### 1. Jira API Token Rotation

**Step 1.1: Create new Jira API token**

1. Log in to [Atlassian Account](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Navigate to Security → API tokens
3. Click "Create API token"
4. Name it: `pm-agent-api-token-YYYY-MM-DD`
5. Copy the token immediately (it won't be shown again)

**Step 1.2: Test new token**

```bash
# Test the new token before deploying
export NEW_JIRA_TOKEN="your-new-token"
export JIRA_EMAIL="your-email@example.com"
export JIRA_DOMAIN="yourcompany.atlassian.net"

# Test API access
curl -u "${JIRA_EMAIL}:${NEW_JIRA_TOKEN}" \
  "https://${JIRA_DOMAIN}/rest/api/3/myself" \
  -H "Accept: application/json"

# Should return user details if successful
```

**Step 1.3: Update token in secrets manager**

```bash
# AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id pm-agent/production/jira-token \
  --secret-string "${NEW_JIRA_TOKEN}"

# Verify update
aws secretsmanager get-secret-value \
  --secret-id pm-agent/production/jira-token \
  --query 'SecretString' \
  --output text | head -c 20
```

**Step 1.4: Update environment variables**

For containerized deployments:
```bash
# Kubernetes
kubectl set env deployment/pm-agent-backend \
  JIRA_API_TOKEN="${NEW_JIRA_TOKEN}" \
  -n production

# Docker Compose
# Update .env file then restart
docker-compose restart backend
```

**Step 1.5: Verify service functionality**

```bash
# Check logs for successful Jira API calls
kubectl logs -f deployment/pm-agent-backend -n production | grep -i jira

# Test a Jira operation through your API
curl -X POST https://api.yourdomain.com/api/tickets/test-jira-connection \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
```

**Step 1.6: Revoke old token**

1. Return to Atlassian Account → Security → API tokens
2. Find the old token
3. Click "Delete"
4. Confirm deletion

⚠️ **Wait 5-10 minutes** after verification before revoking the old token to ensure no processes are still using it.

---

### 2. OpenAI API Key Rotation

**Step 2.1: Create new OpenAI API key**

1. Log in to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Navigate to API keys
3. Click "Create new secret key"
4. Name it: `pm-agent-YYYY-MM-DD`
5. Set permissions (if available): Full access or restricted to needed models
6. Copy the key immediately

**Step 2.2: Test new API key**

```bash
# Test the new key
export NEW_OPENAI_KEY="sk-..."

curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer ${NEW_OPENAI_KEY}" \
  -H "Content-Type: application/json"

# Test a simple completion
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer ${NEW_OPENAI_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Say test successful"}],
    "max_tokens": 10
  }'
```

**Step 2.3: Update in secrets manager**

```bash
# AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id pm-agent/production/openai-key \
  --secret-string "${NEW_OPENAI_KEY}"
```

**Step 2.4: Update environment and restart services**

```bash
# Kubernetes
kubectl set env deployment/pm-agent-backend \
  OPENAI_API_KEY="${NEW_OPENAI_KEY}" \
  -n production

# Verify rollout
kubectl rollout status deployment/pm-agent-backend -n production
```

**Step 2.5: Verify AI functionality**

```bash
# Test AI completion through your API
curl -X POST https://api.yourdomain.com/api/chat/test \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

**Step 2.6: Revoke old key**

1. Return to OpenAI Platform → API keys
2. Find the old key
3. Click "Delete" or "Revoke"

---

### 3. GitHub Personal Access Token Rotation

**Step 3.1: Create new GitHub PAT**

1. Go to GitHub → Settings → Developer settings → [Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: `pm-agent-production-YYYY-MM-DD`
4. Expiration: 90 days (recommended for automatic rotation reminders)
5. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
6. Click "Generate token"
7. Copy the token immediately

**Step 3.2: Test new token**

```bash
# Test the new token
export NEW_GITHUB_TOKEN="ghp_..."

# Test API access
curl -H "Authorization: token ${NEW_GITHUB_TOKEN}" \
  https://api.github.com/user

# Test repository access
curl -H "Authorization: token ${NEW_GITHUB_TOKEN}" \
  https://api.github.com/repos/your-org/your-repo
```

**Step 3.3: Update in secrets manager**

```bash
# AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id pm-agent/production/github-token \
  --secret-string "${NEW_GITHUB_TOKEN}"
```

**Step 3.4: Update environment**

```bash
# Kubernetes
kubectl set env deployment/pm-agent-backend \
  GITHUB_TOKEN="${NEW_GITHUB_TOKEN}" \
  -n production

# Also update any GitHub Actions secrets if applicable
# Go to Repository → Settings → Secrets and variables → Actions
# Update the GITHUB_TOKEN secret
```

**Step 3.5: Verify GitHub operations**

```bash
# Test creating a branch or PR through your API
curl -X POST https://api.yourdomain.com/api/github/test \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"

# Check logs
kubectl logs -f deployment/pm-agent-backend -n production | grep -i github
```

**Step 3.6: Revoke old token**

1. Return to GitHub → Settings → Developer settings → Personal access tokens
2. Find the old token
3. Click "Delete"

---

### 4. Database Password Rotation

⚠️ **Critical:** This requires careful coordination to avoid service disruption.

**Step 4.1: Prepare for database password rotation**

```bash
# Check current database connections
psql -h your-db-host -U your-db-user -d your-db -c \
  "SELECT count(*) FROM pg_stat_activity WHERE usename = 'your-db-user';"
```

**Step 4.2: Create new database password**

```bash
# Generate a strong password
NEW_DB_PASSWORD=$(openssl rand -base64 32)
echo "New password: ${NEW_DB_PASSWORD}"
# Store securely!
```

**Step 4.3: Update database user password**

```sql
-- Connect as admin user
psql -h your-db-host -U postgres

-- Update password
ALTER USER your_db_user WITH PASSWORD 'new-secure-password';

-- Verify
\du your_db_user
```

**Step 4.4: Update connection string in secrets manager**

```bash
# Build new DATABASE_URL
NEW_DATABASE_URL="postgresql://your-db-user:${NEW_DB_PASSWORD}@your-db-host:5432/your-db"

# Update in secrets manager
aws secretsmanager update-secret \
  --secret-id pm-agent/production/database-url \
  --secret-string "${NEW_DATABASE_URL}"
```

**Step 4.5: Rolling update with zero downtime**

```bash
# Update pods one at a time to maintain availability
kubectl set env deployment/pm-agent-backend \
  DATABASE_URL="${NEW_DATABASE_URL}" \
  -n production

# Monitor the rollout
kubectl rollout status deployment/pm-agent-backend -n production

# Watch for connection errors
kubectl logs -f deployment/pm-agent-backend -n production | grep -i database
```

**Step 4.6: Verify database connectivity**

```bash
# Test database connection through your API
curl https://api.yourdomain.com/health

# Should show database: healthy
```

---

### 5. JWT Secret Key Rotation

⚠️ **Note:** Rotating JWT secret will invalidate all existing user sessions.

**Step 5.1: Generate new JWT secret**

```bash
# Generate a strong secret (256-bit)
NEW_JWT_SECRET=$(openssl rand -base64 32)
echo "New JWT secret: ${NEW_JWT_SECRET}"
```

**Step 5.2: Implement dual-secret verification (optional)**

For zero-downtime rotation, implement dual-secret verification:

```python
# In your JWT verification code
def verify_token(token: str) -> dict:
    """Verify JWT with current or previous secret."""
    secrets = [
        os.getenv("JWT_SECRET_KEY"),
        os.getenv("JWT_SECRET_KEY_PREVIOUS")  # Keep old secret temporarily
    ]
    
    for secret in secrets:
        try:
            return jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.InvalidSignatureError:
            continue
    
    raise jwt.InvalidSignatureError("Token invalid with all secrets")
```

**Step 5.3: Update secrets manager**

```bash
# Store old secret as previous
OLD_JWT_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id pm-agent/production/jwt-secret \
  --query 'SecretString' \
  --output text)

aws secretsmanager update-secret \
  --secret-id pm-agent/production/jwt-secret-previous \
  --secret-string "${OLD_JWT_SECRET}"

# Update to new secret
aws secretsmanager update-secret \
  --secret-id pm-agent/production/jwt-secret \
  --secret-string "${NEW_JWT_SECRET}"
```

**Step 5.4: Update environment variables**

```bash
# Kubernetes - update both secrets
kubectl set env deployment/pm-agent-backend \
  JWT_SECRET_KEY="${NEW_JWT_SECRET}" \
  JWT_SECRET_KEY_PREVIOUS="${OLD_JWT_SECRET}" \
  -n production
```

**Step 5.5: Grace period**

Wait 24 hours (or your max token lifetime) before removing the old secret.

**Step 5.6: Remove old secret**

```bash
# After grace period
kubectl set env deployment/pm-agent-backend \
  JWT_SECRET_KEY_PREVIOUS- \
  -n production

# Remove from secrets manager
aws secretsmanager delete-secret \
  --secret-id pm-agent/production/jwt-secret-previous \
  --force-delete-without-recovery
```

---

## Post-Rotation Verification

### Comprehensive System Test

```bash
#!/bin/bash
# post-rotation-test.sh

echo "=== Post-Rotation System Verification ==="

# 1. Health check
echo "1. Checking system health..."
curl -f https://api.yourdomain.com/health || echo "❌ Health check failed"

# 2. Test Jira integration
echo "2. Testing Jira integration..."
curl -X GET https://api.yourdomain.com/api/tickets/test \
  -H "Authorization: Bearer ${AUTH_TOKEN}" || echo "❌ Jira test failed"

# 3. Test AI functionality
echo "3. Testing AI functionality..."
curl -X POST https://api.yourdomain.com/api/chat/test \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' || echo "❌ AI test failed"

# 4. Test GitHub integration
echo "4. Testing GitHub integration..."
curl -X GET https://api.yourdomain.com/api/github/repos \
  -H "Authorization: Bearer ${AUTH_TOKEN}" || echo "❌ GitHub test failed"

# 5. Test database
echo "5. Testing database connectivity..."
curl -X GET https://api.yourdomain.com/api/conversations \
  -H "Authorization: Bearer ${AUTH_TOKEN}" || echo "❌ Database test failed"

echo "=== Verification Complete ==="
```

Run the test script:
```bash
chmod +x post-rotation-test.sh
./post-rotation-test.sh
```

### Monitoring

Monitor these metrics for 24 hours post-rotation:

```bash
# Error rates
kubectl logs deployment/pm-agent-backend -n production | grep -i error | wc -l

# API latency
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/health

# Active connections
kubectl get pods -n production -o wide
```

### Update Documentation

- [ ] Update token rotation log
- [ ] Update token creation dates in documentation
- [ ] Document any issues encountered
- [ ] Update next scheduled rotation date

```bash
# Update rotation log
cat >> docs/token-rotation-log.txt << EOF
---
Rotation Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Rotated By: $(whoami)
Tokens Rotated: Jira, OpenAI, GitHub, Database, JWT
Issues Encountered: None
Next Rotation Due: $(date -u -d "+90 days" +"%Y-%m-%d")
EOF
```

## Rollback Procedures

If issues occur after rotation, follow these steps to rollback:

### Quick Rollback

```bash
#!/bin/bash
# rollback-tokens.sh

echo "⚠️  Rolling back token rotation..."

# Restore from secrets manager previous versions
for SECRET in jira-token openai-key github-token database-url jwt-secret; do
  echo "Restoring ${SECRET}..."
  
  # Get previous version
  aws secretsmanager get-secret-value \
    --secret-id "pm-agent/production/${SECRET}" \
    --version-stage AWSPREVIOUS \
    --query 'SecretString' \
    --output text > /tmp/${SECRET}.txt
  
  # Restore
  aws secretsmanager update-secret \
    --secret-id "pm-agent/production/${SECRET}" \
    --secret-string "file:///tmp/${SECRET}.txt"
done

# Trigger deployment rollback
kubectl rollout undo deployment/pm-agent-backend -n production

echo "✅ Rollback complete. Verifying..."
kubectl rollout status deployment/pm-agent-backend -n production
```

### Per-Token Rollback

If only one token is causing issues:

```bash
# Example: Rollback Jira token only
OLD_JIRA_TOKEN="your-backed-up-token"

kubectl set env deployment/pm-agent-backend \
  JIRA_API_TOKEN="${OLD_JIRA_TOKEN}" \
  -n production

# Monitor
kubectl logs -f deployment/pm-agent-backend -n production
```

## Troubleshooting

### Issue: "Authentication failed" errors after rotation

**Symptoms:** 401/403 errors in logs, API calls failing

**Solution:**
```bash
# 1. Verify new token is correct
echo $JIRA_API_TOKEN | head -c 20

# 2. Check token was properly updated in environment
kubectl get deployment pm-agent-backend -n production -o json | \
  jq '.spec.template.spec.containers[0].env'

# 3. Verify pod picked up new environment variable
kubectl exec -it deployment/pm-agent-backend -n production -- \
  env | grep JIRA_API_TOKEN

# 4. If not updated, force restart
kubectl rollout restart deployment/pm-agent-backend -n production
```

### Issue: Database connection pool errors

**Symptoms:** "Too many connections", "Connection refused"

**Solution:**
```bash
# 1. Check active connections
psql -h your-db-host -U postgres -c \
  "SELECT count(*), usename FROM pg_stat_activity GROUP BY usename;"

# 2. Kill old connections using old password
psql -h your-db-host -U postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE usename = 'your_db_user' AND state = 'idle';"

# 3. Restart pods to create fresh connections
kubectl rollout restart deployment/pm-agent-backend -n production
```

### Issue: Users logged out after JWT rotation

**Symptoms:** All users forced to log in again

**Solution:** This is expected behavior. Notify users in advance:

```bash
# Send notification before rotation
curl -X POST https://api.yourdomain.com/api/admin/broadcast \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{"message": "System maintenance in 5 minutes. You may need to log in again."}'
```

### Issue: GitHub operations failing

**Symptoms:** Cannot create PRs, branches, or read repos

**Solution:**
```bash
# 1. Verify token scopes
curl -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/user -I | grep X-OAuth-Scopes

# 2. Check rate limits
curl -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/rate_limit

# 3. Test specific operation
curl -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/repos/your-org/your-repo/branches

# 4. If scopes are wrong, create new token with correct scopes
```

### Issue: OpenAI rate limit or quota errors

**Symptoms:** "Rate limit exceeded", "Quota exceeded"

**Solution:**
```bash
# Check OpenAI account usage
curl https://api.openai.com/v1/usage?date=$(date +%Y-%m-%d) \
  -H "Authorization: Bearer ${OPENAI_API_KEY}"

# Verify you're using the correct organization
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "OpenAI-Organization: your-org-id"
```

## Security Best Practices

### Token Storage

1. **Never commit tokens to git**
   ```bash
   # Add to .gitignore
   echo "*.env" >> .gitignore
   echo ".env.local" >> .gitignore
   echo "*secret*" >> .gitignore
   ```

2. **Use secrets manager**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - GCP Secret Manager

3. **Encrypt tokens at rest**
   ```bash
   # Example: Encrypt local backup
   echo "${JIRA_API_TOKEN}" | \
     openssl enc -aes-256-cbc -salt -out jira-token.enc
   ```

### Token Rotation Schedule

| Token Type | Rotation Frequency | Auto-Expiry |
|------------|-------------------|-------------|
| Jira API Token | 90 days | No |
| OpenAI API Key | 90 days | No |
| GitHub PAT | 90 days | Yes (recommended) |
| Database Password | 90 days | No |
| JWT Secret | 180 days | No |

### Audit Logging

Log all token rotations:

```bash
# Example audit log entry
cat >> /var/log/token-rotation-audit.log << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "action": "token_rotation",
  "token_type": "jira_api_token",
  "rotated_by": "$(whoami)",
  "environment": "production",
  "old_token_last_4": "${OLD_TOKEN: -4}",
  "new_token_last_4": "${NEW_TOKEN: -4}",
  "rotation_reason": "scheduled_rotation"
}
EOF
```

### Access Control

Limit who can rotate tokens:

```bash
# AWS IAM policy for secrets rotation
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:UpdateSecret",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:pm-agent/production/*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "your-org-id"
        }
      }
    }
  ]
}
```

## Automation

### Automated Rotation Script

Create an automated rotation script for scheduled rotations:

```python
#!/usr/bin/env python3
"""
Automated token rotation script.
Usage: python rotate_tokens.py --environment production --tokens jira,openai
"""

import os
import sys
import boto3
import requests
from datetime import datetime
from typing import List

class TokenRotator:
    """Handles automated token rotation."""
    
    def __init__(self, environment: str):
        self.environment = environment
        self.secrets_client = boto3.client('secretsmanager')
        self.rotation_log = []
    
    def rotate_jira_token(self) -> bool:
        """Rotate Jira API token."""
        print("🔄 Rotating Jira API token...")
        
        # This is a placeholder - actual implementation would:
        # 1. Call Jira API to create new token (if API available)
        # 2. Test new token
        # 3. Update secrets manager
        # 4. Trigger deployment update
        # 5. Verify and revoke old token
        
        try:
            # Implementation here
            self.rotation_log.append({
                'token': 'jira',
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
            return True
        except Exception as e:
            print(f"❌ Failed to rotate Jira token: {e}")
            self.rotation_log.append({
                'token': 'jira',
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return False
    
    def rotate_openai_key(self) -> bool:
        """Rotate OpenAI API key."""
        print("🔄 Rotating OpenAI API key...")
        
        # Implementation similar to above
        return True
    
    def send_notification(self, success: bool):
        """Send notification about rotation status."""
        status = "✅ Success" if success else "❌ Failed"
        message = f"Token rotation {status}\n\nLog:\n{self.rotation_log}"
        
        # Send to Slack, email, etc.
        print(message)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Rotate PM Agent tokens')
    parser.add_argument('--environment', required=True, 
                       choices=['staging', 'production'])
    parser.add_argument('--tokens', required=True,
                       help='Comma-separated list of tokens to rotate')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate rotation without making changes')
    
    args = parser.parse_args()
    
    rotator = TokenRotator(args.environment)
    tokens = args.tokens.split(',')
    
    all_success = True
    for token in tokens:
        token = token.strip()
        if token == 'jira':
            all_success &= rotator.rotate_jira_token()
        elif token == 'openai':
            all_success &= rotator.rotate_openai_key()
    
    rotator.send_notification(all_success)
    sys.exit(0 if all_success else 1)

if __name__ == '__main__':
    main()
```

### Scheduled Rotation (Cron)

```bash
# Add to crontab for quarterly rotation
# Run first Sunday of each quarter at 2 AM
0 2 1 1,4,7,10 * /usr/local/bin/check-and-rotate-tokens.sh

# check-and-rotate-tokens.sh
#!/bin/bash
set -e

# Only run on first Sunday
if [ $(date +\%u) -eq 7 ] && [ $(date +\%d) -le 7 ]; then
    echo "Running quarterly token rotation..."
    python /opt/pm-agent/scripts/rotate_tokens.py \
        --environment production \
        --tokens jira,openai,github
fi
```

## Compliance and Auditing

### Compliance Requirements

Document your compliance requirements:

- **SOC 2**: Token rotation every 90 days
- **PCI-DSS**: Strong authentication, regular rotation
- **HIPAA**: Access logging, encryption at rest and in transit
- **GDPR**: Data encryption, access controls

### Audit Trail

Maintain an audit trail of all rotations:

```bash
# Query AWS CloudTrail for secrets access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::SecretsManager::Secret \
  --max-results 50 \
  --output table

# Export audit log
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::SecretsManager::Secret \
  --output json > token-rotation-audit-$(date +%Y%m%d).json
```

## Emergency Procedures

### Compromised Token

If a token is suspected to be compromised:

1. **Immediate rotation** (don't wait for maintenance window)
2. **Revoke old token immediately**
3. **Audit access logs** for suspicious activity
4. **Notify security team**
5. **Document incident**

```bash
#!/bin/bash
# emergency-rotation.sh

echo "🚨 EMERGENCY TOKEN ROTATION"
read -p "Which token is compromised? (jira/openai/github/db/jwt): " TOKEN
read -p "Confirm emergency rotation of ${TOKEN}? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted"
    exit 1
fi

# Immediate rotation without testing phase
case $TOKEN in
    jira)
        # Generate new token manually, then update immediately
        read -sp "Paste new Jira token: " NEW_TOKEN
        aws secretsmanager update-secret \
            --secret-id pm-agent/production/jira-token \
            --secret-string "${NEW_TOKEN}"
        kubectl set env deployment/pm-agent-backend \
            JIRA_API_TOKEN="${NEW_TOKEN}" -n production
        ;;
    # Add other cases...
esac

echo "✅ Emergency rotation complete"
echo "📝 Document this incident in the security log"
```

## Contacts

- **On-Call Engineer**: Check PagerDuty schedule
- **Security Team**: security@yourcompany.com
- **DevOps Lead**: devops@yourcompany.com
- **Incident Commander**: Use incident response procedure

## Appendix

### A. Token Generation Best Practices

```bash
# Generate cryptographically secure tokens
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate strong passwords
openssl rand -base64 32

# Generate UUID
uuidgen
```

### B. Secrets Manager CLI Reference

```bash
# List all secrets
aws secretsmanager list-secrets

# Get secret value
aws secretsmanager get-secret-value --secret-id your-secret

# Update secret
aws secretsmanager update-secret \
  --secret-id your-secret \
  --secret-string "new-value"

# Get previous version
aws secretsmanager get-secret-value \
  --secret-id your-secret \
  --version-stage AWSPREVIOUS
```

### C. Testing Checklist

- [ ] Jira API connectivity
- [ ] OpenAI API completions
- [ ] GitHub repository access
- [ ] Database queries
- [ ] User authentication
- [ ] Service-to-service communication
- [ ] Background jobs
- [ ] Scheduled tasks

### D. Related Documentation

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Next Review Date:** Quarterly  
**Owner:** DevOps Team
