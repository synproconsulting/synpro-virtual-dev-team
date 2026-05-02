# SonarCloud Tab - Results View

## Overview

The SonarCloud tab in the Control Centre provides a comprehensive interface for triggering code quality analysis and viewing detailed results from SonarCloud. This feature integrates with the SonarCloud API to display quality metrics, issues, and quality gate status.

## Features

### 1. Analysis Triggering
- Trigger on-demand SonarCloud analysis for any project
- Support for different branches and pull requests
- Immediate feedback with dashboard links

### 2. Results View with Tabs

#### Overview Tab
- **Quality Gate Status**: Visual banner showing pass/fail status
- **Key Metrics Cards**: Quick view of bugs, vulnerabilities, code smells, and security hotspots
- **Coverage & Duplications**: Visual progress bars for code coverage and duplication percentages
- **Ratings**: Color-coded badges for reliability, security, and maintainability ratings (A-E scale)

#### Metrics Tab
- **Categorized Metrics**: Organized by Reliability, Security, Maintainability, Coverage, Duplications, and Size
- **Detailed Values**: All available metrics from SonarCloud with formatted display
- **Smart Formatting**: Automatic formatting for percentages, ratings, and large numbers

#### Issues Tab
- **Detailed Issue List**: Browse all issues with type, severity, and location
- **Filtering**: Filter by issue type (Bug, Vulnerability, Code Smell) and severity (Blocker to Info)
- **Rich Information**: Each issue shows:
  - Type icon (🐛 for bugs, 🔒 for vulnerabilities, 👃 for code smells)
  - Severity badge (color-coded)
  - Message and location (file and line number)
  - Rule reference

#### Quality Gate Conditions Tab
- **Condition Details**: Each quality gate condition with actual vs. threshold values
- **Status Indicators**: Visual pass/fail indicators for each condition
- **Clear Comparison**: Shows comparator (GT, LT, etc.) and error thresholds

## Backend API

### Endpoints

#### `POST /api/sonarcloud/trigger`
Trigger a SonarCloud analysis.

**Request Body:**
```json
{
  "projectKey": "my-org_my-project",
  "branch": "main",
  "pullRequest": "123"
}
```

**Response:**
```json
{
  "status": "success",
  "taskId": null,
  "dashboardUrl": "https://sonarcloud.io/dashboard?id=my-org_my-project",
  "message": "Analysis trigger initiated..."
}
```

#### `GET /api/sonarcloud/results`
Fetch comprehensive analysis results.

**Query Parameters:**
- `projectKey` (required): SonarCloud project key
- `branch` (optional): Branch name, defaults to "main"

**Response:**
```json
{
  "projectKey": "my-org_my-project",
  "qualityGateStatus": "OK",
  "qualityGateConditions": [...],
  "metrics": [...],
  "issues": {
    "bugs": 5,
    "vulnerabilities": 2,
    "codeSmells": 15,
    "securityHotspots": 1
  },
  "coverage": "85.5",
  "duplications": "3.2",
  "dashboardUrl": "..."
}
```

#### `GET /api/sonarcloud/issues`
Fetch detailed issues with filtering.

**Query Parameters:**
- `projectKey` (required): SonarCloud project key
- `branch` (optional): Branch name
- `types` (optional): Comma-separated issue types (BUG, VULNERABILITY, CODE_SMELL)
- `severities` (optional): Comma-separated severities (BLOCKER, CRITICAL, MAJOR, MINOR, INFO)
- `statuses` (optional): Comma-separated statuses (OPEN, CONFIRMED, REOPENED, RESOLVED, CLOSED)
- `page` (optional): Page number (default: 1)
- `pageSize` (optional): Page size (default: 100, max: 500)

**Response:**
```json
[
  {
    "key": "issue1",
    "rule": "squid:S1234",
    "severity": "MAJOR",
    "component": "my-project:src/main.py",
    "line": 42,
    "message": "Issue description",
    "type": "BUG",
    "status": "OPEN",
    "creationDate": "2024-01-01T00:00:00Z"
  }
]
```

#### `GET /api/sonarcloud/metrics`
Fetch specific metrics.

**Query Parameters:**
- `projectKey` (required): SonarCloud project key
- `metricKeys` (required): Comma-separated metric keys
- `branch` (optional): Branch name

#### `GET /api/sonarcloud/quality-gate`
Fetch quality gate status only.

