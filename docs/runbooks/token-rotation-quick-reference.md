# Token Rotation Quick Reference

**⚠️ For detailed procedures, see [token-rotation.md](./token-rotation.md)**

## Emergency Quick Steps

If a token is compromised:

```bash
# 1. REVOKE OLD TOKEN IMMEDIATELY (via provider console)
# 2. Generate new token
# 3. Update and deploy
./scripts/rotate-k8s-secret.sh \
  --secret-name [SECRET] \
  --key [KEY] \
  --value "[NEW_VALUE]" \
  --deployments "[DEPLOY1,DEPLOY2]"

# 4. Verify
python scripts/verify-token-rotation.py --service all

# 5. Monitor logs
kubectl logs -f deployment/[SERVICE] | grep -i "auth\|error"
```

---

## Jira API Token

**Generate:** https://id.atlassian.com/manage-profile/security/api-tokens

**Quick Rotate:**
```bash
# 1. Generate new token from URL above
# 2. Update Kubernetes secret
kubectl create secret generic jira-api-token \
  --from-literal=token='NEW_TOKEN' \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart services
kubectl rollout restart deployment/pm-agent deployment/orchestrator deployment/uat-backend

# 4. Verify
python scripts/verify-token-rotation.py --service jira
```

**Services:** pm-agent, orchestrator, uat-backend  
**Rotation Schedule:** Every 30 days

---

## OpenAI API Key

**Generate:** https://platform.openai.com/api-keys

**Quick Rotate:**
```bash
# 1. Generate new key from URL above
# 2. Update Kubernetes secret
kubectl create secret generic openai-api-key \
  --from-literal=key='NEW_KEY' \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart services
kubectl rollout restart deployment/pm-agent deployment/orchestrator

# 4. Verify
python scripts/verify-token-rotation.py --service openai
```

**Services:** pm-agent, orchestrator  
**Rotation Schedule:** Every 60 days

---

## GitHub Token

**Generate:** https://github.com/settings/tokens

**Scopes Needed:** `repo`, `workflow` (if using Actions)

**Quick Rotate:**
```bash
# 1. Generate new token from URL above
# 2. Update Kubernetes secret
kubectl create secret generic github-token \
  --from-literal=token='NEW_TOKEN' \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart services
kubectl rollout restart deployment/orchestrator

# 4. Verify
python scripts/verify-token-rotation.py --service github
```

**Services:** orchestrator  
**Rotation Schedule:** Every 30 days

---

## Database Credentials

**Quick Rotate:**
```bash
# 1. Create new database user
psql -h [HOST] -U [ADMIN] -d [DB] << EOF
CREATE USER app_new WITH PASSWORD 'NEW_PASSWORD';
GRANT ALL ON SCHEMA public TO app_new;
GRANT ALL ON ALL TABLES IN SCHEMA public TO app_new;
EOF

# 2. Update Kubernetes secret
kubectl create secret generic db-credentials \
  --from-literal=username='app_new' \
  --from-literal=password='NEW_PASSWORD' \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart services
kubectl rollout restart deployment/uat-backend

# 4. Verify
python scripts/verify-token-rotation.py --service database

# 5. After 24 hours, drop old user
psql -h [HOST] -U [ADMIN] -d [DB] -c "DROP USER app_old;"
```

**Services:** uat-backend  
**Rotation Schedule:** Every 90 days

---

## Verification Commands

```bash
# Verify all tokens
python scripts/verify-token-rotation.py --service all

# Verify specific token
python scripts/verify-token-rotation.py --service [jira|openai|github|database]

# Check service health
kubectl get pods
kubectl logs -f deployment/[SERVICE]

# Check for auth errors
kubectl logs deployment/[SERVICE] --since=1h | grep -i "401\|403\|auth"

# Monitor real-time
kubectl logs -f deployment/[SERVICE] | grep -i "error"
```

---

## Rollback Procedure

If rotation causes issues:

```bash
# 1. Restore old secret (if backed up)
kubectl apply -f secret-backups/[SECRET]_[TIMESTAMP].yaml

# 2. Restart deployments
kubectl rollout restart deployment/[SERVICE]

# 3. Verify rollback
kubectl rollout status deployment/[SERVICE]
kubectl logs -f deployment/[SERVICE]

# 4. Investigate issue before retrying
```

---

## Using Helper Scripts

### Kubernetes Secret Rotation Script

```bash
# Dry run first
./scripts/rotate-k8s-secret.sh \
  --secret-name jira-api-token \
  --key token \
  --value "new_token_value" \
  --deployments "pm-agent,orchestrator" \
  --dry-run

# Actual rotation
./scripts/rotate-k8s-secret.sh \
  --secret-name jira-api-token \
  --key token \
  --value "new_token_value" \
  --deployments "pm-agent,orchestrator"
```

### Verification Script

```bash
# Set environment variables
export JIRA_EMAIL="email@example.com"
export JIRA_API_TOKEN="token"
export JIRA_DOMAIN="your-domain.atlassian.net"
export OPENAI_API_KEY="sk-..."
export GITHUB_TOKEN="ghp_..."
export DATABASE_URL="postgresql://..."

# Run verification
python scripts/verify-token-rotation.py --service all --verbose

# Save results to file
python scripts/verify-token-rotation.py --service all -o results.json
```

---

## Checklist

Before rotation:
- [ ] Notify team in #engineering
- [ ] Schedule during low-traffic period
- [ ] Have rollback plan ready
- [ ] Backup current secrets

During rotation:
- [ ] Generate new token/credential
- [ ] Test new token before deployment
- [ ] Update all services
- [ ] Verify health checks pass
- [ ] Monitor for errors

After rotation:
- [ ] All services healthy
- [ ] No authentication errors
- [ ] Update audit log
- [ ] Wait 24 hours before revoking old token
- [ ] Revoke old token
- [ ] Archive backup securely

---

## Common Issues

### "401 Unauthorized" after rotation
- Check if secret was actually updated: `kubectl get secret [NAME] -o yaml`
- Check if pod restarted: `kubectl get pods`
- Force restart: `kubectl delete pod [POD_NAME]`

### "Connection refused"
- Service might be starting up
- Wait and retry: `kubectl rollout status deployment/[SERVICE]`
- Check logs: `kubectl logs deployment/[SERVICE]`

### Some pods not updated
- Force restart all: `kubectl rollout restart deployment/[SERVICE]`
- Check rollout history: `kubectl rollout history deployment/[SERVICE]`

### Old token still works
- Token provider might cache (check TTL)
- Verify you revoked correct token
- Wait for cache expiration

---

## Important URLs

- **Jira API Tokens:** https://id.atlassian.com/manage-profile/security/api-tokens
- **OpenAI API Keys:** https://platform.openai.com/api-keys
- **GitHub Tokens:** https://github.com/settings/tokens
- **Full Runbook:** [token-rotation.md](./token-rotation.md)
- **Audit Log:** [docs/security-audit-log.md](../security-audit-log.md)

---

## Emergency Contacts

- **Security Team:** security@company.com
- **On-Call:** Use PagerDuty
- **Slack:** #engineering, #security

---

**Last Updated:** 2024-01-15  
**Owner:** Security Team
