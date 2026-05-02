# Railway GraphQL API Integration

## Overview

This document describes the integration of Railway's GraphQL API with the SynPro Control Centre UAT deployment system (SDT1-58).

## Architecture

### Backend Components

1. **`railway_api.py`** - Railway GraphQL API client
   - Handles authentication and GraphQL query execution
   - Provides methods for projects, services, environments, and deployments
   - Full async/await support with httpx

2. **`railway_router.py`** - FastAPI router for Railway operations
   - RESTful endpoints wrapping Railway GraphQL API
   - Authentication required for all endpoints
   - Error handling and logging

3. **Integration in `main.py`**
   - Railway router registered at `/api/railway`
   - Available alongside other API routers

### Frontend Components

1. **`railwayApi.js`** - Frontend API client
   - Abstracts backend Railway API calls
   - Token management via localStorage
   - Error handling

2. **`UATDeployment.jsx`** - React component
   - UI for Railway deployment management
   - Real-time deployment status polling
   - Multi-service deployment support

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Railway API token - get from https://railway.app/account/tokens
RAILWAY_API_TOKEN=your-railway-api-token-here

# Optional: Default project ID
RAILWAY_PROJECT_ID=your-default-project-id
```

### Getting a Railway API Token

1. Log in to [Railway](https://railway.app)
2. Go to [Account Settings > Tokens](https://railway.app/account/tokens)
3. Click "Create Token"
4. Copy the token and add it to your `.env` file

**⚠️ Security Note:** Never commit your Railway API token to version control. Keep it in `.env` which should be in `.gitignore`.

## API Endpoints

### Backend Endpoints

All endpoints require authentication via Bearer token.

#### Get Projects
```http
GET /api/railway/projects
```

Returns all Railway projects accessible by the configured API token.

**Response:**
```json
[
  {
    "id": "project-uuid",
    "name": "My Project",
    "description": "Project description",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Get Project Services
```http
GET /api/railway/projects/{project_id}/services
```

Returns all services in a project.

**Response:**
```json
[
  {
    "id": "service-uuid",
    "name": "API Service",
    "icon": "🚀",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Get Project Environments
```http
GET /api/railway/projects/{project_id}/environments
```

Returns all environments in a project.

**Response:**
```json
[
  {
    "id": "environment-uuid",
    "name": "production",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Get Service Deployments
```http
GET /api/railway/services/{service_id}/deployments?limit=10
```

Returns recent deployments for a service.

**Response:**
```json
[
  {
    "id": "deployment-uuid",
    "status": "SUCCESS",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:05:00Z",
    "static_url": "https://example.railway.app",
    "meta": {}
  }
]
```

#### Trigger Deployment
```http
POST /api/railway/deployments/trigger
Content-Type: application/json

{
  "service_id": "service-uuid",
  "environment_id": "environment-uuid"
}
```

Triggers a new deployment for the specified service and environment.

**Response:**
```json
{
  "id": "deployment-uuid",
  "status": "QUEUED",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get Deployment Status
```http
GET /api/railway/deployments/{deployment_id}
```

Returns the current status of a deployment.

**Response:**
```json
{
  "id": "deployment-uuid",
  "status": "BUILDING",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:02:00Z",
  "static_url": null,
  "meta": {}
}
```

#### Get Service Variables
```http
GET /api/railway/services/{service_id}/variables?environment_id={env_id}
```

Returns environment variables for a service. Note: Some values may be redacted by Railway.

**Response:**
```json
{
  "variables": {
    "DATABASE_URL": "postgres://...",
    "API_KEY": "***",
    "PORT": "8000"
  }
}
```

#### Health Check
```http
GET /api/railway/health
```

Checks if Railway API token is configured.

**Response:**
```json
{
  "status": "healthy",
  "message": "Railway API configured"
}
```

## Deployment Statuses

Railway deployments can have the following statuses:

- **QUEUED** - Deployment is queued and waiting to start
- **INITIALIZING** - Deployment is initializing
- **BUILDING** - Building the service
- **DEPLOYING** - Deploying the built service
- **ACTIVE** - Deployment is active and running
- **SUCCESS** - Deployment completed successfully
- **FAILED** - Deployment failed
- **CRASHED** - Deployment crashed after starting

## Frontend Usage

### Basic Deployment Flow

```javascript
import {
  getRailwayProjects,
  getProjectServices,
  getProjectEnvironments,
  triggerDeployment,
  getDeploymentStatus
} from '../api/railwayApi';

// 1. Load projects
const projects = await getRailwayProjects();

// 2. Load services and environments for a project
const services = await getProjectServices(projectId);
const environments = await getProjectEnvironments(projectId);

// 3. Trigger deployment
const deployment = await triggerDeployment(serviceId, environmentId);

// 4. Poll deployment status
const interval = setInterval(async () => {
  const status = await getDeploymentStatus(deployment.id);
  
  if (['SUCCESS', 'FAILED', 'CRASHED'].includes(status.status)) {
    clearInterval(interval);
    console.log('Deployment finished:', status.status);
  }
}, 5000);
```

### Multi-Service Deployment

The UATDeployment component supports deploying multiple services at once:

```javascript
const deploymentResults = [];

for (const serviceId of selectedServices) {
  try {
    const result = await triggerDeployment(serviceId, environmentId);
    deploymentResults.push({
      serviceId,
      deployment: result,
      status: 'triggered'
    });
  } catch (err) {
    deploymentResults.push({
      serviceId,
      error: err.message,
      status: 'failed'
    });
  }
}
```

## Testing

### Backend Tests

Run backend tests with pytest:

```bash
cd uat/backend
pytest tests/test_railway_api.py -v
pytest tests/test_railway_router.py -v
```

### Test Coverage

The implementation includes comprehensive tests for:

- Railway API client initialization and error handling
- GraphQL query execution
- All API methods (projects, services, environments, deployments)
- Router endpoints with success and error scenarios
- Authentication and authorization

### Manual Testing

1. Start the backend server:
   ```bash
   cd uat/backend
   uvicorn main:app --reload
   ```

2. Test the health endpoint:
   ```bash
   curl http://localhost:8000/api/railway/health
   ```

3. Test getting projects (requires auth token):
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/api/railway/projects
   ```

## Error Handling

### Backend Errors

The backend handles several types of errors:

1. **RailwayAPIError** - Railway API specific errors
   - HTTP status: 502 Bad Gateway
   - Returns error details from Railway API

2. **Authentication Errors** - Missing or invalid auth token
   - HTTP status: 401 Unauthorized

3. **Validation Errors** - Invalid request payload
   - HTTP status: 422 Unprocessable Entity

4. **Server Errors** - Unexpected errors
   - HTTP status: 500 Internal Server Error

### Frontend Error Handling

The frontend handles errors gracefully:

```javascript
try {
  const result = await triggerDeployment(serviceId, environmentId);
  setSuccess('Deployment triggered successfully');
} catch (err) {
  setError(`Deployment failed: ${err.message}`);
}
```

## Security Considerations

1. **API Token Storage**
   - Backend: Store in environment variables only
   - Frontend: Store auth tokens in localStorage (not Railway token)
   - Never commit tokens to version control

2. **Authentication**
   - All Railway endpoints require authentication
   - Uses existing JWT authentication system

3. **Rate Limiting**
   - Railway API has rate limits
   - Frontend implements polling with reasonable intervals (5s)
   - Stops polling when deployment reaches terminal state

4. **Environment Variables**
   - Service variables may contain sensitive data
   - Railway automatically redacts some values
   - Handle with care in the UI

## Troubleshooting

### "Railway API token not provided"

**Cause:** RAILWAY_API_TOKEN not set in environment

**Solution:** Add the token to your `.env` file:
```bash
RAILWAY_API_TOKEN=your-token-here
```

### "Railway API is not configured or unreachable"

**Causes:**
1. Railway API token is invalid or expired
2. Network connectivity issues
3. Railway API is down

**Solutions:**
1. Verify your token at https://railway.app/account/tokens
2. Check network connectivity
3. Check Railway status at https://railway.app/status

### "Deployment trigger returned no data"

**Cause:** Service or environment ID is invalid

**Solution:** Verify the IDs are correct using the get services/environments endpoints

### Deployment stays in QUEUED status

**Causes:**
1. Railway is experiencing high load
2. Service configuration issues
3. Billing/quota limits

**Solutions:**
1. Wait a few minutes and check again
2. Check service configuration in Railway dashboard
3. Verify your Railway account status

## References

- [Railway Public API Documentation](https://docs.railway.app/reference/public-api)
- [Railway GraphQL Schema](https://railway.app/graphql/schema)
- [Railway Status Page](https://railway.app/status)

## Future Enhancements

Potential improvements for future iterations:

1. **Deployment Logs** - Stream deployment logs in real-time
2. **Rollback** - Add ability to rollback to previous deployments
3. **Build Configuration** - Modify build settings via UI
4. **Metrics** - Display deployment metrics and analytics
5. **Webhooks** - Subscribe to deployment events
6. **Multi-Region** - Support for multiple Railway regions
7. **Cost Tracking** - Display deployment costs and resource usage