**Query Parameters:**
- `projectKey` (required): SonarCloud project key
- `branch` (optional): Branch name

## Configuration

### Environment Variables

#### Backend
- `SONARCLOUD_TOKEN`: SonarCloud API token (required)
- `SONARCLOUD_ORG`: SonarCloud organization (optional, for reference)

#### Frontend
- `REACT_APP_API_BASE_URL`: Backend API URL (defaults to http://localhost:5000)

## Usage Guide

### Triggering Analysis

1. Navigate to the **SonarCloud** tab in the Control Centre
2. Enter the project key (e.g., `my-org_my-project`)
3. Optionally specify a branch or pull request
4. Click **Trigger Analysis**
5. View the success message and dashboard link

### Viewing Results

1. Enter or keep the project key in the form
2. Click the **View Results** toggle button
3. Click **Refresh Results** to load the latest analysis
4. Browse through different tabs:
   - **Overview**: High-level metrics and ratings
   - **Metrics**: Detailed metrics by category
   - **Issues**: Browse and filter issues
   - **Quality Gate Conditions**: Check pass/fail criteria

### Filtering Issues

In the Issues tab:
1. Use the **Type** dropdown to filter by issue type
2. Use the **Severity** dropdown to filter by severity level
3. Issues update automatically when filters change

## Implementation Details

### Frontend Components

- **SonarCloudTrigger.jsx**: Main container with form and view toggle
- **SonarResultsView.jsx**: Results display with tabbed interface
- **SonarCloudTrigger.css**: Main component styling
- **SonarResultsView.css**: Results view styling

### Backend Router

- **sonarcloud_router.py**: FastAPI router with all endpoints
- Uses `httpx` for async HTTP requests to SonarCloud API
- Pydantic models for request/response validation
- Comprehensive error handling

### API Integration

The backend acts as a proxy to the SonarCloud API:
- Authenticates using Bearer token
- Formats and validates requests
- Transforms responses for frontend consumption
- Handles errors gracefully

## Color Coding

### Quality Gate Status
- 🟢 Green (#52c41a): OK/PASSED
- 🔴 Red (#f5222d): ERROR/FAILED
- 🟡 Yellow (#faad14): WARN/WARNING

### Severity Levels
- 🔴 Blocker: #f5222d
- 🔴 Critical: #ff4d4f
- 🟠 Major: #fa8c16
- 🟡 Minor: #faad14
- 🔵 Info: #1890ff

### Ratings (A-E)
- 🟢 A (1): #52c41a
- 🟢 B (2): #95de64
- 🟡 C (3): #faad14
- 🟠 D (4): #ff7a45
- 🔴 E (5): #f5222d

## Testing

### Backend Tests
Run the test suite:
```bash
cd uat/backend
pytest tests/test_sonarcloud_router.py -v
```

Tests cover:
- Analysis triggering
- Results fetching
- Issue filtering
- Metrics retrieval
- Quality gate status
- Error handling
- Authentication

### Manual Testing

1. **Without SonarCloud Token**: Should show configuration error
2. **Invalid Project Key**: Should show API error
3. **Valid Project**: Should display all tabs with data
4. **Issue Filtering**: Should update issue list when filters change
5. **Branch Switching**: Should reload data for new branch

## Future Enhancements

Potential improvements:
- Real-time analysis status polling
- Historical trend charts
- Issue assignment workflow
- Export functionality (PDF/CSV)
- Custom quality gate templates
- Integration with Jira (link issues to tickets)
- Code diff view for issues
- Webhook support for automatic updates

## Troubleshooting

### "SONARCLOUD_TOKEN not configured"
- Set the `SONARCLOUD_TOKEN` environment variable in the backend
- Restart the backend service

### "Failed to connect to SonarCloud"
- Check network connectivity
- Verify SonarCloud API is accessible
- Check token permissions

### "Project not found"
- Verify the project key is correct
- Ensure the token has access to the project
- Check if the project exists on SonarCloud

### Empty Results
- Ensure analysis has been run at least once
- Check if the specified branch exists
- Verify the project has completed analysis

## References

- [SonarCloud API Documentation](https://sonarcloud.io/web_api)
- [SonarCloud Quality Gates](https://docs.sonarcloud.io/improving/quality-gates/)
- [SonarCloud Metrics](https://docs.sonarcloud.io/digging-deeper/metric-definitions/)
