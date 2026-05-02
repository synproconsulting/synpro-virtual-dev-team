# Railway Deployment Validation and Alerting

This document describes the Railway GraphQL deployment validation and alerting system implemented in the CI/CD pipeline.

## Overview

The Railway deployment system provides:
- **API Connectivity Validation**: Ensures Railway API is accessible before deployment
- **Deployment Status Monitoring**: Tracks deployment progress and validates success
- **Slack Alerting**: Sends notifications for deployment events (success, failure, warnings)
- **Comprehensive Logging**: Detailed deployment logs for troubleshooting

## Components

### 1. Railway Deploy Validator (`uat/backend/railway_deploy_validator.py`)

Main validation module that interacts with Railway GraphQL API.

**Key Features:**
- Validates Railway API connectivity
- Resolves service and environment IDs from names
- Triggers deployments via GraphQL mutations
- Monitors deployment status with polling
- Returns structured validation results

**Main Class:**
```python
RailwayDeployValidator(railway_token: str, project_id: str)
```

**Key Methods:**
- `validate_api_connectivity()` - Check Railway API is accessible
- `resolve_service_and_environment(service_name, environment_name)` - Get IDs from names
- `trigger_redeploy(service_id, environment_id)` - Trigger deployment
- `validate_deployment_status(service_id, environment_id, timeout_seconds)` - Monitor deployment
- `get_project_info()` - Retrieve project metadata

### 2. Railway Alerting (`uat/backend/railway_alerting.py`)

Slack notification module for deployment events.

**Key Features:**
- Success/failure/warning alerts
- Rich formatted messages with deployment metadata
- API connectivity failure notifications
- Deployment pipeline summaries

**Main Class:**
```python
DeploymentAlert(webhook_url: Optional[str] = None)
```

**Key Methods:**
- `alert_deployment_success(service_name, environment, deployment_id, ...)` - Success notification
- `alert_deployment_failure(service_name, environment, error_message, ...)` - Failure notification
- `alert_validation_warning(message, service_name, details)` - Warning notification
- `alert_api_connectivity_failure(error_message, project_id)` - API issue notification

### 3. Validated Deploy Script (`scripts/deploy_railway_validated.py`)

Orchestration script for validated deployments.

**Usage:**
```bash
python scripts/deploy_railway_validated.py \
  --services synpro-virtual-dev-team Virtual-Dev-Team-UAT-Frontend \
  --environment production \
  --commit-sha abc123 \
  --branch main
```

**Arguments:**
- `--services` - List of service names to deploy (space-separated)
- `--environment` - Target environment (default: production)
- `--no-validate` - Skip deployment status validation (not recommended)
- `--commit-sha` - Git commit SHA for tracking
- `--branch` - Git branch name

**Exit Codes:**
- `0` - All deployments successful
- `1` - One or more deployments failed or validation error

## CI/CD Integration

### GitHub Actions Workflow

The CI pipeline includes two Railway-related jobs:

#### 1. `validate-railway` Job

Runs before deployment to validate Railway API connectivity.

```yaml
validate-railway:
  name: Validate Railway API
  runs-on: ubuntu-latest
  needs: [test, security]
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

**Purpose:**
- Ensures Railway API is accessible
- Validates credentials (RAILWAY_TOKEN, RAILWAY_PROJECT_ID)
- Lists available environments and services
- Fails fast if API is unreachable

#### 2. `deploy` Job

Executes validated deployment with alerting.

```yaml
deploy:
  name: Deploy to Railway
  runs-on: ubuntu-latest
  needs: [test, security, validate-railway]
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

**Features:**
- Deploys multiple services with validation
- Monitors deployment status
- Sends Slack notifications
- Provides deployment summary
- Includes fallback alerting on failure

## Configuration

### Required Environment Variables

**Railway Credentials:**
- `RAILWAY_TOKEN` - Railway API authentication token
- `RAILWAY_PROJECT_ID` - Railway project ID

**Slack Integration (Optional):**
- `SLACK_WEBHOOK_URL` - Slack incoming webhook URL for notifications

### GitHub Secrets

Set these secrets in your GitHub repository settings:

1. **RAILWAY_TOKEN**: Get from Railway dashboard → Project Settings → Tokens
2. **RAILWAY_PROJECT_ID**: Get from Railway project URL or API
3. **SLACK_WEBHOOK_URL**: Create an incoming webhook in Slack workspace settings

## Slack Notifications

### Success Notification

```
✅ Deployment successful for synpro-virtual-dev-team

Service: synpro-virtual-dev-team
Environment: production
Deployment ID: deploy_abc123
Commit: abc123d
Branch: main
```

### Failure Notification

