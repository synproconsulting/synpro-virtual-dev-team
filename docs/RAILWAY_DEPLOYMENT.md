# Railway Deployment Integration

This document describes the Railway GraphQL API integration for UAT deployments (SDT1-58).

## Overview

The UAT Deploy tab in the Control Centre is now wired to Railway's GraphQL API, allowing you to:

- View all services in your Railway project
- Trigger deployments for selected services
- Monitor deployment status in real-time
- View recent deployment history per service
- Access deployment logs

## Architecture

### Backend Components

#### `railway_client.py`
Python client for Railway GraphQL API with methods for:
- `list_services()` - Get all services in a project
- `get_environments()` - Get all environments
- `trigger_deployment()` - Deploy a service to an environment
- `get_deployment_status()` - Check deployment status
- `get_service_deployments()` - Get deployment history for a service
- `get_deployment_logs()` - Fetch deployment logs

#### `deployment_router.py`
FastAPI router providing REST endpoints:
- `GET /api/deployments/services` - List available services
- `GET /api/deployments/environments` - List environments
- `POST /api/deployments/trigger` - Trigger a deployment
- `GET /api/deployments/{deployment_id}` - Get deployment status
- `GET /api/deployments/service/{service_id}/deployments` - Get service deployment history
- `GET /api/deployments/{deployment_id}/logs` - Get deployment logs

### Frontend Components

#### `src/api/deploymentApi.js`
API client for the frontend with functions:
- `getServices()` - Fetch available services
- `getEnvironments()` - Fetch environments
- `triggerDeployment()` - Trigger a deployment
- `getDeploymentStatus()` - Poll deployment status
- `getServiceDeployments()` - Get deployment history

#### `src/components/UATDeployment.jsx`
React component providing:
- Service selection with checkboxes
- Environment picker
- Custom branch input (optional)
- Deployment notes field
- Real-time deployment status updates
- Recent deployment history per service

## Setup

### 1. Get Railway API Credentials

