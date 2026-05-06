# PM Agent Validation

## Overview

The PM Agent Validation feature provides real-time validation warnings for Jira stories that are missing critical fields or don't follow best practices. This ensures that all stories are properly configured before sprint execution begins.

## Key Features

### 1. Execution Order Validation

**Critical**: Stories without `execution_order` (customfield_10071) will **not** be picked up by the Orchestrator for automated execution.

- Every story created by the PM Agent must have `execution_order` set
- The Orchestrator uses this field to sequence ticket execution
- Missing this field blocks the entire sprint automation

### 2. Validation Warnings

The system checks for:

- **Missing Execution Order** (Critical)
  - Stories without `execution_order` set
  - Prevents automated workflow execution
  - Must be resolved before sprint starts

- **Missing Epic Link** (Informational)
  - Stories not linked to an Epic
  - Recommended for better organization
  - Won't block execution

- **Long Summary** (Informational)
  - Summaries over 100 characters
  - Recommended for better readability in Jira views
  - Won't block execution

## Components

### ValidationWarnings

Full validation warnings panel with expandable sections.

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
      dismissible={false}
    />
  );
}
```

### ValidationBadge

Compact badge showing warning count.

```jsx
import ValidationBadge from './components/ValidationBadge';

<ValidationBadge
  count={5}
  criticalCount={2}
  onClick={() => showWarnings()}
  showLabel={true}
/>
```

### PMValidationDashboard

Complete dashboard view with summary cards and help section.

```jsx
import PMValidationDashboard from './components/PMValidationDashboard';

<PMValidationDashboard sprintId={currentSprint.id} />
```

## Hook API

### useValidationWarnings

```javascript
const {
  warnings,        // Array of warning objects
  loading,         // Boolean loading state
  error,           // Error message if fetch failed
  lastFetch,       // Date of last successful fetch
  refresh,         // Function to manually refresh
  hasWarnings,     // Boolean if any warnings exist
  criticalCount,   // Count of critical warnings
  warningCount,    // Count of warning-level warnings
  infoCount,       // Count of info-level warnings
} = useValidationWarnings({
  sprintId: null,           // Optional sprint filter
  autoRefresh: false,       // Auto-refresh enabled
  refreshInterval: 300000,  // 5 minutes
});
```

## API Endpoints

The validation system expects these backend endpoints:

### GET `/api/pm-agent/validation-warnings`

Returns all validation warnings for the current sprint.

**Response:**
```json
{
  "warnings": [
    {
      "issue_key": "SDT1-26",
      "type": "MISSING_EXECUTION_ORDER",
      "message": "execution_order not set. This story will not be sequenced correctly.",
      "suggestion": "Set execution_order based on dependencies.",
      "severity": "critical"
    }
  ]
}
```

### GET `/api/pm-agent/validation-warnings?sprint_id={id}`

Returns validation warnings for a specific sprint.

### GET `/api/pm-agent/validate-issue/{issue_key}`

Validates a specific issue and returns warnings.

**Response:**
```json
{
  "issue_key": "SDT1-26",
  "warnings": [...],
  "valid": false
}
```

## Integration Examples

### Sprint Dashboard Integration

```jsx
import { useValidationWarnings } from '../hooks/useValidationWarnings';
import ValidationBadge from './ValidationBadge';

function SprintDashboard() {
  const { criticalCount, warnings } = useValidationWarnings({ 
    sprintId: currentSprintId 
  });

  return (
    <div>
      <h2>
        Sprint Dashboard
        {criticalCount > 0 && (
          <ValidationBadge 
            count={warnings.length}
            criticalCount={criticalCount}
            onClick={() => setShowValidation(true)}
          />
        )}
      </h2>
      {/* Rest of dashboard */}
    </div>
  );
}
```

### PM Agent Chat Integration

```jsx
import ValidationWarnings from './ValidationWarnings';

function PMAgentChat() {
  const [showValidation, setShowValidation] = useState(false);
  const { warnings, refresh } = useValidationWarnings();

  return (
    <>
      <div className="chat-container">
        {/* Chat messages */}
      </div>
      {showValidation && (
        <ValidationWarnings
          warnings={warnings}
          onRefresh={refresh}
          dismissible={true}
        />
      )}
    </>
  );
}
```

## Styling

All components use CSS custom properties for theming:

- `--bg-card`: Card background
- `--bg`: Secondary background
- `--bg-hover`: Hover state background
- `--border`: Border color
- `--text`: Primary text color
- `--muted`: Muted text color
- `--accent`: Accent color

## Best Practices

1. **Always set execution_order**: The PM Agent should never create a story without this field
2. **Review critical warnings before sprint execution**: Use the PMValidationDashboard
3. **Link stories to epics**: Helps with organization and tracking
4. **Keep summaries concise**: Under 100 characters for better UX

## Troubleshooting

### Warnings Not Showing

1. Check that `VITE_API_URL` environment variable is set
2. Verify backend endpoint is implemented and returning correct format
3. Check browser console for API errors

### Validation Not Updating

1. Use the refresh button to manually update
2. Enable auto-refresh for real-time updates
3. Check network tab for failed requests

### False Positives

If validation shows warnings for issues that have been fixed:
1. Click the refresh button
2. Clear browser cache
3. Check that the backend is reading the latest Jira data

## Future Enhancements

- Real-time validation via WebSocket
- Bulk fix actions (set execution_order for multiple stories)
- Validation rules configuration
- Custom validation rules via API
- Integration with PM Agent to auto-fix common issues
