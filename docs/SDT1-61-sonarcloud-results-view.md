# SDT1-61: SonarCloud Tab - Add Results View

## Overview

This feature adds comprehensive SonarCloud integration to the Control Centre, providing real-time code quality metrics, security vulnerability scanning, and technical debt analysis.

## Components

### Backend API (`uat/backend/sonarcloud_router.py`)

FastAPI router that integrates with SonarCloud API to:
- Trigger analysis runs
- Fetch quality gate status
- Retrieve project metrics
- Get issues summary (bugs, vulnerabilities, code smells, security hotspots)
- List available projects

#### Endpoints

- **POST** `/api/sonarcloud/trigger` - Trigger a SonarCloud analysis
- **GET** `/api/sonarcloud/results?projectKey={key}&branch={branch}` - Fetch analysis results
- **GET** `/api/sonarcloud/metrics?projectKey={key}&metrics={metrics}` - Get specific metrics
- **GET** `/api/sonarcloud/quality-gate?projectKey={key}&branch={branch}` - Get quality gate status
- **GET** `/api/sonarcloud/projects` - List all projects in organization

#### Configuration

Required environment variables:

```bash
SONARCLOUD_TOKEN=your_sonarcloud_token_here
SONARCLOUD_ORG=your_organization_name
```

### Frontend Component (`control-centre/src/components/SonarCloudTrigger.jsx`)

Enhanced React component with:
- Project configuration form
- One-click analysis triggering
- Real-time results display
- Auto-refresh capability (30-second intervals)
- Visual quality gate status
- Issues breakdown by type
- Key metrics dashboard
- Direct links to SonarCloud portal

#### Features

1. **Quality Gate Status Card**
   - Visual indicator (green/red/yellow)
   - Pass/fail status with descriptive messages
   - Prominent display at top of results

2. **Issues Overview**
   - 🐛 Bugs - Critical code defects
   - 🔒 Vulnerabilities - Security issues
   - 💨 Code Smells - Maintainability concerns
   - 🔥 Security Hotspots - Code requiring security review
   - Color-coded severity indicators

3. **Metrics Dashboard**
   - Code coverage percentage
   - Lines of code (ncloc)
   - Duplications
   - Technical debt (formatted as time units)
   - Additional SonarCloud metrics

4. **User Experience**
   - Auto-refresh toggle for continuous monitoring
   - Loading states with spinners
   - Error handling with clear messages
   - Responsive design for mobile/tablet
   - Smooth animations and transitions
   - Empty state guidance

## API Integration

### Trigger Analysis

```javascript
POST /api/sonarcloud/trigger
{
  "projectKey": "my-org_my-project",
  "branch": "main",
  "pullRequest": "123"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "To trigger analysis, run the GitHub Actions workflow or SonarScanner CLI",
  "projectKey": "my-org_my-project",
  "branch": "main",
  "dashboardUrl": "https://sonarcloud.io/dashboard?id=my-org_my-project",
  "instructions": "Run: gh workflow run sonarcloud.yml"
}
```

### Fetch Results

```javascript
GET /api/sonarcloud/results?projectKey=my-org_my-project&branch=main
```

**Response:**
```json
{
  "projectKey": "my-org_my-project",
  "qualityGateStatus": "OK",
  "metrics": [
    {"name": "Bugs", "value": "5"},
    {"name": "Coverage", "value": "85.5%"},
    {"name": "Lines of Code", "value": "1500"}
  ],
  "issues": {
    "bugs": 5,
    "vulnerabilities": 2,
    "codeSmells": 20,
    "securityHotspots": 3
  },
  "coverage": "85.5",
  "duplications": "3.2",
  "dashboardUrl": "https://sonarcloud.io/dashboard?id=my-org_my-project"
}
```

## Setup Instructions

### 1. Configure SonarCloud Credentials

Add to your `.env` file or Railway environment variables:

```bash
SONARCLOUD_TOKEN=your_token_here
SONARCLOUD_ORG=your_organization
```

To generate a token:
1. Go to SonarCloud.io
2. Navigate to My Account > Security
3. Generate a new token with appropriate permissions

### 2. Backend Setup

The router is automatically included in `main.py`:

```python
from sonarcloud_router import router as sonarcloud_router
app.include_router(sonarcloud_router)
```

No additional dependencies required (uses existing `httpx`).

### 3. Frontend Setup

The component is already integrated in `App.jsx`:

```javascript
{ id: "sonarcloud", label: "SonarCloud", component: SonarCloudTrigger }
```

No additional dependencies required.

