# Token Rotation Quick Reference Card

> **Quick access guide for on-call engineers performing token rotation**

## Emergency Contacts

- **On-Call Primary**: [Slack: #oncall-primary]
- **Security Team**: [Slack: #security-incidents]
- **Escalation**: [Phone: XXX-XXX-XXXX]

---

## Quick Commands

### 1. Jira Token Rotation

```bash
# Rotate
python3 scripts/rotate_token.py --service jira --token '<NEW_TOKEN>' --environment production

# Verify
python3 scripts/verify_token_rotation.py --environment production --service jira
```

### 2. OpenAI Key Rotation

```bash
# Rotate
python3 scripts/rotate_token.py --service openai --token '<NEW_KEY>' --environment production

# Verify
python3 scripts/verify_token_rotation.py --environment production --service openai
```

### 3. GitHub Token Rotation

```bash
# Rotate
python3 scripts/rotate_token.py --service github --token '<NEW_TOKEN>' --environment production

# Verify
python3 scripts/verify_token_rotation.py --environment production --service github
```

### 4. JWT Secret Rotation (Zero-Downtime)

```bash
# Rotate (zero-downtime mode)
python3 scripts/rotate_token.py --service jwt --token '<NEW_SECRET>' --environment production --zero-downtime

# Verify
python3 scripts/verify_token_rotation.py --environment production --service jwt
```

---

## Token Generation URLs

| Service | URL |
|---------|-----|
| **Jira** | https://id.atlassian.com/manage-profile/security/api-tokens |
| **OpenAI** | https://platform.openai.com/api-keys |
| **GitHub** | https://github.com/settings/tokens |
| **JWT** | Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |

---

## Pre-Flight Checklist

- [ ] Backup current secrets: `kubectl get secret sdt1-secrets -n production -o yaml > backup.yaml`
- [ ] Check current service health
- [ ] Have rollback plan ready
- [ ] Team notified on Slack

---

## Rollback Command

```bash
# Restore from backup
kubectl apply -f backup-secrets-$(date +%Y%m%d).yaml

# Restart services
kubectl rollout restart deployment/uat-backend -n production
kubectl rollout restart deployment/pm-agent -n production
kubectl rollout restart deployment/dev-agent -n production
```

---

## Health Check Commands

```bash
# Check deployments
kubectl get deployments -n production

# Check pods
kubectl get pods -n production

# Check logs for errors
kubectl logs -l app=uat-backend --tail=50 -n production | grep -i error
```

---

## Troubleshooting

### "401 Unauthorized" Errors

1. Verify token was generated correctly at source
2. Check secret was updated: `kubectl get secret sdt1-secrets -n production -o yaml`
3. Verify pods restarted: `kubectl get pods -n production`
4. Test token manually with curl

### Pods Not Restarting

```bash
# Force pod deletion
kubectl delete pod -l app=uat-backend -n production

# Watch pod recreation
kubectl get pods -n production -w
```

### Database Connection Failures

```bash
# Test connection from pod
kubectl exec -it deployment/uat-backend -n production -- \
  python3 -c "from database import test_connection; test_connection()"
```

---

## Post-Rotation Tasks

- [ ] Verify all services healthy
- [ ] Check logs for errors (10 minutes)
- [ ] Revoke old token at source
- [ ] Update rotation log
- [ ] Post in #operations Slack channel

---

## Rotation Schedule

| Token | Frequency | Next Due |
|-------|-----------|----------|
| Jira | 90 days | [DATE] |
| OpenAI | 90 days | [DATE] |
| GitHub | 90 days | [DATE] |
| JWT | 180 days | [DATE] |
| Database | 90 days | [DATE] |

---

## Full Documentation

See [TOKEN_ROTATION.md](TOKEN_ROTATION.md) for complete runbook with detailed procedures.

---

**Last Updated**: 2024-01-XX  
**Version**: 1.0
