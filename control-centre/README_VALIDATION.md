# PM Agent Validation Feature

## Quick Start

The PM Agent Validation feature warns when stories are missing critical fields like `execution_order`, which is required for the Orchestrator to sequence ticket execution.

### Installation

All validation components are already included in the control-centre package. No additional dependencies required.

### Basic Usage

```jsx
import ValidationWarnings from './components/ValidationWarnings';
import { useValidationWarnings } from './hooks/useValidationWarnings';

function MyComponent() {
  const { warnings, loading, refresh } = useValidationWarnings();

  return (
    <ValidationWarnings
      warnings={warnings}
      loading={loading}
      onRefresh={refresh}
    />
  );
}
```

## Components

### 1. ValidationWarnings

Full-featured validation warnings panel with sections for critical and informational warnings.

**Props:**
- `warnings` (Array): Array of warning objects
- `loading` (Boolean): Loading state
- `onRefresh` (Function): Callback for refresh button
- `dismissible` (Boolean): Allow dismissing warnings
- `className` (String): Additional CSS class
- `title` (String): Panel title
- `showCount` (Boolean): Show warning count in title

**Example:**
```jsx
<ValidationWarnings
  warnings={warnings}
  loading={false}
  onRefresh={handleRefresh}
  dismissible={true}
  title="Validation Warnings"
  showCount={true}
/>
```

### 2. ValidationBadge

Compact badge for displaying warning count in headers or toolbars.

**Props:**
- `count` (Number): Total warning count
- `criticalCount` (Number): Critical warning count
- `onClick` (Function): Click handler
- `size` (String): 'small', 'medium', or 'large'
- `showLabel` (Boolean): Show text label

**Example:**
```jsx
<ValidationBadge
  count={5}
  criticalCount={2}
  onClick={() => setShowPanel(true)}
  size="medium"
  showLabel={true}
/>
```

### 3. PMValidationDashboard

Complete dashboard view with summary cards, auto-refresh, and help documentation.

**Props:**
- `sprintId` (Number|String): Optional sprint ID to filter warnings

**Example:**
```jsx
<PMValidationDashboard sprintId={currentSprint.id} />
```

## Hooks

### useValidationWarnings

React hook for managing validation state.

**Parameters:**
```javascript
{
  sprintId: null,           // Filter by sprint ID
  autoRefresh: false,       // Enable auto-refresh
  refreshInterval: 300000,  // Refresh interval (ms)
}
```

**Returns:**
```javascript
{
  warnings: [],        // Array of warnings
  loading: false,      // Loading state
  error: null,         // Error message
  lastFetch: Date,     // Last fetch timestamp
  refresh: Function,   // Manual refresh function
  hasWarnings: false,  // Boolean convenience flag
  criticalCount: 0,    // Count of critical warnings
  warningCount: 0,     // Count of warning-level
  infoCount: 0,        // Count of info-level
}
```

## Warning Types

### MISSING_EXECUTION_ORDER (Critical)

**Why it matters:** Stories without `execution_order` will not be picked up by the Orchestrator. This blocks the entire automated workflow.

**How to fix:** Set execution_order on the story based on dependencies:
- Stories that others depend on get lower numbers (1, 2, 3...)
- Independent stories get higher numbers
- Use PM Agent tools to establish dependencies first

### MISSING_EPIC (Informational)

**Why it matters:** Stories not linked to Epics are harder to organize and track.

**How to fix:** Link the story to an appropriate Epic in Jira.

### LONG_SUMMARY (Informational)

**Why it matters:** Summaries over 100 characters are truncated in Jira board views.

**How to fix:** Shorten the summary to under 100 characters.

## API Integration

The validation system expects these backend endpoints:

### GET `/api/pm-agent/validation-warnings`

Returns all validation warnings for the current/active sprint.

**Response Format:**
```json
{
  "warnings": [
    {
      "issue_key": "SDT1-26",
      "type": "MISSING_EXECUTION_ORDER",
      "message": "execution_order not set...",
      "suggestion": "Set execution_order based on dependencies...",
      "severity": "critical"
    }
  ]
}
```

### GET `/api/pm-agent/validation-warnings?sprint_id={id}`

Returns warnings filtered by sprint ID.

### GET `/api/pm-agent/validate-issue/{issue_key}`

Validates a single issue.

**Response Format:**
```json
{
  "issue_key": "SDT1-26",
  "warnings": [...],
  "valid": false
}
```

## Development & Testing

### Using Mock Data

For development without a backend:

```javascript
import { generateMockWarnings, testScenarios } from './utils/validationTestData';

// Generate warnings
const warnings = generateMockWarnings({
  criticalCount: 3,
  infoCount: 2,
});

// Use predefined scenarios
const warnings = testScenarios.criticalOnly.warnings;
```

### Environment Variables

