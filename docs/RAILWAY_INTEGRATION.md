# Railway GraphQL API Integration

This document describes the Railway GraphQL API integration for monitoring and triggering deployments through the Control Centre UAT Deploy tab.

## Overview

The Railway integration provides real-time visibility into deployment status across Railway projects and environments. It uses Railway's GraphQL API to fetch deployment information and trigger new deployments directly from the Control Centre.

## Architecture

### Backend Components

#### 1. Railway Client (`uat/backend/railway_client.py`)

Core client for interacting with Railway's GraphQL API.

**Key Features:**
- Asynchronous GraphQL query execution
- Project and service discovery
- Deployment status monitoring
- Deployment log retrieval
- Deployment triggering

**Main Methods:**
- `get_projects()` - Fetch all accessible projects
- `get_project_services(project_id)` - Get services in a project
- `get_service_deployments(service_id, environment_id, limit)` - Get recent deployments for a service
- `get_environment_deployments(project_id, environment_name)` - Get all deployments in an environment
- `get_deployment_logs(deployment_id, limit)` - Fetch deployment logs
- `trigger_deployment(service_id, environment_id)` - Trigger a new deployment

#### 2. Railway Router (`uat/backend/railway_router.py`)

FastAPI router exposing Railway functionality through REST endpoints.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/railway/projects` | List all projects |
| GET | `/api/railway/projects/{project_id}/services` | List services in a project |
| GET | `/api/railway/services/{service_id}/deployments` | Get service deployments |
| GET | `/api/railway/projects/{project_id}/environments/{env_name}/deployments` | Get environment deployments |
| GET | `/api/railway/deployments/{deployment_id}/logs` | Get deployment logs |
| POST | `/api/railway/deployments/trigger` | Trigger a deployment |
| GET | `/api/railway/health` | Check Railway API health |

### Frontend Components

#### 1. Railway API Client (`control-centre/src/api/railway.js`)

JavaScript client for calling backend Railway endpoints.

**Key Functions:**
- `getRailwayProjects()` - Fetch projects
- `getRailwayServices(projectId)` - Fetch services
- `getServiceDeployments(serviceId, options)` - Fetch deployments
- `getEnvironmentDeployments(projectId, environmentName)` - Fetch environment deployments
- `getDeploymentLogs(deploymentId, limit)` - Fetch logs
- `triggerDeployment(serviceId, environmentId)` - Trigger deployment
- `checkRailwayHealth()` - Check API health
- `formatDeploymentStatus(status)` - Format status for display

#### 2. UAT Deployment Component (`control-centre/src/components/UATDeployment.jsx`)

React component displaying Railway deployment information.

**Features:**
- Project selection dropdown
- Environment filtering (production, staging, UAT, development)
- Real-time deployment status cards
- Auto-refresh every 30 seconds (optional)
- Manual refresh button
- Deployment metadata display
- Health status indicator

## Configuration

### Environment Variables

#### Backend (`uat/backend/.env`)

```bash
# Railway API Configuration
RAILWAY_API_TOKEN=your-railway-api-token-here
RAILWAY_PROJECT_ID=your-default-project-id
```

**Getting Your Railway API Token:**
1. Go to https://railway.app/account/tokens
2. Click "Create Token"
3. Copy the token and set it as `RAILWAY_API_TOKEN`

**Finding Your Project ID:**
1. Navigate to your Railway project
2. The project ID is in the URL: `https://railway.app/project/{PROJECT_ID}`
3. Set it as `RAILWAY_PROJECT_ID` (optional, for auto-selection)

#### Frontend (`control-centre/.env`)

```bash
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# Optional: Default Railway project ID
VITE_RAILWAY_PROJECT_ID=your-railway-project-id
```

## Usage

### Backend Setup

1. **Install Dependencies:**
   ```bash
   cd uat/backend
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   ```bash
   export RAILWAY_API_TOKEN=your_token_here
   export RAILWAY_PROJECT_ID=your_project_id
   ```

3. **Start Server:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Verify Health:**
   ```bash
   curl http://localhost:8000/api/railway/health
   ```

### Frontend Setup

1. **Install Dependencies:**
   ```bash
   cd control-centre
   npm install
   ```

2. **Configure Environment:**
   ```bash
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env
   echo "VITE_RAILWAY_PROJECT_ID=your_project_id" >> .env
   ```

3. **Start Development Server:**
   ```bash
   npm run dev
   ```

4. **Access Control Centre:**
   Navigate to http://localhost:3001 and click on "UAT Deploy" tab

### Using the UAT Deploy Tab

1. **Select Project:** Choose a Railway project from the dropdown
2. **Select Environment:** Choose the target environment (production, staging, UAT, etc.)
3. **View Deployments:** See all recent deployments with status indicators
4. **Auto-Refresh:** Toggle auto-refresh for real-time updates every 30 seconds
5. **Manual Refresh:** Click the refresh button to update deployment data

## Railway Deployment Statuses

The integration recognizes and displays the following Railway deployment statuses:

| Status | Color | Description |
|--------|-------|-------------|
| SUCCESS | Green | Deployment completed successfully |
| ACTIVE | Green | Service is running |
| FAILED | Red | Deployment failed |
| CRASHED | Dark Red | Service crashed after deployment |
| BUILDING | Blue | Currently building the service |
| DEPLOYING | Purple | Currently deploying the service |
| INITIALIZING | Cyan | Deployment initializing |
| WAITING | Orange | Waiting in queue |
| REMOVING | Gray | Being removed |
| REMOVED | Gray | Has been removed |

## API Examples

### Fetch Projects

```bash
curl http://localhost:8000/api/railway/projects
```

**Response:**
```json
{
  "projects": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My Project",
      "description": "Production services",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-15T00:00:00Z"
    }
  ]
}
```

### Fetch Environment Deployments

```bash
curl "http://localhost:8000/api/railway/projects/PROJECT_ID/environments/production/deployments"
```

**Response:**
```json
{
  "environment": "production",
  "deployments": [
    {
      "id": "deploy-123",
      "status": "SUCCESS",
      "serviceName": "API Service",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:35:00Z",
      "staticUrl": "https://api.railway.app"
    }
  ]
}
```

### Trigger Deployment

```bash
curl -X POST http://localhost:8000/api/railway/deployments/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "service-123",
    "environment_id": "env-456"
  }'
