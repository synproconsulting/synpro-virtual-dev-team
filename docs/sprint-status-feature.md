# Sprint Status Feature

## Overview

The Sprint Status feature provides comprehensive real-time visibility into the current sprint's progress, health metrics, and team workload directly in the Control Centre.

**Ticket**: [SDT1-74] Control Centre shows current sprint status

## Features

### 1. Sprint Overview Dashboard

The Sprint Overview tab displays:

- **Sprint Information**
  - Sprint name and goal
  - Start and end dates
  - Days remaining in the sprint

- **Sprint Health Indicator**
  - Visual health status (On Track / At Risk)
  - Color-coded health metrics
  - Automatic risk detection

- **Key Metrics Cards**
  - Completion rate with progress bar
  - Issues completed vs total
  - Issues in progress with story points
  - Current velocity (story points per day)

- **Visual Progress Bar**
  - Story points progress visualization
  - Breakdown by status (Done, In Progress, To Do)

- **Risk Factors**
  - Automatic detection of sprint risks
  - Clear list of identified issues
  - Warning when completion is low with limited time

- **Team Workload**
  - Per-team-member assignment breakdown
  - Story points assigned vs completed
  - Visual progress bars for each member

### 2. Real-Time Updates

- Auto-refreshes every 60 seconds
- Manual refresh available
- Last update timestamp displayed

## API Endpoints

### GET `/api/sprint-status/current`

Returns comprehensive current sprint status.

**Response:**

```json
{
  "sprint": {
    "id": "42",
    "name": "Sprint 42",
    "state": "active",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-14T00:00:00Z",
    "goal": "Deliver critical features"
  },
  "issue_breakdown": {
    "todo": 5,
    "in_progress": 3,
    "done": 12,
    "total": 20
  },
  "story_points": {
    "total": 50,
    "completed": 30,
    "in_progress": 10,
    "remaining": 20,
    "completion_percentage": 60.0
  },
  "team_workload": [
    {
      "name": "Alice Developer",
      "assigned_issues": 8,
      "assigned_points": 20,
      "completed_issues": 5,
      "completed_points": 12
    }
  ],
  "health_metrics": {
    "days_remaining": 7,
    "completion_rate": 60.0,
    "velocity": 4.2,
    "at_risk": false,
    "risk_factors": []
  },
  "last_updated": "2024-01-08T12:00:00Z"
}
```

### GET `/api/sprint-status/health-check`

Health check endpoint for the sprint status service.

**Response:**

```json
{
  "status": "ok",
  "service": "sprint-status",
  "jira_configured": true
}
```

## Sprint Health Algorithm

The sprint is marked as "At Risk" if any of these conditions are met:

1. **Low Completion with Limited Time**: Less than 70% complete with 3 or fewer days remaining
2. **No Progress**: No completed story points with less than 10 days remaining
3. **Too Many In Progress**: More issues in progress than done, and more than 3 in progress
4. **Low Velocity**: Current velocity is less than 70% of required velocity to complete on time

### Velocity Calculation

```
velocity = completed_points / days_elapsed
required_velocity = remaining_points / days_remaining
```

If `velocity < required_velocity * 0.7`, the sprint is at risk.

## Frontend Components

### SprintStatusOverview Component

Main component that displays the sprint status overview.

**Location**: `control-centre/src/components/SprintStatusOverview.jsx`

**Features**:
- Responsive grid layout
- Real-time metric cards
- Health indicator with color coding
- Team workload visualization
- Risk factor alerts

**Props**: None (self-contained, fetches data internally)

### Integration with SprintDashboard

The overview is integrated as a tab in the existing Sprint Dashboard:

```javascript
<SprintDashboard>
  <Tabs>
    <Tab id="overview" label="Sprint Overview">
      <SprintStatusOverview />
    </Tab>
    <Tab id="jira" label="Jira Issues">...</Tab>
    <Tab id="prs" label="Pull Requests">...</Tab>
    <Tab id="ci" label="CI/CD">...</Tab>
  </Tabs>
</SprintDashboard>
```

## Configuration

### Backend Environment Variables

```bash
# Required for sprint status
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=SDT1
JIRA_BOARD_ID=34
```

### Frontend Environment Variables

```bash
VITE_API_URL=http://localhost:8000
```

## Data Sources

The sprint status feature pulls data from:

1. **Jira Agile API** (`/rest/agile/1.0/board/{boardId}/sprint`)
   - Active sprint metadata
   - Sprint dates and goal

2. **Jira Search API** (`/rest/api/3/search`)
   - Sprint issues with JQL
   - Custom fields: `customfield_10016` (story points)
   - Status and assignee information

## Error Handling

- Returns empty status when no active sprint exists
- Gracefully handles missing story points (treats as 0)
- Handles unassigned issues (excluded from team workload)
- 500 error if Jira API fails with detailed error message

## Testing

### Backend Tests

Location: `uat/backend/tests/test_sprint_status_router.py`

Covers:
- Active sprint status retrieval
- No active sprint scenario
- At-risk sprint detection
- Team workload aggregation
- Error handling
- Edge cases (zero points, unassigned issues)

Run tests:

```bash
cd uat/backend
pytest tests/test_sprint_status_router.py -v
```

### Frontend Testing

Manual testing checklist:

- [ ] Sprint overview loads with active sprint
- [ ] Metrics update correctly
- [ ] Health indicator shows correct status
- [ ] Risk factors display when present
- [ ] Team workload shows all assigned members
- [ ] Auto-refresh works (wait 60 seconds)
- [ ] Handles no active sprint gracefully
- [ ] Mobile responsive layout works

## Future Enhancements

Potential improvements for future tickets:

1. **Historical Trends**
   - Sprint velocity over time
   - Burndown chart visualization
   - Completion rate trends

2. **Predictive Analytics**
   - Forecast sprint completion
   - Suggest optimal workload distribution
   - Identify bottlenecks early

3. **Notifications**
   - Alert when sprint becomes at-risk
   - Daily digest of sprint status
   - Slack/email integration

4. **Drill-Down Views**
   - Click team member to see their issues
   - Click metric to filter issue list
   - Interactive charts and graphs

5. **Custom Metrics**
   - Configurable risk thresholds
   - User-defined KPIs
   - Custom field support

## Troubleshooting

### Sprint status shows "No Active Sprint"

**Cause**: No sprint is currently active in Jira

**Solution**: Activate a sprint in Jira or check `JIRA_BOARD_ID` configuration

### Health metrics show 0 velocity

**Cause**: Sprint just started or no issues completed yet

**Solution**: Normal behavior for new sprints. Velocity will update as issues are completed.

### Team workload is empty

**Cause**: Issues are not assigned to team members

**Solution**: Assign issues in Jira to see workload distribution

### 500 error on `/api/sprint-status/current`

**Causes**:
- Jira API credentials invalid
- Network connectivity issues
- Jira board ID incorrect

**Solution**: Check environment variables and Jira connectivity

## Related Documentation

- [Jira API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Control Centre Architecture](./control-centre-architecture.md)
- [Sprint Dashboard Component](./sprint-dashboard.md)
