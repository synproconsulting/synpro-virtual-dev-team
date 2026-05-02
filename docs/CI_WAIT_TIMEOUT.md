# CI Wait Timeout Configuration

## Overview

The Orchestrator now includes configurable timeout functionality for waiting on CI/CD checks to complete on GitHub commits and pull requests.

## Timeout Values

### Current Configuration
- **CI Wait Timeout**: 30 minutes (1800 seconds)
- **Poll Interval**: 30 seconds

### Previous Configuration
- CI Wait Timeout: 15 minutes (900 seconds)

## Change History

### [SDT1-64] Extended CI Wait Timeout (30 minutes)
**Date**: Current implementation  
**Change**: Extended timeout from 15 minutes to 30 minutes  
**Rationale**: Longer-running integration tests and deployment workflows require more time to complete. The 15-minute timeout was insufficient for comprehensive test suites and complex CI pipelines.

## Usage

### Basic Usage

Wait for CI checks on a specific commit:

```python
from tools.github_client import wait_for_ci_completion

# Wait for CI with default 30-minute timeout
result = wait_for_ci_completion(
    commit_sha="abc123def456",
    verbose=True
)

if result["all_passed"]:
    print("All CI checks passed!")
else:
    print(f"CI checks failed or timed out: {result['state']}")
```

### Wait for PR CI

Convenience function for waiting on pull request CI:

```python
from tools.github_client import wait_for_pr_ci

# Wait for all CI checks on PR #123
result = wait_for_pr_ci(
    pr_number=123,
    verbose=True
)

print(f"Completed: {result['completed']}")
print(f"All passed: {result['all_passed']}")
print(f"Duration: {result['duration_seconds']}s")
```

### Custom Timeout

Override the default timeout if needed:

```python
from tools.github_client import wait_for_ci_completion

# Wait for 45 minutes instead of default 30
result = wait_for_ci_completion(
    commit_sha="abc123def456",
    timeout_seconds=45 * 60,  # 45 minutes
    poll_interval=60,  # Poll every 60 seconds
    verbose=True
)
```

## Return Values

Both `wait_for_ci_completion()` and `wait_for_pr_ci()` return a dictionary with:

- `completed` (bool): Whether checks completed (true) or timed out (false)
- `timed_out` (bool): Whether the wait timed out
- `all_passed` (bool): Whether all CI checks passed
- `state` (str): Overall state - "success", "failure", "pending", or "error"
- `duration_seconds` (float): How long the wait took
- `checks` (list): Details of all individual checks

## CI Check Types

The wait functions monitor both:

1. **Status Checks**: Traditional commit status checks
   - Example: `ci/test`, `ci/lint`, etc.
   
2. **Check Runs**: GitHub Actions and Apps
   - Example: GitHub Actions workflows, third-party CI apps

## Configuration Constants

The timeout values are configured in `tools/github_client.py`:

```python
# CI wait timeout configuration (in seconds)
CI_WAIT_TIMEOUT_SECONDS = 30 * 60  # 30 minutes
CI_POLL_INTERVAL_SECONDS = 30      # Poll every 30 seconds
```

## Integration with Orchestrator

The Orchestrator can use these functions when executing tickets to ensure CI passes before marking a ticket as complete:

```python
from tools.github_client import wait_for_pr_ci

# After creating a PR for a ticket
pr_number = create_pr_for_ticket(ticket_key)

# Wait for CI to complete
ci_result = wait_for_pr_ci(pr_number)

if ci_result["all_passed"]:
    mark_ticket_complete(ticket_key)
else:
    mark_ticket_failed(ticket_key, "CI checks failed")
```

## Troubleshooting

### Timeout Issues

If CI consistently times out at 30 minutes:

1. **Check CI Pipeline**: Investigate why tests are taking so long
2. **Optimize Tests**: Parallelize or optimize slow test suites
3. **Increase Timeout**: Temporarily increase for specific cases:
   ```python
   wait_for_ci_completion(sha, timeout_seconds=60*60)  # 1 hour
   ```

### No Checks Found

If `total_checks` is 0, it may mean:
- No CI is configured for the repository
- Checks haven't started yet (wait a bit and retry)
- Branch protection rules don't require status checks

### Intermittent Failures

If checks intermittently fail:
- Review individual check logs in GitHub
- Check for flaky tests
- Ensure external dependencies are stable

## Testing

Run the test suite for CI wait functionality:

```bash
pytest tests/test_github_ci_wait.py -v
```

The tests verify:
- Correct timeout value (30 minutes)
- Polling behavior
- Success/failure detection
- Timeout handling
- Combined status from multiple check types
