# Token Rotation Scripts

This directory contains helper scripts for token and credential rotation operations.

## Overview

Token rotation is a critical security practice. These scripts help automate and verify the rotation process to reduce errors and ensure consistency.

## Scripts

### 1. verify-token-rotation.py

Python script to verify that rotated tokens are working correctly across all services.

**Requirements:**
```bash
pip install requests psycopg2-binary
```

**Environment Variables:**
```bash
# Jira
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your_token"
export JIRA_DOMAIN="your-domain.atlassian.net"

# OpenAI
export OPENAI_API_KEY="sk-..."

# GitHub
export GITHUB_TOKEN="ghp_..."

# Database
export DATABASE_URL="postgresql://user:pass@host:5432/db"

# Service URLs (optional)
export PM_AGENT_URL="http://localhost:8000"
export ORCHESTRATOR_URL="http://localhost:8001"
export UAT_BACKEND_URL="http://localhost:8002"
```

**Usage:**
```bash
# Verify all services
python scripts/verify-token-rotation.py --service all

# Verify specific service
python scripts/verify-token-rotation.py --service jira
python scripts/verify-token-rotation.py --service openai
python scripts/verify-token-rotation.py --service github
python scripts/verify-token-rotation.py --service database

# Verbose output
python scripts/verify-token-rotation.py --service all --verbose

# Save results to file
python scripts/verify-token-rotation.py --service all -o results.json

# Check service health
python scripts/verify-token-rotation.py --service health
```

**What it checks:**
- **Jira:** Authentication, user info, project access
- **OpenAI:** Authentication, model access, GPT-4 availability
- **GitHub:** Authentication, token scopes, rate limits
- **Database:** Connection, query execution, current user
- **Health:** Service health endpoints

**Exit codes:**
- 0: All checks passed
- 1: One or more checks failed

---

### 2. rotate-k8s-secret.sh

Bash script to safely rotate Kubernetes secrets and restart affected deployments.

**Requirements:**
- `kubectl` installed and configured
- Access to Kubernetes cluster
- Appropriate RBAC permissions

**Usage:**
```bash
# Basic usage
./scripts/rotate-k8s-secret.sh \
  --secret-name jira-api-token \
  --key token \
  --value "new_token_here" \
  --deployments "pm-agent,orchestrator,uat-backend"

# Dry run (recommended first)
./scripts/rotate-k8s-secret.sh \
  --secret-name jira-api-token \
  --key token \
  --value "new_token_here" \
  --deployments "pm-agent,orchestrator" \
  --dry-run

# With custom namespace
./scripts/rotate-k8s-secret.sh \
  --secret-name github-token \
  --key token \
  --value "ghp_..." \
  --deployments "orchestrator" \
  --namespace production

# Skip backup (not recommended)
./scripts/rotate-k8s-secret.sh \
  --secret-name openai-api-key \
  --key key \
  --value "sk-..." \
  --deployments "pm-agent,orchestrator" \
  --skip-backup

# Custom wait time
./scripts/rotate-k8s-secret.sh \
  --secret-name db-credentials \
  --key password \
  --value "new_password" \
  --deployments "uat-backend" \
  --wait-time 600
```

**What it does:**
1. Backs up current secret to `./secret-backups/` directory
2. Updates or creates the Kubernetes secret
3. Restarts all specified deployments
4. Monitors rollout status
5. Verifies pods are running
6. Provides rollback instructions

**Options:**
- `--secret-name`: Name of the Kubernetes secret (required)
- `--key`: Key within the secret to update (required)
- `--value`: New value for the secret (required)
- `--deployments`: Comma-separated list of deployments to restart (required)
- `--namespace`: Kubernetes namespace (default: default)
- `--backup-dir`: Directory for backups (default: ./secret-backups)
- `--skip-backup`: Skip backing up current secret
- `--dry-run`: Print commands without executing
- `--wait-time`: Timeout for rollout status in seconds (default: 300)

**Exit codes:**
- 0: Success
- 1: Error occurred

---

## Workflow Example

Complete workflow for rotating the Jira API token:

```bash
# 1. Generate new token
# Visit: https://id.atlassian.com/manage-profile/security/api-tokens
# Create token, copy to clipboard

# 2. Set the new token value
NEW_TOKEN="your_new_token_here"

# 3. Test with verification script first (using old token)
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="old_token"
export JIRA_DOMAIN="your-domain.atlassian.net"
python scripts/verify-token-rotation.py --service jira

# 4. Dry run the rotation
./scripts/rotate-k8s-secret.sh \
  --secret-name jira-api-token \
  --key token \
  --value "$NEW_TOKEN" \
  --deployments "pm-agent,orchestrator,uat-backend" \
  --dry-run

# 5. Perform actual rotation
./scripts/rotate-k8s-secret.sh \
  --secret-name jira-api-token \
  --key token \
  --value "$NEW_TOKEN" \
  --deployments "pm-agent,orchestrator,uat-backend"

# 6. Verify new token works
export JIRA_API_TOKEN="$NEW_TOKEN"
python scripts/verify-token-rotation.py --service jira --verbose

# 7. Check service logs
kubectl logs -f deployment/pm-agent | grep -i "jira\|auth"

# 8. Monitor for 15 minutes
kubectl logs deployment/pm-agent --since=15m | grep -i "401\|403\|error"

# 9. If all good, document in audit log
# See: docs/security-audit-log.md

# 10. After 24 hours, revoke old token
# Visit: https://id.atlassian.com/manage-profile/security/api-tokens
```

