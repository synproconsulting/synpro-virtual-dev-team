# Orchestrator CI/CD Monitoring

## Overview

The Orchestrator CI monitoring module (`agents/orchestrator_ci_monitor.py`) provides functionality to monitor GitHub Actions CI/CD pipeline status when executing tickets that trigger deployments.

## Configuration

### Timeout Settings

As of **SDT1-64**, the CI wait timeout has been extended:

- **Previous timeout**: 15 minutes
- **Current timeout**: **30 minutes**
- **Poll interval**: 30 seconds

This change accommodates longer-running CI pipelines, particularly for:
- Complex deployment workflows
- Multiple service deployments
- E2E test suites
- Integration tests with external dependencies

### Environment Variables

- `GITHUB_TOKEN`: Required. GitHub personal access token or workflow token with `actions:read` permission.

## Usage

### Basic Usage

```python
from agents.orchestrator_ci_monitor import wait_for_ci_completion

# Wait for CI to complete (30 minute timeout by default)
result = wait_for_ci_completion(
    repo_owner="myorg",
    repo_name="myrepo",
    branch="feature/my-feature",
)

if result == "success":
    print("CI passed!")
elif result == "failure":
    print("CI failed")
elif result == "timeout":
    print("CI timed out after 30 minutes")
```

### Advanced Usage with CIMonitor Class

```python
from agents.orchestrator_ci_monitor import CIMonitor

# Create monitor with custom settings
monitor = CIMonitor(
    github_token="ghp_xxxxx",
    timeout_minutes=30,  # Extended timeout
    poll_interval_seconds=30,
    verbose=True,
)

# Monitor specific workflow run
result = monitor.wait_for_ci(
    repo_owner="myorg",
    repo_name="myrepo",
    branch="main",
    commit_sha="abc123def456",  # Optional: monitor specific commit
    run_id=12345678,  # Optional: monitor specific run
)
```

### Integration with Orchestrator

```python
from agents.orchestrator import Orchestrator
from agents.orchestrator_ci_monitor import wait_for_ci_completion

class EnhancedOrchestrator(Orchestrator):
    """Orchestrator with CI monitoring."""
    
    def execute_ticket(self, ticket_key: str) -> bool:
        # Execute ticket work
        super().execute_ticket(ticket_key)
        
        # Wait for CI to pass
        ci_result = wait_for_ci_completion(
            repo_owner="myorg",
            repo_name="myrepo",
            branch=f"feature/{ticket_key.lower()}",
            timeout_minutes=30,
        )
        
        if ci_result != "success":
            raise Exception(f"CI {ci_result} for {ticket_key}")
        
        return True
```

## Return Values

The `wait_for_ci_completion` function and `wait_for_ci_with_retry` method return one of:

- `"success"`: CI pipeline completed successfully
- `"failure"`: CI pipeline failed or was skipped
- `"cancelled"`: CI pipeline was cancelled
- `"timeout"`: CI pipeline did not complete within the timeout period (30 minutes)

## Error Handling

### CITimeoutError

Raised when CI pipeline exceeds the configured timeout (30 minutes by default).

```python
from agents.orchestrator_ci_monitor import CITimeoutError

try:
    result = monitor.wait_for_ci("owner", "repo", "main", run_id=123)
except CITimeoutError as e:
    print(f"CI timed out: {e}")
```

### Retry Logic

The `wait_for_ci_with_retry` method automatically retries transient HTTP errors:

- Default: 3 retry attempts
- Wait between retries: 60 seconds
- Timeouts are not retried (return `"timeout"` immediately)

## API Details

### GitHub API Integration

The monitor uses the GitHub Actions REST API:

- **Endpoint**: `GET /repos/{owner}/{repo}/actions/runs`
- **Authentication**: Bearer token (requires `GITHUB_TOKEN`)
- **Rate limits**: Respects GitHub API rate limits
- **API Version**: `2022-11-28`

### Workflow Status Values

- `queued`: Workflow is queued but not yet started
- `in_progress`: Workflow is currently running
- `completed`: Workflow has finished (check `conclusion` for result)

### Workflow Conclusion Values

- `success`: All jobs succeeded
- `failure`: One or more jobs failed
- `cancelled`: Workflow was cancelled
- `skipped`: Workflow was skipped
- `timed_out`: Workflow exceeded GitHub's timeout
- `action_required`: Manual intervention required
- `neutral`: Workflow completed with neutral status

## Performance Considerations

### Timeout Selection

The 30-minute timeout was chosen based on typical CI pipeline durations:

- Unit tests: 2-5 minutes
- Integration tests: 5-10 minutes
- E2E tests: 10-20 minutes
- Deployment: 5-15 minutes
- **Total pipeline**: 15-30 minutes

### Poll Interval

The 30-second poll interval balances:
- API rate limit consumption
- Timely status updates
- System resource usage

At this interval, a 30-minute wait performs ~60 API calls.

### API Rate Limits

GitHub API rate limits:
- **Authenticated**: 5,000 requests/hour
- **Per-workflow**: ~60 requests over 30 minutes
- **Concurrent sprints**: Can monitor ~80 workflows simultaneously within rate limits

## Testing

Comprehensive test suite in `uat/backend/tests/test_orchestrator_ci_monitor.py` covers:

- Monitor initialization and configuration
- Workflow status retrieval
- Timeout handling (30 minutes)
- Success/failure/cancelled detection
- Retry logic for transient errors
- API error handling

Run tests:

```bash
pytest uat/backend/tests/test_orchestrator_ci_monitor.py -v
```

## Changelog

### SDT1-64: Extended CI Wait Timeout (2024)

- **Changed**: Timeout extended from 15 to 30 minutes
- **Reason**: Accommodate longer-running CI pipelines with multiple deployment stages
- **Impact**: Orchestrator will wait longer for CI completion before timing out
- **Configuration**: `CI_WAIT_TIMEOUT_MINUTES = 30`

## See Also

- [Orchestrator Documentation](./orchestrator.md)
- [GitHub Actions REST API](https://docs.github.com/en/rest/actions)
- [CI/CD Pipeline Configuration](.github/workflows/ci.yml)