Add to `.env.local`:
```bash
# Enable mock validation API
VITE_USE_MOCK_VALIDATION=true

# Your actual API URL (when not using mock)
VITE_API_URL=http://localhost:8000

# Jira URL for issue links
VITE_JIRA_URL=https://synproconsulting.atlassian.net
```

### Testing Scenarios

Run through these scenarios:

1. **No Warnings**: Sprint with all fields set correctly
2. **Critical Only**: Sprint with missing execution_order
3. **Mixed**: Sprint with critical and informational warnings
4. **Auto-refresh**: Enable auto-refresh and verify updates
5. **Sprint Filter**: Switch between sprints and verify warnings update

## Integration Examples

### Sprint Dashboard

Add validation badge to sprint dashboard header:

```jsx
import ValidationBadge from './components/ValidationBadge';
import { useValidationWarnings } from './hooks/useValidationWarnings';

function SprintDashboard({ sprint }) {
  const { warnings, criticalCount } = useValidationWarnings({ 
    sprintId: sprint.id 
  });

  return (
    <div className="sprint-header">
      <h2>Sprint {sprint.name}</h2>
      {warnings.length > 0 && (
        <ValidationBadge
          count={warnings.length}
          criticalCount={criticalCount}
          onClick={() => navigate('/validation')}
        />
      )}
    </div>
  );
}
```

### PM Agent Chat

Show critical warnings at top of chat:

```jsx
import ValidationWarnings from './components/ValidationWarnings';

function PMAgentChat() {
  const { warnings } = useValidationWarnings();
  const critical = warnings.filter(w => w.severity === 'critical');

  return (
    <div className="chat-container">
      {critical.length > 0 && (
        <div className="chat-alert">
          <ValidationWarnings
            warnings={critical}
            title="Critical Issues"
            dismissible={false}
          />
        </div>
      )}
      {/* Chat messages... */}
    </div>
  );
}
```

### Standalone Validation Page

Create a dedicated validation page:

```jsx
import PMValidationDashboard from './components/PMValidationDashboard';

function ValidationPage() {
  const { sprintId } = useParams();

  return (
    <div className="page-container">
      <PMValidationDashboard sprintId={sprintId} />
    </div>
  );
}
```

## Styling

All components use CSS custom properties for theming. Customize in your global CSS:

```css
:root {
  --bg-card: #ffffff;
  --bg: #f8fafc;
  --bg-hover: #f1f5f9;
  --border: #e2e8f0;
  --text: #0f172a;
  --muted: #64748b;
  --accent: #6366f1;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-card: #1e293b;
    --bg: #0f172a;
    --bg-hover: #334155;
    --border: #334155;
    --text: #f8fafc;
    --muted: #94a3b8;
    --accent: #818cf8;
  }
}
```

## Troubleshooting

### Warnings Not Appearing

**Check:**
1. `VITE_API_URL` is set correctly
2. Backend endpoint is implemented
3. Browser console for API errors
4. Network tab shows successful responses

**Debug:**
```javascript
const { warnings, error, loading } = useValidationWarnings();

console.log('Warnings:', warnings);
console.log('Error:', error);
console.log('Loading:', loading);
```

### Stale Data

**Solutions:**
1. Click the refresh button
2. Enable auto-refresh
3. Clear browser cache
4. Verify backend is reading latest Jira data

### Styling Issues

**Check:**
1. CSS files are imported
2. CSS custom properties are defined
3. No conflicting styles
4. Browser DevTools for computed styles

## Best Practices

1. **Always validate before sprint execution**
   - Use PMValidationDashboard to review all warnings
   - Resolve critical warnings first
   - Document why informational warnings are ignored (if any)

2. **Monitor validation in real-time**
   - Enable auto-refresh during active sprint planning
   - Show badges in navigation/headers
   - Alert users when critical warnings appear

3. **Educate the team**
   - Document why execution_order is critical
   - Share examples of properly configured stories
   - Include validation checks in sprint planning checklist

4. **Automate fixes when possible**
   - PM Agent should automatically set execution_order
   - Use bulk actions to link stories to epics
   - Validate during story creation, not just before execution

## Related Documentation

- [PM Agent Validation Details](./docs/PM_AGENT_VALIDATION.md)
- [Validation Examples](./src/components/ValidationExample.jsx)
- [Test Data Generator](./src/utils/validationTestData.js)

## Support

For issues or questions:
1. Check browser console for errors
2. Review backend logs for API errors
3. Verify Jira field configuration (customfield_10071)
4. Check that stories have execution_order set in Jira

## Changelog

### v1.0.0 (SDT1-65)
- Initial implementation of validation warnings
- ValidationWarnings component
- ValidationBadge component
- PMValidationDashboard component
- useValidationWarnings hook
- Mock data generator for testing
- Comprehensive documentation