1. Log in to [Railway Dashboard](https://railway.app/)
2. Go to **Account Settings > Tokens**
3. Create a new API token and copy it
4. Navigate to your project settings to get:
   - Project ID (from URL or settings)
   - Environment IDs (from environment settings)

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Railway Configuration
RAILWAY_API_TOKEN=your-railway-api-token-here
RAILWAY_PROJECT_ID=your-railway-project-id
RAILWAY_UAT_ENVIRONMENT_ID=your-uat-environment-id
```

For production deployment on Railway, set these as environment variables in the Railway dashboard.

### 3. Test the Integration

Start the backend:
```bash
cd uat/backend
uvicorn main:app --reload
```

Start the frontend:
```bash
cd control-centre
npm run dev
```

Navigate to the **UAT Deploy** tab to see your Railway services.

## Usage

### Deploying Services

1. Select one or more services from the list
2. (Optional) Choose a different environment (defaults to UAT)
3. (Optional) Enter a custom branch name to deploy from
4. (Optional) Add deployment notes
5. Click **Deploy** to trigger the deployment(s)

### Monitoring Deployments

- The UI automatically polls for deployment status updates
- Status badges show current state:
  - 🟢 **SUCCESS** - Deployment completed successfully
  - 🟡 **BUILDING/DEPLOYING** - In progress
  - 🔴 **FAILED/CRASHED** - Deployment failed
- Recent deployments are shown under each selected service

### Viewing Deployment Details

After triggering a deployment, you'll see:
- Deployment ID
- Current status
- Triggered timestamp
- Static URL (if available)
- Link to view logs (coming soon)

## API Reference

### Trigger Deployment

**Endpoint:** `POST /api/deployments/trigger`

**Request Body:**
```json
{
  "service_id": "service-uuid",
  "environment_id": "env-uuid",  // optional, defaults to RAILWAY_UAT_ENVIRONMENT_ID
  "custom_branch": "feature/xyz", // optional
  "notes": "Deployment notes"     // optional
}
```

**Response:**
```json
{
  "deployment_id": "deployment-uuid",
  "status": "BUILDING",
  "service_id": "service-uuid",
  "environment_id": "env-uuid",
  "triggered_at": "2024-01-15T10:00:00Z",
  "static_url": "https://app.railway.app",
  "message": "Deployment triggered successfully"
}
```

### Get Services

**Endpoint:** `GET /api/deployments/services`

**Response:**
```json
{
  "services": [
    {
      "id": "service-uuid",
      "name": "API Service",
      "icon": "nodejs",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 1
}
```

### Get Deployment Status

**Endpoint:** `GET /api/deployments/{deployment_id}`

**Response:**
```json
{
  "deployment": {
    "id": "deployment-uuid",
    "status": "SUCCESS",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:05:00Z",
    "static_url": "https://app.railway.app",
    "can_rollback": true,
    "can_redeploy": true,
    "environment": {
      "id": "env-uuid",
      "name": "UAT"
    },
    "service": {
      "id": "service-uuid",
      "name": "API Service"
    }
  },
  "message": "Deployment status: SUCCESS"
}
```

## Railway GraphQL Schema

The integration uses Railway's GraphQL API v2. Key queries used:

### List Services
```graphql
query ListServices($projectId: String!) {
  project(id: $projectId) {
    services {
      edges {
        node {
          id
          name
          icon
        }
      }
    }
  }
}
```

### Trigger Deployment
```graphql
mutation DeployService($serviceId: String!, $environmentId: String!) {
  serviceDeploy(input: {serviceId: $serviceId, environmentId: $environmentId}) {
    id
    status
    createdAt
    staticUrl
  }
}
```

### Get Deployment Status
```graphql
query GetDeployment($deploymentId: String!) {
  deployment(id: $deploymentId) {
    id
    status
    createdAt
    updatedAt
    staticUrl
    environment {
      id
      name
    }
    service {
      id
      name
    }
  }
}
```

## Error Handling

The integration includes comprehensive error handling:

### Backend Errors
- `RailwayAPIError` - Raised for Railway API failures
- HTTP 502 - Railway API unavailable or returned error
- HTTP 500 - Internal server error
- HTTP 404 - Deployment not found

### Frontend Errors
All errors are caught and displayed to the user with actionable messages.

### Common Issues

**"RAILWAY_API_TOKEN environment variable is not configured"**
- Solution: Set the `RAILWAY_API_TOKEN` environment variable

**"Failed to fetch services from Railway"**
- Check that your API token is valid
- Verify project ID is correct
- Ensure token has appropriate permissions

**"Failed to trigger deployment"**
- Verify service ID is correct
- Check environment ID is valid
- Ensure Railway project is active

## Testing

Run the backend tests:
```bash
cd uat/backend
pytest tests/test_railway_client.py -v
```

Tests cover:
- Client initialization
- GraphQL query execution
- All API methods
- Error handling
- Environment variable configuration

## Security Considerations

1. **API Token Security**
   - Never commit Railway API tokens to version control
   - Use environment variables only
   - Rotate tokens periodically
   - Use Railway's role-based access control

2. **Rate Limiting**
   - Railway API has rate limits
   - The client includes timeout handling
   - Consider implementing request throttling for high-volume usage

3. **Authentication**
   - Currently, deployment endpoints don't require authentication
   - Consider adding authentication middleware for production use

## Future Enhancements

Potential improvements for future iterations:

- [ ] Deployment rollback functionality
- [ ] Real-time log streaming via WebSocket
- [ ] Deployment approval workflow
- [ ] Slack/email notifications on deployment status
- [ ] Deployment metrics and history dashboard
- [ ] Support for multi-region deployments
- [ ] Automated rollback on health check failures
- [ ] Deployment scheduling (e.g., deploy at specific time)

## References

- [Railway GraphQL API Documentation](https://docs.railway.app/reference/public-api)
- [Railway Dashboard](https://railway.app/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## Support

For issues or questions:
1. Check Railway status page for API availability
2. Review backend logs for detailed error messages
3. Verify all environment variables are set correctly
4. Consult Railway API documentation for schema changes
