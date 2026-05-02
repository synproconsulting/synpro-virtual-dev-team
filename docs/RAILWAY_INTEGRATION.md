# Railway Integration Documentation

## Overview

The UAT Deploy tab in the Control Centre provides real-time monitoring and management of Railway deployments through Railway's GraphQL API. This integration allows the team to monitor deployment status, view logs, and trigger new deployments directly from the Control Centre.

## Architecture

### Backend Components

1. **`railway_client.py`** - Railway GraphQL API client
   - Handles authentication with Railway API
   - Executes GraphQL queries and mutations
   - Provides methods for fetching projects, services, deployments, and logs
   - Triggers new deployments

2. **`railway_router.py`** - FastAPI router with REST endpoints
   - `/api/railway/projects` - Get all accessible projects
   - `/api/railway/projects/{project_id}/services` - Get services in a project
   - `/api/railway/services/{service_id}/deployments` - Get service deployments
   - `/api/railway/projects/{project_id}/environments/{environment_name}/deployments` - Get environment deployments
   - `/api/railway/deployments/{deployment_id}/logs` - Get deployment logs
   - `/api/railway/deployments/trigger` - Trigger a new deployment
   - `/api/railway/health` - Check Railway API health

### Frontend Components

1. **`UATDeployment.jsx`** - React component for the UAT Deploy tab
   - Displays Railway projects and environments
   - Shows deployment status cards with real-time updates
   - Auto-refresh functionality (30-second interval)
   - Environment selection (production, staging, UAT, development)

2. **`railway.js`** - API client for frontend-backend communication
   - Wraps all Railway API endpoints
   - Handles error responses
   - Formats deployment status for display

## Configuration

### Backend Configuration

Add the following to `uat/backend/.env`:

```bash
# Railway API token - get from https://railway.app/account/tokens
RAILWAY_API_TOKEN=your-railway-api-token-here
```

