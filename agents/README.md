# Manager Agent

The Manager Agent is responsible for managing Jira workflow transitions with robust exponential backoff retry logic. It provides a resilient interface for transitioning issues through their lifecycle states.

## Features

- **Exponential Backoff Retry Logic**: Automatically retries failed API calls with exponential backoff
- **Configurable Retry Parameters**: Customize max retries, base delay, and max delay
- **Jitter**: Adds randomness to retry delays to prevent thundering herd problems
- **Multiple Transition Methods**: Support for both transition ID and status name-based transitions
- **Bulk Operations**: Transition multiple issues in a single operation
- **Workflow Helpers**: Convenience methods for common transitions (start work, complete, code review, testing)
- **Comprehensive Error Handling**: Detailed error messages and status tracking

## Architecture

```
agents/
├── manager_agent.py          # Core Manager Agent implementation
├── tests/
│   ├── __init__.py
│   └── test_manager_agent.py # Comprehensive test suite
└── README.md                 # This file

uat/backend/
└── manager_agent.py          # FastAPI router exposing Manager Agent API
```

## Retry Logic

The Manager Agent implements exponential backoff with the following behavior:

### Retryable Errors
- **HTTP 429** (Rate Limit)
- **HTTP 500** (Internal Server Error)
- **HTTP 502** (Bad Gateway)
- **HTTP 503** (Service Unavailable)
- **HTTP 504** (Gateway Timeout)
- **Network Errors** (Timeout, Connection errors)

### Non-Retryable Errors
- **HTTP 4xx** (Client errors like 400, 401, 403, 404)
- These fail immediately without retry

### Backoff Calculation

```python
delay = base_delay * (exponential_base ^ attempt)
delay = min(delay, max_delay)  # Cap at max
delay_with_jitter = delay ± (25% random jitter)
```

**Default Configuration:**
- `max_retries`: 5
- `base_delay`: 1.0 seconds
- `max_delay`: 60.0 seconds
- `exponential_base`: 2

**Example delays:**
- Attempt 0: ~1 second
- Attempt 1: ~2 seconds
- Attempt 2: ~4 seconds
- Attempt 3: ~8 seconds
- Attempt 4: ~16 seconds
- Attempt 5: ~32 seconds

## Usage

### Python API

```python
from agents.manager_agent import create_manager_agent

# Create agent with default settings
agent = create_manager_agent()

# Or with custom retry settings
agent = create_manager_agent(max_retries=10, base_delay=2.0)

# Start work on an issue
result = await agent.start_work("SDT1-44", assignee="john.doe")
print(f"Transitioned in {result.total_time:.2f}s after {result.attempts} attempts")

# Move to code review
result = await agent.move_to_code_review("SDT1-44", comment="Ready for review")

# Move to testing
result = await agent.move_to_testing("SDT1-44")

# Complete work
result = await agent.complete_work("SDT1-44", comment="All tests passing")

# Custom transition by status name
result = await agent.client.transition_issue_by_name(
    issue_key="SDT1-44",
    target_status="In Progress",
    comment="Starting work"
)

# Get current status
status = await agent.get_issue_status("SDT1-44")
print(f"Current status: {status}")
```

### REST API

The Manager Agent is exposed via FastAPI endpoints at `/api/manager-agent`.

#### Transition Issue

```bash
POST /api/manager-agent/transition
{
  "issue_key": "SDT1-44",
  "target_status": "In Progress",
  "assignee": "john.doe",
  "comment": "Starting work on this ticket"
}
```

#### Start Work

```bash
POST /api/manager-agent/start-work/SDT1-44?assignee=john.doe&comment=Starting%20work
```

#### Complete Work

```bash
POST /api/manager-agent/complete-work/SDT1-44?comment=All%20done
```

#### Move to Code Review

```bash
POST /api/manager-agent/code-review/SDT1-44
```

#### Move to Testing

```bash
POST /api/manager-agent/testing/SDT1-44
```

#### Get Issue Status

```bash
GET /api/manager-agent/status/SDT1-44
```

#### Bulk Transition

```bash
POST /api/manager-agent/bulk-transition
{
  "transitions": [
    {
      "issue_key": "SDT1-44",
      "target_status": "In Progress"
    },
    {
      "issue_key": "SDT1-45",
      "target_status": "Code Review"
    }
  ]
}
```

### Response Format

```json
{
  "success": true,
  "status": "success",
  "issue_key": "SDT1-44",
  "transition_id": "11",
  "transition_name": "Start Progress",
  "attempts": 1,
  "total_time": 0.523,
  "final_status": "In Progress",
  "error_message": null
}
```

## Configuration

Set these environment variables:

```bash
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=SDT1
```

## Testing

Run the comprehensive test suite:

```bash
# From agents/ directory
pytest tests/test_manager_agent.py -v

# Run with coverage
pytest tests/test_manager_agent.py --cov=manager_agent --cov-report=html

# Run specific test
pytest tests/test_manager_agent.py::TestJiraRetryClient::test_execute_with_retry_success_first_attempt -v
```

### Test Coverage

The test suite includes:
- ✓ Auth header creation
- ✓ Exponential backoff calculation
- ✓ Delay capping at max_delay
- ✓ Successful requests (first attempt and after retries)
- ✓ Max retries exceeded
- ✓ Retryable vs non-retryable errors
- ✓ Timeout and network errors
- ✓ Get issue and transitions
- ✓ Single and bulk transitions
- ✓ Transition by name with fallback
- ✓ Workflow methods (start, complete, review, testing)
- ✓ Integration scenarios

## Classes

### `JiraRetryClient`

Low-level client with retry logic for Jira API calls.

**Methods:**
- `get_issue(issue_key)` - Get issue details
- `get_transitions(issue_key)` - Get available transitions
- `transition_issue(issue_key, transition_id, ...)` - Execute transition by ID
- `transition_issue_by_name(issue_key, target_status, ...)` - Execute transition by status name
- `bulk_transition(transitions)` - Execute multiple transitions

### `ManagerAgent`

High-level agent with workflow convenience methods.

**Methods:**
- `start_work(issue_key, assignee, comment)` - Move to "In Progress"
- `complete_work(issue_key, comment)` - Move to "Done"
- `move_to_code_review(issue_key, comment)` - Move to "Code Review"
- `move_to_testing(issue_key, comment)` - Move to "Testing" or "QA"
- `get_issue_status(issue_key)` - Get current status

### `TransitionResult`

Result object returned by transition operations.

**Fields:**
- `status: TransitionStatus` - SUCCESS, FAILED, RETRYING, or MAX_RETRIES_EXCEEDED
- `issue_key: str` - Jira issue key
- `transition_id: str` - Transition ID used (optional)
- `transition_name: str` - Transition name (optional)
- `attempts: int` - Number of attempts made
- `total_time: float` - Total time in seconds
- `error_message: str` - Error message if failed (optional)
- `final_status: str` - Final status after transition (optional)

## Error Handling

The Manager Agent provides detailed error information:

```python
result = await agent.start_work("SDT1-999")

if result.status != TransitionStatus.SUCCESS:
    print(f"Failed after {result.attempts} attempts")
    print(f"Error: {result.error_message}")
    print(f"Total time: {result.total_time:.2f}s")
```

## Best Practices

1. **Use Workflow Methods**: Prefer `start_work()`, `complete_work()`, etc. over raw transitions
2. **Monitor Retry Attempts**: Log `result.attempts` to track API reliability
3. **Set Reasonable Timeouts**: Default is 30s per request
4. **Handle Failures Gracefully**: Check `result.status` before proceeding
5. **Use Bulk Operations**: For multiple transitions, use `bulk_transition()` for better performance
6. **Add Comments**: Always provide meaningful comments for audit trails

## Monitoring

Track these metrics in production:

- `result.attempts` - Number of retries needed
- `result.total_time` - Total operation time
- `result.status` - Success/failure rate
- HTTP status codes in logs

## Integration with Other Agents

The Manager Agent is designed to be called by:

- **Orchestrator**: Coordinates workflow across multiple issues
- **Developer Agent**: Transitions issues during development
- **QA Agent**: Moves issues to testing/done
- **PM Agent**: Updates issue status based on sprint planning

## Future Enhancements

- [ ] Circuit breaker pattern for sustained failures
- [ ] Metrics collection (Prometheus/StatsD)
- [ ] Webhook notifications on status changes
- [ ] Batch optimization for bulk operations
- [ ] Custom transition validation rules
- [ ] Rate limit aware scheduling

## Troubleshooting

### Issue: All retries exhausted
**Cause**: Jira API is down or rate limiting
**Solution**: Check Jira status, verify credentials, increase delays

### Issue: "No transition found to 'Status'"
**Cause**: Target status not available from current status
**Solution**: Check Jira workflow, verify current status, use correct status name

### Issue: 401 Unauthorized
**Cause**: Invalid credentials
**Solution**: Verify JIRA_EMAIL and JIRA_API_TOKEN environment variables

### Issue: Slow transitions
**Cause**: Network latency or API slowness
**Solution**: Monitor `total_time`, consider reducing `max_retries` or adjusting timeouts

## License

Part of the SynPro Virtual Dev Team project.
