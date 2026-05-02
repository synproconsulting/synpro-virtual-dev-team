# Railway GraphQL Deploy - Validation & Alerting

## Overview

This document describes the CI/CD validation and alerting system for Railway GraphQL deployments. The system ensures deployment reliability through automated validation, health checks, and proactive alerting.

## Architecture

The validation system consists of several components:

1. **GraphQL Schema Validation** - Validates all GraphQL queries against Railway's API schema
2. **Integration Testing** - Tests Railway API client functionality
3. **Health Monitoring** - Checks deployment health status
4. **Metrics Collection** - Gathers deployment statistics and trends
5. **Alerting** - Notifies team of failures via GitHub Issues and Slack

## Components

### 1. GitHub Actions Workflow

**File**: `.github/workflows/railway-deploy-validation.yml`

The workflow runs on:
- Push to `main` branch (affects `uat/backend/`)
- Pull requests to `main`
- Manual dispatch

**Jobs**:

#### `validate-graphql-schema`
- Validates GraphQL query syntax
- Ensures compatibility with Railway API schema
- Creates GitHub issue on validation failure

#### `test-railway-integration`
- Runs comprehensive API integration tests
- Uploads code coverage to Codecov
- Creates GitHub issue on test failure

#### `validate-deployment-health`
- Checks current deployment status
- Identifies failed or degraded deployments
- Sends Slack alert on unhealthy deployments

#### `deployment-metrics`
- Collects deployment statistics
- Generates metrics report
- Posts summary as commit comment

#### `notify-success`
- Sends Slack notification on successful validation
- Only runs for `main` branch

### 2. GraphQL Validation Tests

**File**: `uat/backend/tests/test_railway_graphql_validation.py`

Validates:
- GraphQL query syntax correctness
- Query structure and variable usage
- Field selections against schema
- Security (no hardcoded IDs, proper parameterization)
- Performance (pagination, field optimization)

**Test Classes**:
- `TestGraphQLQueryValidation` - Validates all queries against schema
- `TestRailwayAPIConnectivity` - Tests live API connectivity (requires token)
- `TestGraphQLQueryStructure` - Validates query best practices
- `TestErrorHandling` - Tests error handling patterns
- `TestQueryPerformance` - Ensures queries are optimized

### 3. Health Check Script

**File**: `uat/backend/scripts/check_railway_health.py`

**Purpose**: Validates Railway deployment health and alerts on issues.

**Features**:
- Checks deployment status for all services
- Identifies failed, degraded, or in-progress deployments
- Detects multiple recent failures
- Sends alerts via webhook
- Generates JSON report for CI artifacts

**Health Statuses**:
- `HEALTHY` - Latest deployment successful
- `DEGRADED` - Deployment in progress or minor issues
- `UNHEALTHY` - Deployment failed or multiple recent failures
- `UNKNOWN` - Unable to determine status

**Usage**:
```bash
export RAILWAY_API_TOKEN="your-token"
export RAILWAY_PROJECT_ID="your-project-id"
export RAILWAY_SERVICE_ID="optional-specific-service"
export ALERT_WEBHOOK_URL="optional-slack-webhook"

python scripts/check_railway_health.py
```

**Exit Codes**:
- `0` - All services healthy
- `1` - Unhealthy services detected or error

### 4. Metrics Collection Script

**File**: `uat/backend/scripts/collect_deployment_metrics.py`

**Purpose**: Collects deployment metrics for monitoring and analysis.

**Metrics Collected**:
- Total deployments (per service and project-wide)
- Success/failure counts
- Success rate percentage
- Average build time
- Min/max build times
- Status breakdown (building, deployed, failed, etc.)
- Latest deployment info

**Usage**:
```bash
export RAILWAY_API_TOKEN="your-token"
export RAILWAY_PROJECT_ID="your-project-id"

python scripts/collect_deployment_metrics.py
```