```

**Response:**
```json
{
  "success": true,
  "deployment": {
    "id": "deploy-789",
    "status": "INITIALIZING",
    "createdAt": "2024-01-15T11:00:00Z"
  },
  "message": "Deployment triggered successfully"
}
```

## Testing

### Backend Tests

Run the test suite:

```bash
cd uat/backend
pytest tests/test_railway_client.py -v
pytest tests/test_railway_router.py -v
```

**Test Coverage:**
- Railway client initialization
- GraphQL query execution
- Project and service fetching
- Deployment retrieval and filtering
- Deployment triggering
- Error handling
- Router endpoint responses

### Manual Testing

1. **Test Health Endpoint:**
   ```bash
   curl http://localhost:8000/api/railway/health
   ```

2. **Test Projects Endpoint:**
   ```bash
   curl http://localhost:8000/api/railway/projects
   ```

3. **Test in Control Centre:**
   - Navigate to UAT Deploy tab
   - Verify projects load
   - Switch between environments
   - Enable auto-refresh
   - Check deployment cards display correctly

## Troubleshooting

### "Railway API not configured" Error

**Cause:** `RAILWAY_API_TOKEN` environment variable is not set.

**Solution:**
```bash
export RAILWAY_API_TOKEN=your_token_here
```

### "Failed to fetch projects" Error

**Causes:**
- Invalid API token
- Network connectivity issues
- Railway API is down

**Solutions:**
1. Verify token is valid: https://railway.app/account/tokens
2. Check network connectivity
3. Check Railway status: https://railway.app/status

### Empty Deployments List

**Causes:**
- Wrong environment name
- No deployments in environment
- Service not deployed yet

**Solutions:**
1. Verify environment name (case-insensitive)
2. Check Railway dashboard for deployments
3. Try different environment (production, staging, etc.)

### Auto-refresh Not Working

**Causes:**
- Auto-refresh not enabled
- Browser tab not active (some browsers throttle timers)
- Network issues

**Solutions:**
1. Ensure auto-refresh checkbox is checked
2. Keep tab active
3. Check network connectivity
4. Try manual refresh

## Security Considerations

1. **API Token Protection:**
   - Store Railway API token in environment variables only
   - Never commit tokens to version control
   - Rotate tokens regularly
   - Use Railway's token permissions to limit scope

2. **Backend Proxy:**
   - All Railway API calls go through the backend
   - Frontend never exposes Railway API token
   - Backend validates requests before forwarding

3. **Rate Limiting:**
   - Railway API has rate limits
   - Backend should implement caching for frequently accessed data
   - Auto-refresh interval should be reasonable (30s minimum)

4. **Error Handling:**
   - Graceful degradation when Railway API is unavailable
   - Clear error messages without exposing sensitive information
   - Logging of errors for debugging

## Future Enhancements

1. **Deployment Logs in UI:**
   - Add button to view deployment logs
   - Stream logs in real-time
   - Filter logs by severity

2. **Deployment Actions:**
   - Rollback to previous deployment
   - Cancel in-progress deployment
   - Restart service

3. **Metrics Integration:**
   - Display service metrics (CPU, memory, requests)
   - Historical deployment success rate
   - Deployment duration trends

4. **Notifications:**
   - Alert on deployment failures
   - Notify on deployment completion
   - Webhook integration

5. **Multi-environment Comparison:**
   - Side-by-side environment comparison
   - Diff between environment deployments
   - Promotion workflow (staging → production)

## References

- [Railway API Documentation](https://docs.railway.app/reference/public-api)
- [Railway GraphQL Schema](https://railway.app/graphql)
- [Railway Account Tokens](https://railway.app/account/tokens)
- [Railway Status Page](https://railway.app/status)

## Support

For issues or questions:
1. Check Railway documentation: https://docs.railway.app
2. Review Railway status: https://railway.app/status
3. Check backend logs for errors
4. Verify environment variables are set correctly
