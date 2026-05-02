# Railway Integration Guide

This document describes the Railway GraphQL API integration for UAT deployments.

## Overview

The UAT Deploy tab in the Control Centre is now wired to Railway's GraphQL API, enabling:

- Real-time service listing from Railway projects
- Multi-service deployment triggers
- Deployment status monitoring
- Deployment history tracking
- Live deployment logs (future enhancement)

## Architecture

```
┌─────────────────────┐
│  Control Centre     │
│  (React Frontend)   │
└──────────┬──────────┘
           │
           │ HTTP/REST
           ▼
┌─────────────────────┐
│  UAT Backend        │
│  (FastAPI)          │
└──────────┬──────────┘
           │
           │ GraphQL
           ▼
┌─────────────────────┐
│  Railway API        │
│  (GraphQL)          │
└─────────────────────┘
```

## Configuration

### Backend Setup

1. **Get Railway API Token**
   - Go to Railway Dashboard → Settings → Tokens
   - Create a new token with appropriate permissions
   - Copy the token

2. **Get Project and Environment IDs**
   - Project ID: Found in Railway project settings URL
   - Environment ID: Found in environment settings URL

3. **Set Environment Variables**

```bash
# .env or Railway environment variables
RAILWAY_API_TOKEN=your-railway-api-token-here
RAILWAY_PROJECT_ID=your-project-id-here
RAILWAY_ENVIRONMENT_ID=your-environment-id-here  # Optional
```

### Frontend Setup

1. **Configure API Base URL**

```bash
# control-centre/.env
VITE_API_BASE_URL=http://localhost:8000  # Development
# or
VITE_API_BASE_URL=https://your-api.railway.app  # Production
```

## API Endpoints

### Backend (FastAPI)

#### List Services
```http
GET /api/deployments/services
Authorization: Bearer <token>
```

Response:
```json
[
  {
    "id": "service-id",
    "name": "API Service",
    "icon": "🚀"
  }
]
```

#### List Environments
```http
GET /api/deployments/environments
Authorization: Bearer <token>
```

Response:
```json
[
  {
    "id": "env-id",
    "name": "UAT"
  }
]
```

#### Trigger Deployment
```http
POST /api/deployments/trigger
Authorization: Bearer <token>
Content-Type: application/json

{
  "service_ids": ["service-1", "service-2"],
  "environment_id": "env-id",  // Optional
  "deployment_notes": "Deploying new features"  // Optional
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully triggered 2 deployment(s)",
  "deployments": [
    {
      "id": "deployment-id",
      "status": "BUILDING",
      "service_name": "API Service",
      "environment_name": "UAT",
      "created_at": "2024-01-01T12:00:00Z",
      "url": "https://api.example.com"
    }
  ],
  "failed_services": []
}
```

#### Get Deployment Status
```http
GET /api/deployments/status/{deployment_id}
Authorization: Bearer <token>
```

#### Get Deployment History
```http
GET /api/deployments/history?service_id=service-1&limit=10
Authorization: Bearer <token>
```

#### Get Deployment Logs
```http
GET /api/deployments/logs/{deployment_id}?limit=100
Authorization: Bearer <token>
```

## Frontend Usage

### Railway API Client

```javascript
import {
  listServices,
  listEnvironments,
  triggerDeployment,
  getDeploymentStatus,
  getDeploymentHistory,
  pollDeploymentStatus,
} from '../api/railway';

// List available services
const services = await listServices();

// Trigger deployment
const result = await triggerDeployment({
  service_ids: ['service-1', 'service-2'],
  environment_id: 'env-id',
  deployment_notes: 'Deploy v2.0',
});

// Poll deployment status
await pollDeploymentStatus(
  deploymentId,
  (status) => {
    console.log('Status update:', status);
  },
  5000,  // Poll every 5 seconds
  600000 // 10 minute timeout
);
```

## Deployment Status Values

Railway deployment statuses:

- `BUILDING` - Deployment is being built
- `DEPLOYING` - Deployment is being deployed
- `SUCCESS` / `ACTIVE` - Deployment succeeded
- `FAILED` - Deployment failed
- `CRASHED` - Service crashed after deployment
- `REMOVED` - Deployment was removed

## Security

### Authentication

All endpoints require authentication via JWT token:

```javascript
// Token is automatically included from localStorage
localStorage.setItem('authToken', 'your-jwt-token');
```

### Authorization

Only authenticated users can:
- View services and environments
- Trigger deployments
- View deployment history

## Error Handling

### Backend Errors

The backend returns standard HTTP error codes:

- `400` - Bad request (e.g., missing service IDs)
- `401` - Unauthorized (missing or invalid token)
- `404` - Resource not found (e.g., deployment ID)
- `500` - Internal server error (Railway API errors)

### Frontend Error Handling

```javascript
try {
  await triggerDeployment(config);
} catch (error) {
  console.error('Deployment failed:', error.message);
  // Display error to user
}
```

## Testing

### Backend Tests

```bash
# Run tests
cd uat/backend
pytest tests/test_railway_client.py
pytest tests/test_deployment_router.py

# Run with coverage
pytest --cov=. tests/
```

### Manual Testing

1. **Test Service Listing**
   - Open Control Centre
   - Navigate to UAT Deploy tab
   - Verify services load from Railway

2. **Test Deployment**
   - Select one or more services
   - Choose environment
   - Click "Deploy to UAT"
   - Verify deployment triggers in Railway

3. **Test Status Polling**
   - After triggering deployment
   - Verify status updates automatically
   - Check deployment history refreshes

## Troubleshooting

### Services Not Loading

1. Check Railway API token is valid
2. Verify project ID is correct
3. Check network connectivity to Railway API
4. Review backend logs for errors

### Deployment Fails

1. Check service IDs are correct
2. Verify environment ID exists
3. Ensure Railway project has necessary permissions
4. Check Railway project status

### Authentication Errors

1. Verify JWT token is valid
2. Check token is being sent in Authorization header
3. Ensure backend JWT configuration is correct

## Railway GraphQL API Reference

Official documentation:
- [Railway GraphQL API Docs](https://docs.railway.app/reference/public-api)
- [Railway API Explorer](https://railway.app/graphql)

Common queries used:

```graphql
# Get project info
query GetProject($projectId: String!) {
  project(id: $projectId) {
    id
    name
    environments { edges { node { id name } } }
    services { edges { node { id name } } }
  }
}

# Trigger deployment
mutation DeploymentTrigger($environmentId: String!, $serviceId: String!) {
  deploymentTrigger(
    input: {
      environmentId: $environmentId
      serviceId: $serviceId
    }
  ) {
    id
    status
    createdAt
  }
}

# Get deployment status
query GetDeployment($deploymentId: String!) {
  deployment(id: $deploymentId) {
    id
    status
    createdAt
    service { name }
    environment { name }
    url
  }
}
```

## Future Enhancements

Planned improvements:

1. **Real-time Log Streaming**
   - WebSocket connection for live logs
   - Tail logs during deployment

2. **Rollback Support**
   - One-click rollback to previous deployment
   - Deployment comparison view

3. **Deployment Scheduling**
   - Schedule deployments for specific times
   - Recurring deployment windows

4. **Deployment Notifications**
   - Email/Slack notifications on deployment status
   - Webhook integrations

5. **Multi-Environment Support**
   - Deploy to multiple environments simultaneously
   - Environment promotion workflows

## Support

For issues or questions:

1. Check Railway API status: https://status.railway.app/
2. Review Railway API docs: https://docs.railway.app/
3. Check backend logs for detailed error messages
4. Verify all environment variables are set correctly