---

## Troubleshooting

### Verification script fails with "Module not found"

```bash
# Install required dependencies
pip install requests psycopg2-binary

# Or if you have requirements.txt
pip install -r requirements.txt
```

### Rotation script fails with "kubectl: command not found"

```bash
# Install kubectl
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify installation
kubectl version --client
```

### "Permission denied" when running scripts

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run with bash explicitly
bash scripts/rotate-k8s-secret.sh --help
```

### Rollout fails or times out

```bash
# Check pod status
kubectl get pods

# Check pod events
kubectl describe pod <pod-name>

# Check logs
kubectl logs deployment/<deployment-name>

# Manually rollback using backup
kubectl apply -f secret-backups/<secret-name>_<timestamp>.yaml
kubectl rollout restart deployment/<deployment-name>
```

### Verification shows old token still works

This can happen due to:
1. **Token caching**: Some services cache tokens for a period
2. **Multiple replicas**: Some pods might not have restarted
3. **Not revoked**: Old token hasn't been revoked yet

**Solutions:**
```bash
# Force restart all pods
kubectl rollout restart deployment/<deployment-name>
kubectl delete pod -l app=<deployment-name>

# Wait for cache expiration (varies by service)

# Verify token was actually revoked in provider console
```

---

## Security Best Practices

1. **Never commit tokens/secrets** to version control
2. **Use dry-run first** to validate commands
3. **Always backup** before rotation (default behavior)
4. **Test new tokens** before deployment
5. **Monitor logs** during and after rotation
6. **Keep backups secure** and delete after retention period
7. **Document rotations** in security audit log
8. **Wait 24 hours** before revoking old tokens (allows rollback)
9. **Rotate regularly** according to schedule
10. **Use emergency procedure** for compromised tokens

---

## Backup Management

The rotation script creates backups in `./secret-backups/` by default.

**Backup format:**
```
secret-backups/
├── jira-api-token_20240115_143022.yaml
├── openai-api-key_20240115_150033.yaml
└── github-token_20240116_091544.yaml
```

**Retention policy:**
- Keep backups for 7 days after successful rotation
- Delete after 7 days if no issues occurred
- For emergency rotations, keep for 30 days
- Store securely (encrypted filesystem recommended)

**Manual backup:**
```bash
# Backup all secrets
kubectl get secrets -n <namespace> -o yaml > all-secrets-backup.yaml

# Backup specific secret
kubectl get secret <secret-name> -n <namespace> -o yaml > secret-backup.yaml

# Restore from backup
kubectl apply -f secret-backup.yaml
```

---

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines for automated rotation:

```yaml
# Example GitHub Actions workflow
name: Scheduled Token Rotation

on:
  schedule:
    - cron: '0 2 1 * *'  # Monthly at 2 AM on 1st
  workflow_dispatch:  # Manual trigger

jobs:
  rotate-tokens:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG }}" > kubeconfig
          export KUBECONFIG=kubeconfig
      
      - name: Rotate Jira Token
        run: |
          ./scripts/rotate-k8s-secret.sh \
            --secret-name jira-api-token \
            --key token \
            --value "${{ secrets.NEW_JIRA_TOKEN }}" \
            --deployments "pm-agent,orchestrator"
      
      - name: Verify Rotation
        run: |
          export JIRA_API_TOKEN="${{ secrets.NEW_JIRA_TOKEN }}"
          python scripts/verify-token-rotation.py --service jira
      
      - name: Notify Team
        if: failure()
        run: |
          # Send notification to Slack/email
          echo "Token rotation failed!"
```

---

## Contributing

When adding new scripts:

1. Follow existing naming conventions
2. Include usage documentation
3. Add error handling
4. Support dry-run mode
5. Provide clear error messages
6. Update this README

---

## Support

- **Documentation:** [docs/runbooks/token-rotation.md](../docs/runbooks/token-rotation.md)
- **Quick Reference:** [docs/runbooks/token-rotation-quick-reference.md](../docs/runbooks/token-rotation-quick-reference.md)
- **Security Team:** security@company.com
- **Issues:** Create ticket in Jira

---

**Last Updated:** 2024-01-15  
**Maintained By:** Security Team