**Getting your Railway API token:**
1. Log in to [Railway](https://railway.app)
2. Go to Account Settings → Tokens
3. Create a new token with the following permissions:
   - Read projects, services, and deployments
   - Trigger deployments
4. Copy the token and add it to your `.env` file

### Frontend Configuration

Add the following to `control-centre/.env`:

```bash
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# Optional: Default Railway project ID to auto-select
VITE_RAILWAY_PROJECT_ID=your-railway-project-id-here
```

**Finding your Railway project ID:**
1. Open your project in Railway
2. Go to Settings
3. Copy the Project ID from the project settings

## Usage

### Monitoring Deployments

1. Navigate to the **UAT Deploy** tab in the Control Centre
2. Select your project from the dropdown
3. Choose the environment (production, staging, UAT, development)
4. View deployment status cards showing:
   - Service name
   - Deployment status (with color-coded badges)
   - Deployment ID
   - Creation and update timestamps
   - Service URL (if available)

### Auto-Refresh

Enable auto-refresh to automatically update deployment status every 30 seconds:
- Check the "Auto-refresh (30s)" checkbox
- The display will refresh silently in the background
- Last refresh timestamp is shown at the top

### Triggering Deployments

Use the `/api/railway/deployments/trigger` endpoint to trigger new deployments:

```bash
curl -X POST http://localhost:8000/api/railway/deployments/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "your-service-id",
    "environment_id": "your-environment-id"
  }'
```

## Deployment Status Reference

The integration recognizes the following Railway deployment statuses:

| Status | Color | Description |
|--------|-------|-------------|
| SUCCESS | Green (#22c55e) | Deployment completed successfully |
| ACTIVE | Green (#10b981) | Deployment is active and running |
| BUILDING | Blue (#3b82f6) | Building the deployment |
| DEPLOYING | Purple (#8b5cf6) | Deploying to Railway |
| INITIALIZING | Cyan (#06b6d4) | Initializing deployment |
| WAITING | Orange (#f59e0b) | Waiting in queue |
| FAILED | Red (#ef4444) | Deployment failed |
| CRASHED | Red (#dc2626) | Deployment crashed |
| REMOVING | Gray (#9ca3af) | Removing deployment |
| REMOVED | Gray (#6b7280) | Deployment removed |

## API Reference

### Get Projects

```http
GET /api/railway/projects
```

Returns all Railway projects accessible to the configured API token.

**Response:**
```json
{
  "projects": [
    {
      "id": "project-id",
      "name": "Project Name",
      "description": "Project description",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Get Project Services

```http
GET /api/railway/projects/{project_id}/services
```

Returns all services in a specific project.

### Get Service Deployments

```http
GET /api/railway/services/{service_id}/deployments?environment_id=env1&limit=10
```

Returns recent deployments for a service, optionally filtered by environment.

**Query Parameters:**
- `environment_id` (optional) - Filter by environment ID
- `limit` (optional, default: 10, max: 50) - Number of deployments to return

### Get Environment Deployments

```http
GET /api/railway/projects/{project_id}/environments/{environment_name}/deployments
```

Returns all deployments for all services in a specific environment.

**Path Parameters:**
- `project_id` - Railway project ID
- `environment_name` - Environment name (e.g., "production", "staging", "uat")

**Response:**
```json
{
  "environment": "production",
  "deployments": [
    {
      "id": "deployment-id",
      "status": "SUCCESS",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:01:00Z",
      "staticUrl": "https://service.railway.app",
      "serviceId": "service-id",
      "serviceName": "API Service"
    }
  ]
}
```

### Get Deployment Logs

```http
GET /api/railway/deployments/{deployment_id}/logs?limit=100
```

Returns logs for a specific deployment.

**Query Parameters:**
- `limit` (optional, default: 100, max: 500) - Number of log entries to return

### Trigger Deployment

```http
POST /api/railway/deployments/trigger
Content-Type: application/json

{
  "service_id": "service-id",
  "environment_id": "environment-id"
}
```

Triggers a new deployment for a service in a specific environment.

**Response:**
```json
{
  "success": true,
  "deployment": {
    "id": "deployment-id",
    "status": "INITIALIZING",
    "createdAt": "2024-01-01T00:00:00Z"
  },
  "message": "Deployment triggered successfully"
}
```

### Health Check

```http
GET /api/railway/health
```

Checks if Railway API is configured and accessible.

**Response:**
```json
{
  "status": "healthy",
  "configured": true,
  "projects_count": 5
}
```

Possible statuses:
- `healthy` - Railway API is configured and accessible
- `unconfigured` - RAILWAY_API_TOKEN not set
- `unhealthy` - Configured but unable to connect to Railway API

## Error Handling

### Backend Errors

All Railway API endpoints return standard HTTP error responses:

- **500 Internal Server Error** - Railway API not configured or API error
  ```json
  {
    "detail": "Railway API not configured"
  }
  ```
  or
  ```json
  {
    "detail": "Failed to fetch projects: <error message>"
  }
  ```

- **422 Unprocessable Entity** - Invalid request payload
  ```json
  {
    "detail": [
      {
        "loc": ["body", "service_id"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ]
  }
  ```

### Frontend Error Handling

The UATDeployment component displays errors in a red alert banner:
- Connection errors to backend
- Railway API configuration errors
- Failed API requests

## Testing

### Backend Tests

Run the Railway integration tests:

```bash
cd uat/backend
pytest tests/test_railway_client.py -v
pytest tests/test_railway_router.py -v
```

### Manual Testing

1. **Test Railway API connection:**
   ```bash
   curl http://localhost:8000/api/railway/health
   ```

2. **Test project listing:**
   ```bash
   curl http://localhost:8000/api/railway/projects
   ```

3. **Test environment deployments:**
   ```bash
   curl http://localhost:8000/api/railway/projects/PROJECT_ID/environments/production/deployments
   ```

## Troubleshooting

### Railway API not configured

**Error:** "Railway API is not configured. Please set RAILWAY_API_TOKEN environment variable."

**Solution:**
1. Ensure `RAILWAY_API_TOKEN` is set in `uat/backend/.env`
2. Restart the backend server
3. Verify the token is valid by checking the health endpoint

### No deployments showing

**Issue:** Projects load but no deployments appear

**Solutions:**
1. Verify the environment name matches your Railway environments
2. Check that the project has services deployed to the selected environment
3. Review backend logs for API errors

### Connection timeout

**Issue:** Requests to Railway API timeout

**Solutions:**
1. Check your internet connection
2. Verify Railway API is not experiencing downtime (check Railway status page)
3. Increase the timeout in `railway_client.py` if needed (default: 30 seconds)

### Invalid GraphQL query errors

**Issue:** GraphQL errors in backend logs

**Solutions:**
1. Ensure your Railway API token has the required permissions
2. Check that the token hasn't expired
3. Review the Railway GraphQL schema for any API changes

## Security Considerations

1. **API Token Security**
   - Never commit the `RAILWAY_API_TOKEN` to version control
   - Use environment variables for all sensitive configuration
   - Rotate tokens regularly (recommended: every 90 days)
   - Use Railway's token permissions to limit access scope

2. **CORS Configuration**
   - Backend CORS is configured via `FRONTEND_URL` in `.env`
   - Only allow trusted frontend origins in production

3. **Rate Limiting**
   - Railway API has rate limits - implement caching if needed
   - Auto-refresh is limited to 30-second intervals to avoid excessive requests

## Future Enhancements

Possible improvements to the Railway integration:

1. **Deployment Logs Viewer** - Add a modal to view full deployment logs
2. **Deployment History** - Show deployment history timeline
3. **Multi-environment Comparison** - Compare deployments across environments
4. **Deployment Metrics** - Show build time, deployment duration, etc.
5. **Rollback Functionality** - Quick rollback to previous deployment
6. **Notification Integration** - Alert on deployment failures
7. **Manual Deployment Triggers** - UI buttons to trigger deployments from Control Centre

## Related Documentation

- [Railway GraphQL API Documentation](https://docs.railway.app/reference/public-api)
- [Railway Deployments Guide](https://docs.railway.app/guides/deployments)
- UAT Backend API Documentation: `uat/backend/README.md`
- Control Centre Documentation: `control-centre/README.md`

## Support

For issues or questions:
1. Check this documentation first
2. Review backend logs: `uat/backend/logs/`
3. Check Railway status: https://status.railway.app
4. Contact the development team