### 4. Test the Integration

Run the backend tests:

```bash
cd uat/backend
pytest tests/test_sonarcloud_router.py -v
```

## Usage

### For Developers

1. Navigate to the **SonarCloud** tab in Control Centre
2. Enter your project key (e.g., `synpro-ai_virtual-dev-team`)
3. Select the branch (defaults to `main`)
4. Click **Fetch Results** to see current analysis
5. Enable **Auto-refresh** for continuous monitoring
6. Click **View Full Report on SonarCloud** for detailed analysis

### For CI/CD

The trigger endpoint provides instructions for running analysis:

```bash
# Using GitHub CLI
gh workflow run sonarcloud.yml

# Or using SonarScanner CLI
sonar-scanner \
  -Dsonar.projectKey=your_project_key \
  -Dsonar.organization=your_org \
  -Dsonar.sources=. \
  -Dsonar.host.url=https://sonarcloud.io \
  -Dsonar.login=$SONARCLOUD_TOKEN
```

## Architecture Decisions

### Why Separate Trigger and Fetch?

SonarCloud analysis is a long-running process (30s - 5min depending on project size). The separation allows:
- Non-blocking UI experience
- Flexibility to trigger via CI/CD or manually
- Independent polling of results
- Better error handling per operation

### Auto-Refresh Design

Implemented as a client-side interval (30s) to:
- Reduce server load
- Give immediate user control
- Work with existing API endpoints
- Avoid WebSocket complexity

### Metrics Selection

Default metrics chosen based on:
- OWASP/SANS standards for security
- Industry best practices for maintainability
- Common CI/CD quality gates
- Team feedback and priorities

## Error Handling

The implementation handles:

1. **Missing Configuration**
   - Clear error messages when token/org not set
   - Helpful setup instructions

2. **API Timeouts**
   - 15-second timeout on all requests
   - Graceful degradation
   - Retry suggestions

3. **Invalid Tokens**
   - 401 error detection
   - Token refresh instructions

4. **Project Not Found**
   - 404 handling with project list suggestion
   - Validation on project key format

## Security Considerations

1. **Token Storage**
   - Token stored in environment variables only
   - Never exposed to frontend
   - Server-side API calls only

2. **Rate Limiting**
   - Auto-refresh limited to 30s minimum
   - Backend respects SonarCloud API limits
   - User can disable auto-refresh

3. **CORS**
   - Backend proxy prevents CORS issues
   - No direct browser-to-SonarCloud calls
   - Credentials never in frontend code

## Testing

### Unit Tests

Comprehensive test coverage for:
- Header generation with/without token
- All endpoint success paths
- Error handling (401, 404, 500, 504)
- Timeout handling
- Model validation
- Data transformation

Run tests:

```bash
pytest uat/backend/tests/test_sonarcloud_router.py -v --cov=sonarcloud_router
```

### Manual Testing Checklist

- [ ] Fetch results for valid project
- [ ] Handle invalid project key
- [ ] Display all issue types correctly
- [ ] Quality gate colors match status
- [ ] Auto-refresh works and can be toggled
- [ ] Responsive on mobile devices
- [ ] External links open in new tabs
- [ ] Error messages are user-friendly

## Future Enhancements

### Planned (Not in SDT1-61)

1. **Historical Trends**
   - Chart showing metrics over time
   - Sprint-over-sprint comparison
   - Technical debt trends

2. **Issue Drill-Down**
   - Click on issue count to see list
   - Filter by severity/type
   - Direct links to code locations

3. **Multi-Project View**
   - Compare multiple projects
   - Organization-wide dashboard
   - Portfolio quality overview

4. **Notifications**
   - Alert on quality gate failures
   - Slack/email integration
   - Threshold-based alerts

5. **GitHub PR Integration**
   - Automatic PR analysis
   - Inline PR comments
   - Block merge on quality gate fail

## Related Tickets

- SDT1-47: Modular router architecture (foundation for this work)
- SDT1-56: CORS configuration (required for API proxy)
- Future: GitHub Actions workflow integration

## Support

For issues or questions:
1. Check SonarCloud documentation: https://docs.sonarcloud.io
2. Verify token and organization configuration
3. Review backend logs for API errors
4. Check network tab for request/response details

## References

- [SonarCloud API Documentation](https://sonarcloud.io/web_api)
- [SonarCloud Metrics Definitions](https://docs.sonarcloud.io/digging-deeper/metric-definitions/)
- [Quality Gates Guide](https://docs.sonarcloud.io/improving/quality-gates/)
