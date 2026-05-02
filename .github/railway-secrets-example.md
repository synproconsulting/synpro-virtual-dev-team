# Railway Deployment Validation - GitHub Secrets Configuration

This document describes how to configure GitHub Secrets for the Railway deployment validation workflow.

## Required Secrets

### RAILWAY_API_TOKEN

**Required**: Yes  
**Description**: Railway API authentication token for accessing Railway's GraphQL API.

**How to obtain**:
1. Log in to [Railway](https://railway.app)
2. Go to Account Settings → [API Tokens](https://railway.app/account/tokens)
3. Click "Create Token"
4. Give it a descriptive name (e.g., "GitHub Actions CI")
5. Copy the generated token immediately (it won't be shown again)

**Permissions needed**: Read access to projects, services, deployments, and environments

**How to configure in GitHub**:
1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `RAILWAY_API_TOKEN`
5. Value: Paste your Railway API token
6. Click "Add secret"

---

### RAILWAY_PROJECT_ID

**Required**: Yes (for health checks and metrics)  
**Description**: The Railway project ID to monitor for deployments.

**How to obtain**:
1. Log in to [Railway](https://railway.app)
2. Navigate to your project
3. The project ID is in the URL: `https://railway.app/project/{PROJECT_ID}`
4. Or use the Railway CLI: `railway project`

**How to configure in GitHub**:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `RAILWAY_PROJECT_ID`
4. Value: Your Railway project ID (e.g., `abc123de-f456-7890-ghij-klmnop123456`)
5. Click "Add secret"

---

### RAILWAY_SERVICE_ID

**Required**: No (optional)  
**Description**: Specific Railway service ID to monitor. If not set, all services in the project will be monitored.

**How to obtain**:
1. Log in to [Railway](https://railway.app)
2. Navigate to your project → specific service
3. The service ID is in the URL: `https://railway.app/project/{PROJECT_ID}/service/{SERVICE_ID}`
4. Or use Railway CLI: `railway service`

**How to configure in GitHub**:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `RAILWAY_SERVICE_ID`
4. Value: Your Railway service ID (optional)
5. Click "Add secret"

---

### SLACK_WEBHOOK_URL

**Required**: No (optional, but recommended)  
**Description**: Slack incoming webhook URL for sending deployment alerts.

**How to obtain**:
1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Give it a name (e.g., "Railway Deployment Alerts") and select your workspace
4. Navigate to "Incoming Webhooks" in the left sidebar
5. Toggle "Activate Incoming Webhooks" to On
6. Click "Add New Webhook to Workspace"
7. Select the channel where alerts should be posted (recommend creating `#railway-alerts`)
8. Click "Allow"
9. Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

**How to configure in GitHub**:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `SLACK_WEBHOOK_URL`
4. Value: Paste your Slack webhook URL
5. Click "Add secret"

---

## Verification

After configuring all secrets, verify they're set correctly:

1. Go to Settings → Secrets and variables → Actions
2. You should see:
   - ✅ `RAILWAY_API_TOKEN`
   - ✅ `RAILWAY_PROJECT_ID`
   - ✅ `RAILWAY_SERVICE_ID` (optional)
   - ✅ `SLACK_WEBHOOK_URL` (optional)

## Testing

To test that secrets are configured correctly:

1. Go to Actions tab
2. Select "Railway GraphQL Deploy - Validation & Alerting" workflow
3. Click "Run workflow" → Select branch → "Run workflow"
4. Monitor the workflow run

Expected results:
- ✅ All jobs complete successfully
- ✅ (If Slack configured) Success notification in Slack channel
- ✅ Deployment metrics posted as commit comment

## Security Best Practices

### Rotating Secrets

**Railway API Token**:
- Rotate every 90 days
- Immediately rotate if compromised
- Delete old tokens after rotation

**Slack Webhook**:
- Rotate if compromised
- Can be regenerated without creating new app

### Access Control

- Limit who can view/edit repository secrets (Settings → Manage access)
- Use repository-level secrets (not organization-level) for project-specific tokens
- Enable "Require approval for all outside collaborators" for workflow runs

### Monitoring

- Review GitHub Actions logs for unauthorized access attempts
- Monitor Railway audit logs for API token usage
- Set up Slack alerts for unusual deployment patterns

## Troubleshooting

### "RAILWAY_API_TOKEN not set" error

**Problem**: Workflow fails with environment variable not found.

**Solutions**:
1. Verify secret name is exactly `RAILWAY_API_TOKEN` (case-sensitive)
2. Ensure secret is set at repository level, not organization level
3. Re-run the workflow (secrets may take a moment to propagate)

### "Unauthorized" or "Invalid token" error

**Problem**: Railway API rejects the token.

**Solutions**:
1. Verify token was copied correctly (no extra spaces)
2. Check token hasn't expired (regenerate if needed)
3. Ensure token has required permissions
4. Generate new token and update secret

### Slack notifications not arriving

**Problem**: No Slack messages despite workflow completion.

**Solutions**:
1. Verify `SLACK_WEBHOOK_URL` is set correctly
2. Test webhook manually:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test message"}' \
     YOUR_WEBHOOK_URL
   ```
3. Check webhook hasn't been revoked
4. Verify channel still exists and app has permissions
5. Regenerate webhook if needed

### "Project not found" error

**Problem**: Railway API can't find the specified project.

**Solutions**:
1. Verify `RAILWAY_PROJECT_ID` is correct
2. Ensure API token has access to the project
3. Check project hasn't been deleted or moved

## Additional Resources

- [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Railway API Documentation](https://docs.railway.app/reference/public-api)
- [Slack Incoming Webhooks Guide](https://api.slack.com/messaging/webhooks)
- [Railway Security Best Practices](https://docs.railway.app/reference/security)

## Support

If you continue to experience issues after following this guide:

1. Check the workflow logs in GitHub Actions
2. Review the Railway deployment validation documentation
3. Contact your DevOps team
4. Open an issue in the repository

---

**Last Updated**: 2024-01-15  
**Related**: SDT1-67 - Railway GraphQL deploy - add validation and alerting in CI