**Output**:
- Console: Human-readable summary report
- File: `metrics.json` with detailed statistics

**Lookback Period**: Default 30 days (configurable)

## Configuration

### Required Secrets

Configure these secrets in GitHub repository settings:

#### Required for all jobs:
- `RAILWAY_API_TOKEN` - Railway API authentication token
  - Generate at: https://railway.app/account/tokens

#### Required for health checks:
- `RAILWAY_PROJECT_ID` - Railway project ID to monitor
- `RAILWAY_SERVICE_ID` - (Optional) Specific service to monitor

#### Optional for alerting:
- `SLACK_WEBHOOK_URL` - Slack incoming webhook URL for alerts
  - Create at: https://api.slack.com/messaging/webhooks

### Environment Variables

The scripts use the following environment variables:

```bash
# Required
RAILWAY_API_TOKEN=your_railway_api_token
RAILWAY_PROJECT_ID=your_project_id

# Optional
RAILWAY_SERVICE_ID=specific_service_id  # If omitted, checks all services
ALERT_WEBHOOK_URL=https://hooks.slack.com/...  # For Slack notifications
```

## Alerting

### GitHub Issues

On validation or test failures, the system automatically creates GitHub issues with:
- Workflow run details
- Commit information
- Action items checklist
- Relevant labels for filtering

**Labels**:
- `railway-validation-failure` - GraphQL validation failed
- `railway-test-failure` - Integration tests failed
- `ci-alert` - CI/CD alert
- `bug` - Bug/issue tag

### Slack Notifications

The system sends Slack notifications for:

**Failure Notifications** (always):
- Unhealthy deployment detected
- Contains service details and workflow link
- Interactive "View Workflow" button

**Success Notifications** (main branch only):
- All validations passed
- Deployment health check successful

**Notification Format**:
```
⚠️ Railway Deployment Health Check Failed

Repository: owner/repo
Workflow: Railway GraphQL Deploy - Validation & Alerting
Commit: abc1234
Author: username

Railway deployment health check has failed. One or more deployments may be in a failed state.

[View Workflow]
```

## Monitoring Dashboard

### Deployment Metrics

Metrics are collected and stored as CI artifacts:

**Artifact**: `deployment-metrics`
- Retention: 30 days
- Format: JSON
- Location: GitHub Actions run artifacts

**Contents**:
```json
{
  "project_id": "...",
  "timestamp": "2024-01-15T10:30:00Z",
  "total_services": 5,
  "total_deployments": 120,
  "successful_deployments": 115,
  "failed_deployments": 5,
  "overall_success_rate": 95.83,
  "avg_build_time_seconds": 145.6,
  "services": [...]
}
```

### Commit Comments

For each successful validation on `main`, the system posts deployment metrics as a commit comment:

```
📊 Railway Deployment Metrics

Total Deployments: 120
Successful: 115
Failed: 5
Success Rate: 95.83%

Average Build Time: 2.4 minutes
Latest Deployment: SUCCESS

_Metrics collected from the last 30 days_
```

## Troubleshooting

### Common Issues

#### 1. GraphQL Validation Failures

**Symptom**: `validate-graphql-schema` job fails

**Possible Causes**:
- Railway API schema changed
- Query syntax error
- Missing or deprecated fields

**Resolution**:
1. Review workflow logs for specific errors
2. Check Railway API documentation for schema changes
3. Update queries in `railway_api.py`
4. Run validation tests locally:
   ```bash
   cd uat/backend
   pytest tests/test_railway_graphql_validation.py -v
   ```

#### 2. API Token Issues

**Symptom**: "Unauthorized" errors or "Railway API token not provided"

**Possible Causes**:
- Token not configured in secrets
- Token expired or revoked
- Insufficient permissions

**Resolution**:
1. Verify `RAILWAY_API_TOKEN` is set in GitHub secrets
2. Generate new token at Railway dashboard
3. Ensure token has required permissions (read projects, deployments)

