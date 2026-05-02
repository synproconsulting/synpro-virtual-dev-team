# Token Rotation Scripts

This directory contains automated scripts for rotating API tokens and secrets used by the PM Agent system.

## Overview

Regular token rotation is a critical security practice. These scripts automate the process while maintaining audit trails and minimizing downtime.

## Scripts

### `rotate_tokens.py`

Primary token rotation script with comprehensive features:
- Automated rotation for multiple token types
- Dry-run mode for testing
- Audit logging
- Health checks and validation
- Rollback support

**Usage:**
```bash
# Dry run - test without making changes
python rotate_tokens.py --environment staging --tokens all --dry-run

# Rotate specific tokens
python rotate_tokens.py --environment production --tokens jira,openai

# Automated rotation (no prompts)
python rotate_tokens.py --environment production --tokens jwt --force

# With audit log
python rotate_tokens.py --environment production --tokens all --audit-log /var/log/rotation.json
```

### `emergency_rotation.sh`

Emergency rotation script for compromised credentials:
- Fast rotation without extensive testing
- Manual verification steps
- Audit logging
- Immediate token revocation

**Usage:**
```bash
# Emergency rotation
./emergency_rotation.sh production jira
./emergency_rotation.sh staging openai
```

### `verify_rotation.sh`

Post-rotation verification script:
- Tests all API endpoints
- Verifies token functionality
- Checks deployment status
- Generates health report

**Usage:**
```bash
./verify_rotation.sh production
./verify_rotation.sh staging
```

## Supported Token Types

| Token Type | Description | Rotation Impact |
|------------|-------------|-----------------|
| `jira` | Jira API Token | Low - seamless rotation |
| `openai` | OpenAI API Key | Low - seamless rotation |
| `github` | GitHub PAT | Low - seamless rotation |
| `jwt` | JWT Secret Key | High - invalidates user sessions |
| `database` | Database Password | Medium - requires coordination |

## Prerequisites

### Required Tools

- Python 3.11+
- AWS CLI (configured with credentials)
- kubectl (configured for cluster access)
- bash 4.0+

### Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- boto3 (AWS SDK)
- requests (HTTP client)

### AWS Permissions

Required IAM permissions:
- `secretsmanager:GetSecretValue`
- `secretsmanager:UpdateSecret`
- `ssm:GetParameter` (if using SSM)
- `ssm:PutParameter` (if using SSM)

### Kubernetes Permissions

Required RBAC permissions:
- `deployments.apps/get`
- `deployments.apps/patch`
- `pods/get`
- `pods/list`

## Environment Variables

### For Automated Rotation

Set these when using `--force` mode:

```bash
# For Jira rotation
export NEW_JIRA_TOKEN="your-new-token"
export JIRA_EMAIL="your-email@example.com"
export JIRA_DOMAIN="yourcompany.atlassian.net"

# For OpenAI rotation
export NEW_OPENAI_KEY="sk-..."

# For GitHub rotation
export NEW_GITHUB_TOKEN="ghp_..."
```

## Testing

Run the test suite:

```bash
# All tests
pytest scripts/tests/

# With coverage
pytest --cov=scripts scripts/tests/

# Specific test file
pytest scripts/tests/test_token_rotation.py -v
```

## Best Practices

### 1. Always Use Dry-Run First

```bash
# Test the rotation before executing
python rotate_tokens.py --environment production --tokens all --dry-run
```

### 2. Schedule Regular Rotations

Add to crontab for quarterly rotation:
```bash
# First Sunday of each quarter at 2 AM
0 2 1 1,4,7,10 * /opt/pm-agent/scripts/rotate_tokens.py --environment production --tokens all --force
```

### 3. Maintain Audit Logs

```bash
# Always save audit logs
python rotate_tokens.py \
  --environment production \
  --tokens all \
  --audit-log /var/log/pm-agent/rotation-$(date +%Y%m%d).json
```

### 4. Verify After Rotation

```bash
# Run verification script
./verify_rotation.sh production
```

### 5. Document Emergency Rotations

```bash
# Document why emergency rotation was needed
cat >> /var/log/pm-agent/emergency-rotation-log.txt << EOF
Date: $(date)
Token: jira
Reason: Suspected credential exposure in logs
Rotated by: $(whoami)
Incident: INC-12345
EOF
```

