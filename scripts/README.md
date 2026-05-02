# SDT1 Platform Scripts

This directory contains automation and operational scripts for the SDT1 platform.

## Token Rotation Scripts

### rotate_token.py

Automates token rotation for various services with support for zero-downtime strategies.

**Usage:**

```bash
# Basic rotation
python3 rotate_token.py --service <SERVICE> --token '<NEW_TOKEN>' --environment <ENV>

# Zero-downtime JWT rotation
python3 rotate_token.py --service jwt --token '<NEW_SECRET>' --environment production --zero-downtime

# Dry-run mode (test without applying changes)
python3 rotate_token.py --service jira --token '<NEW_TOKEN>' --environment staging --dry-run

# Verify rotation
python3 rotate_token.py --service openai --environment production --verify
```

**Supported Services:**
- `jira` - Jira API token
- `openai` - OpenAI API key
- `github` - GitHub personal access token
- `jwt` - JWT secret key
- `database` - Database password
- `redis` - Redis password

**Requirements:**
- `kubectl` configured with access to target cluster
- Python 3.11+
- PyYAML package: `pip install pyyaml`

### verify_token_rotation.py

Verifies that token rotation was successful by testing connectivity and authentication.

**Usage:**

```bash
# Verify all services
python3 verify_token_rotation.py --environment production

# Verify specific service
python3 verify_token_rotation.py --environment production --service jira

# Save results to custom file
python3 verify_token_rotation.py --environment staging --output results.json
```

**Checks Performed:**
- API authentication tests
- Kubernetes deployment health
- Pod logs for authentication errors
- Service endpoint availability

**Requirements:**
- `kubectl` configured with access to target cluster
- Python 3.11+
- `requests` package: `pip install requests`

## Installation

Install required dependencies:

```bash
pip install -r requirements-scripts.txt
```

Or install individually:

```bash
pip install pyyaml requests
```

## Configuration

Scripts read configuration from:
1. Environment variables
2. Kubernetes secrets (via kubectl)
3. Default configuration values

### Required Environment Variables

For verification script:
- `JIRA_BASE_URL` - Jira instance URL (default: auto-detected)
- `JIRA_EMAIL` - Jira service account email

### Kubernetes Access

Ensure kubectl is configured:

```bash
# Test access
kubectl get pods -n production

# Configure if needed
kubectl config use-context <your-cluster>
```

## Usage Examples

### Complete Rotation Workflow

```bash
# 1. Backup current secrets
kubectl get secret sdt1-secrets -n production -o yaml > backup.yaml

# 2. Generate new token at source (Jira/GitHub/OpenAI)

# 3. Rotate token
python3 rotate_token.py --service jira --token '<NEW_TOKEN>' --environment production

# 4. Verify rotation
python3 verify_token_rotation.py --environment production --service jira

# 5. If successful, revoke old token at source
```

### Testing in Staging First

```bash
# Always test in staging before production
python3 rotate_token.py --service openai --token '<TEST_KEY>' --environment staging
python3 verify_token_rotation.py --environment staging --service openai
```

### Dry-Run Mode

```bash
# Test rotation process without making changes
python3 rotate_token.py --service github --token '<NEW_TOKEN>' --environment production --dry-run
```

## Troubleshooting

### "kubectl: command not found"

Install kubectl:
```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### "Failed to get secret"

Check kubectl configuration:
```bash
kubectl config current-context
kubectl get secret sdt1-secrets -n production
```

### "No module named 'yaml'"

Install dependencies:
```bash
pip install pyyaml
```

### Script permissions

Make scripts executable:
```bash
chmod +x rotate_token.py verify_token_rotation.py
```

## Security Notes

- **Never commit tokens or secrets** to version control
- **Never log token values** - only log last 4 characters
- **Use secure channels** for sharing tokens (password managers, encrypted chat)
- **Revoke old tokens** immediately after successful rotation
- **Backup before rotation** - always keep a backup of current configuration
- **Test in staging** before rotating production tokens

## Logging

Scripts maintain logs in:
- `token_rotation_log.json` - Rotation history
- `verification_results.json` - Verification results
- `backups/` - Secret backups

These files should not be committed to version control.

## Related Documentation

- [Token Rotation Runbook](../docs/runbooks/TOKEN_ROTATION.md)
- [Quick Reference Card](../docs/runbooks/TOKEN_ROTATION_QUICK_REFERENCE.md)
- [Rotation Checklist Template](../docs/runbooks/templates/token_rotation_checklist.md)

## Contributing

When adding new scripts:
1. Include type hints and docstrings
2. Add usage examples to this README
3. Support `--dry-run` mode for safety
4. Handle errors gracefully with clear messages
5. Log important actions for audit trail

## Support

For issues or questions:
- Internal: #operations Slack channel
- Emergency: On-call rotation (see runbook)
- Documentation: [Token Rotation Runbook](../docs/runbooks/TOKEN_ROTATION.md)