```
❌ Deployment failed for synpro-virtual-dev-team

Service: synpro-virtual-dev-team
Environment: production
Error: Deployment deploy_xyz789 failed with status: FAILED
Deployment ID: deploy_xyz789
Commit: xyz789a
Branch: main
Details:
{
  "error": "Build process failed",
  "code": 500
}
```

### Pipeline Summary

```
✅ Deployment pipeline Success

Successful: 2
Failed: 0
Warnings: 0
Build URL: https://github.com/user/repo/actions/runs/12345
```

## Validation Flow

1. **Pre-Deployment Validation**
   - Check Railway API connectivity
   - Verify credentials are valid
   - List available services and environments

2. **Deployment Trigger**
   - Resolve service and environment IDs from names
   - Trigger redeploy via GraphQL mutation
   - Capture deployment ID

3. **Status Monitoring**
   - Poll deployment status every 10 seconds
   - Check for terminal states (SUCCESS, FAILED, CRASHED)
   - Timeout after 5 minutes (configurable)

4. **Alerting**
   - Send success/failure notifications to Slack
   - Include deployment metadata and build links
   - Provide summary for multi-service deployments

## Error Handling

### API Connectivity Failures

If Railway API is unreachable:
- Validation job fails immediately
- No deployment is attempted
- Slack alert sent with connectivity error
- Exit code 1 returned

### Deployment Failures

If deployment fails:
- Status monitoring detects FAILED/CRASHED state
- Failure alert sent with error details
- Deployment metadata captured in logs
- Exit code 1 returned

### Timeout Handling

If deployment doesn't complete within timeout:
- Validation returns timeout error
- Warning/failure alert sent
- Manual intervention may be required
- Check Railway dashboard for actual status

## Testing

Run the test suite:

```bash
# Test validator
pytest uat/backend/tests/test_railway_validator.py -v

# Test alerting
pytest uat/backend/tests/test_railway_alerting.py -v

# All Railway tests
pytest uat/backend/tests/test_railway*.py -v
```

## Manual Testing

### Test API Connectivity

```bash
export RAILWAY_TOKEN="your_token"
export RAILWAY_PROJECT_ID="your_project_id"

python uat/backend/railway_deploy_validator.py
```

### Test Deployment (Dry Run)

```bash
export RAILWAY_TOKEN="your_token"
export RAILWAY_PROJECT_ID="your_project_id"
export SLACK_WEBHOOK_URL="your_webhook_url"

python scripts/deploy_railway_validated.py \
  --services synpro-virtual-dev-team \
  --environment production \
  --commit-sha $(git rev-parse HEAD) \
  --branch $(git branch --show-current)
```

## Troubleshooting

### Issue: "Railway API error or unreachable"

**Cause:** Network issues or invalid credentials

**Solution:**
1. Verify `RAILWAY_TOKEN` is valid and not expired
2. Check `RAILWAY_PROJECT_ID` matches your project
3. Ensure Railway API is accessible from CI environment
4. Check Railway status page for outages

### Issue: "Could not resolve IDs"

**Cause:** Service or environment name doesn't match Railway

**Solution:**
1. Check service names in Railway dashboard
2. Verify environment name (case-sensitive)
3. Update service names in deployment script
4. Run validation script to list available names

### Issue: "Deployment validation timed out"

**Cause:** Deployment taking longer than expected

**Solution:**
1. Check Railway dashboard for actual deployment status
2. Increase timeout in `validate_deployment_status()` call
3. Review deployment logs for build issues
4. Consider optimizing build process

### Issue: "No Slack notifications received"

**Cause:** Webhook URL not configured or invalid

**Solution:**
1. Verify `SLACK_WEBHOOK_URL` secret is set
2. Test webhook URL with curl
3. Check Slack workspace permissions
4. Verify webhook is enabled in Slack settings

## Best Practices

1. **Always validate before deploying**
   - Don't skip the `validate-railway` job
   - Catch issues early to avoid failed deployments

2. **Monitor deployment status**
   - Use the `--no-validate` flag only for testing
   - Let the validator wait for deployment completion

3. **Configure Slack alerts**
   - Essential for production deployments
   - Enables team visibility into deployment status

4. **Review logs regularly**
   - Check CI logs for warnings
   - Monitor Railway dashboard for issues

5. **Test in staging first**
   - Validate changes in staging environment
   - Use `--environment staging` flag

## Future Enhancements

Potential improvements:

- [ ] Add deployment rollback capability
- [ ] Support multiple Railway projects
- [ ] Add health check validation post-deployment
- [ ] Implement deployment approval workflow
- [ ] Add metrics collection (deployment duration, success rate)
- [ ] Support custom deployment strategies (blue-green, canary)
- [ ] Add Microsoft Teams/Discord webhook support
- [ ] Implement deployment queue for sequential deployments

## References

- [Railway GraphQL API Documentation](https://docs.railway.app/reference/public-api)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