## Rotation Schedule

| Environment | Token Types | Frequency | Day |
|-------------|-------------|-----------|-----|
| Production | All | Quarterly | First Sunday |
| Staging | All | Monthly | First Sunday |

## Troubleshooting

### Issue: Script fails with AWS credentials error

**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Refresh credentials
aws sso login
```

### Issue: Kubernetes connection timeout

**Solution:**
```bash
# Verify kubectl context
kubectl config current-context

# Test connectivity
kubectl cluster-info
```

### Issue: Token validation fails

**Solution:**
```bash
# Manually test the new token
curl -H "Authorization: Bearer ${NEW_TOKEN}" https://api.example.com/test

# Check token scopes/permissions in the provider platform
```

### Issue: Deployment rollout stuck

**Solution:**
```bash
# Check pod status
kubectl get pods -n production

# Check logs
kubectl logs -f deployment/pm-agent-backend -n production

# If needed, rollback
kubectl rollout undo deployment/pm-agent-backend -n production
```

## Security Considerations

### Token Storage

- Never commit tokens to git
- Use AWS Secrets Manager or equivalent
- Encrypt tokens at rest
- Limit access to rotation scripts

### Access Control

- Limit who can run rotation scripts
- Use IAM roles with minimum required permissions
- Enable MFA for production rotations
- Log all rotation activities

### Audit Trail

All rotations are logged to:
- AWS CloudTrail (automatic)
- Local audit logs (`logs/` directory)
- Kubernetes audit logs
- Application logs

Query audit trail:
```bash
# AWS CloudTrail
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::SecretsManager::Secret \
  --max-results 50

# Local logs
cat /var/log/pm-agent/rotation-*.json | jq '.results'
```

## Rollback Procedures

### Quick Rollback

If rotation causes issues:

```bash
# Get previous secret version
aws secretsmanager get-secret-value \
  --secret-id pm-agent/production/jira-token \
  --version-stage AWSPREVIOUS

# Update to previous version
aws secretsmanager update-secret \
  --secret-id pm-agent/production/jira-token \
  --secret-string "$(aws secretsmanager get-secret-value \
    --secret-id pm-agent/production/jira-token \
    --version-stage AWSPREVIOUS \
    --query 'SecretString' \
    --output text)"

# Restart deployment
kubectl rollout restart deployment/pm-agent-backend -n production
```

### Per-Token Rollback

Use the backup files created during rotation:

```bash
# List backups
ls -la logs/backup-*.enc

# Restore from backup
cat logs/backup-production-jira-token-20240101-120000.enc | \
  aws secretsmanager update-secret \
    --secret-id pm-agent/production/jira-token \
    --secret-string file:///dev/stdin
```

## Monitoring

### Post-Rotation Monitoring

Monitor these metrics for 24 hours after rotation:

1. **Error Rates**
   ```bash
   kubectl logs deployment/pm-agent-backend -n production | grep ERROR | wc -l
   ```

2. **API Response Times**
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/health
   ```

3. **Authentication Failures**
   ```bash
   kubectl logs deployment/pm-agent-backend -n production | grep -i "auth" | grep -i "fail"
   ```

4. **Active Connections**
   ```bash
   kubectl get pods -n production -o wide
   kubectl top pods -n production
   ```

## Compliance

### SOC 2 Requirements

- Rotate tokens every 90 days
- Maintain audit logs for 1 year
- Implement dual-person control for production
- Document all rotations

### Audit Documentation

Each rotation should document:
- Date and time
- Environment
- Tokens rotated
- Who performed rotation
- Reason (scheduled/emergency)
- Any issues encountered
- Verification results

## Related Documentation

- [Token Rotation Runbook](../docs/runbooks/token-rotation.md) - Detailed procedures
- [Security Best Practices](../docs/security.md) - Security guidelines
- [Incident Response](../docs/incident-response.md) - Emergency procedures

## Support

For issues or questions:
- On-call engineer: Check PagerDuty
- Security team: security@yourcompany.com
- DevOps team: devops@yourcompany.com

## Contributing

When contributing to these scripts:

1. Test in staging first
2. Add unit tests for new functionality
3. Update this README
4. Document breaking changes
5. Follow Python best practices
6. Add type hints
7. Include error handling

## License

Internal use only - PM Agent system