#### 3. Health Check Failures

**Symptom**: `validate-deployment-health` job fails

**Possible Causes**:
- Actual deployment failure (expected alert)
- Project/service ID misconfigured
- API connectivity issues

**Resolution**:
1. Check Railway dashboard for actual deployment status
2. Verify `RAILWAY_PROJECT_ID` is correct
3. Review health check script output in workflow logs
4. Run health check locally:
   ```bash
   export RAILWAY_API_TOKEN="..."
   export RAILWAY_PROJECT_ID="..."
   python scripts/check_railway_health.py
   ```

#### 4. Slack Notifications Not Sending

**Symptom**: No Slack messages despite failures

**Possible Causes**:
- `SLACK_WEBHOOK_URL` not configured
- Invalid webhook URL
- Webhook expired or revoked

**Resolution**:
1. Verify `SLACK_WEBHOOK_URL` is set in GitHub secrets
2. Test webhook manually:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test message"}' \
     YOUR_WEBHOOK_URL
   ```
3. Regenerate webhook if necessary

## Best Practices

### For Developers

1. **Run validation locally before pushing**:
   ```bash
   cd uat/backend
   pytest tests/test_railway_graphql_validation.py -v
   pytest tests/test_railway_api.py -v
   ```

2. **Monitor GitHub Actions**:
   - Check workflow status on PRs
   - Review failure notifications
   - Address issues promptly

3. **Update queries carefully**:
   - Always validate against schema
   - Use variables (never string interpolation)
   - Request only needed fields

### For Operations

1. **Monitor Slack channel**:
   - Configure dedicated #railway-alerts channel
   - Set up appropriate notification preferences
   - Respond to alerts quickly

2. **Review metrics regularly**:
   - Check success rates weekly
   - Identify trends in build times
   - Investigate repeated failures

3. **Keep tokens secure**:
   - Rotate tokens periodically
   - Use repository secrets (never commit tokens)
   - Limit token permissions to required scope

## Testing

### Local Testing

**GraphQL Validation**:
```bash
cd uat/backend
pytest tests/test_railway_graphql_validation.py -v
```

**API Integration** (requires token):
```bash
export RAILWAY_API_TOKEN="your-token"
pytest tests/test_railway_api.py -v --cov=railway_api
```

**Health Check**:
```bash
export RAILWAY_API_TOKEN="your-token"
export RAILWAY_PROJECT_ID="your-project-id"
python scripts/check_railway_health.py
```

**Metrics Collection**:
```bash
export RAILWAY_API_TOKEN="your-token"
export RAILWAY_PROJECT_ID="your-project-id"
python scripts/collect_deployment_metrics.py
```

### Manual Workflow Trigger

To manually run the validation workflow:

1. Go to GitHub Actions tab
2. Select "Railway GraphQL Deploy - Validation & Alerting"
3. Click "Run workflow"
4. Select branch and click "Run workflow"

## Maintenance

### Regular Tasks

**Weekly**:
- Review deployment metrics
- Check for recurring failures
- Verify alert delivery

**Monthly**:
- Review and close resolved GitHub issues
- Update Railway API schema in tests if needed
- Audit token permissions

**Quarterly**:
- Review and optimize queries
- Update dependencies
- Test disaster recovery procedures

## Related Documentation

- [Railway API Documentation](https://docs.railway.app/reference/public-api)
- [Railway GraphQL Explorer](https://railway.app/graphql)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)

## Support

For issues or questions:
1. Check this documentation
2. Review GitHub workflow logs
3. Check Railway status page
4. Contact DevOps team

## Changelog

### Version 1.0.0 (SDT1-67)
- Initial implementation
- GraphQL schema validation
- Railway API integration tests
- Health check monitoring
- Deployment metrics collection
- GitHub Issues alerting
- Slack notifications
- Comprehensive documentation
