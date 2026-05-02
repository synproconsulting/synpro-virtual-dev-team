# CI Wait Timeout Configuration

## Overview

The orchestrator uses a configurable timeout when waiting for GitHub Actions CI checks to complete on pull requests. This document describes the timeout configuration and the rationale for the current settings.

## Current Configuration

As of **SDT1-64**, the CI wait timeout has been set to:

- **Timeout**: 30 minutes (1800 seconds)
- **Poll Interval**: 30 seconds
- **Maximum Polls**: 60 attempts

### Previous Configuration

Prior to SDT1-64, the timeout was:

- **Timeout**: 15 minutes (900 seconds)
- **Poll Interval**: 30 seconds  
- **Maximum Polls**: 30 attempts

## Rationale for Extension

The timeout was doubled from 15 to 30 minutes to accommodate:

1. **Comprehensive Test Suites**: Modern test suites with extensive unit, integration, and E2E tests can take 10-20 minutes to complete
2. **Multi-Stage Pipelines**: CI pipelines with multiple jobs (test, security scan, quality gate, E2E tests) run in parallel but may take longer overall
3. **Security Scanning**: Tools like Bandit and SonarCloud can add 3-5 minutes to pipeline duration
4. **E2E Testing**: Playwright E2E tests with browser automation can take 5-10 minutes
5. **Cold Starts**: GitHub Actions runners may experience cold start delays, especially during peak usage
6. **Deployment Steps**: Pipelines that include deployment verification steps need additional time

## Configuration Location

The timeout is defined in `tools/ci_wait.py`:

```python
# CI wait configuration
# Increased from 15 minutes to 30 minutes per SDT1-64
CI_WAIT_TIMEOUT_SECONDS = 30 * 60  # 30 minutes
CI_POLL_INTERVAL_SECONDS = 30  # Poll every 30 seconds
```

## Usage

### Basic Usage

```python
from tools.ci_wait import wait_for_ci

# Wait for CI on PR #42 with default timeout (30 minutes)
result = wait_for_ci(pr_number=42)

if result.success:
    print(f"✓ CI passed in {result.duration_seconds/60:.1f} minutes")
elif result.timeout:
    print(f"⏱ CI timed out after {result.duration_seconds/60:.1f} minutes")
else:
    print(f"✗ CI failed: {result.message}")
```

### Custom Timeout

```python
from tools.ci_wait import wait_for_ci

# Use a shorter timeout for quick checks
result = wait_for_ci(
    pr_number=42,
    timeout_seconds=5 * 60,  # 5 minutes
    poll_interval=15,         # Poll every 15 seconds
)
```

### Wait by Branch

```python
from tools.ci_wait import wait_for_ci_by_branch

# Find the PR for a branch and wait for its CI
result = wait_for_ci_by_branch("feature/sdt1-64-ci-timeout")
```

### Get CI Summary

```python
from tools.ci_wait import get_ci_summary

# Get human-readable CI status
summary = get_ci_summary(pr_number=42)
print(summary)
```

## How It Works

### 1. Get PR Details

The function first retrieves the pull request details from GitHub's API to get the HEAD commit SHA.

### 2. Poll Check Runs

Every 30 seconds, it polls the GitHub API for:
- **Check Runs API**: Modern CI checks (GitHub Actions, etc.)
- **Commit Status API**: Legacy status checks (for compatibility)

### 3. Evaluate Completion

Checks are considered complete when:
- All check runs have `status: "completed"`
- Each completed run has a conclusion (success, failure, skipped, etc.)

### 4. Determine Success

The result is successful if all checks have conclusions of:
- `success`: Check passed
- `skipped`: Check was skipped (non-blocking)
- `neutral`: Check completed without error (non-blocking)

Any check with conclusion `failure`, `timed_out`, or `action_required` will result in a failed result.

### 5. Timeout Handling

If checks are not complete after 30 minutes:
- Returns a timeout result
- Includes whatever check runs were found
- Does not retry (orchestrator can decide whether to retry)

## Architecture

### Components

```
tools/ci_wait.py
├── Constants
│   ├── CI_WAIT_TIMEOUT_SECONDS = 1800
│   └── CI_POLL_INTERVAL_SECONDS = 30
├── Data Classes
│   ├── CIWaitResult
│   ├── CheckStatus (Enum)
│   └── CheckConclusion (Enum)
├── API Functions
│   ├── get_pr_head_sha()
│   ├── get_commit_check_runs()
│   └── get_commit_status()
├── Check Logic
│   └── are_checks_complete()
└── Main Functions
    ├── wait_for_ci()
    ├── wait_for_ci_by_branch()
    └── get_ci_summary()
```

### Integration Points

The CI wait functionality integrates with:

1. **Orchestrator** (`agents/orchestrator.py`): Waits for CI after opening PRs
2. **Dev Manager**: Reviews PRs and checks CI status before merge
3. **GitHub Client** (`tools/github_client.py`): Extended with CI status check methods

## Monitoring and Logging

When `verbose=True` (default), the function prints progress:

```
⏳ Waiting for CI checks on PR #42 (timeout: 30 minutes)...
📍 Monitoring commit: abc123de
  [0.5m] CI in progress: 1/3 checks complete. Waiting for: lint, e2e
  [1.2m] CI in progress: 2/3 checks complete. Waiting for: e2e
  [2.8m] CI completed: All 3 checks passed ✓
✓ CI completed in 2.8 minutes: All 3 checks passed ✓
```

## Performance Considerations

### API Rate Limits

GitHub API rate limits:
- **Authenticated**: 5,000 requests per hour
- **Check Runs API**: Counts as 1 request per call
- **Commit Status API**: Counts as 1 request per call

With 30-second polling:
- Maximum polls in 30 minutes: 60
- API requests per wait: 60 × 2 = 120 requests
- Multiple PRs: Can handle ~40 concurrent waits per hour

### Resource Usage

- **Memory**: Minimal (<1 MB per wait)
- **CPU**: Very low (mostly sleeping)
- **Network**: 2 API calls per poll interval

## Testing

Comprehensive test coverage in `tests/test_ci_wait.py`:

- ✓ Timeout value verification (30 minutes)
- ✓ Timeout increase verification (from 15 to 30 minutes)
- ✓ Check status and conclusion enums
- ✓ CIWaitResult data class
- ✓ API function mocking
- ✓ Check completion logic
- ✓ Wait behavior (success, timeout, failure)
- ✓ Branch-based waiting
- ✓ CI summary generation
- ✓ Integration scenarios

Run tests:

```bash
# Run all CI wait tests
pytest tests/test_ci_wait.py -v

# Run with coverage
pytest tests/test_ci_wait.py --cov=tools.ci_wait --cov-report=term-missing
```

## Future Enhancements

Potential improvements for future tickets:

1. **Adaptive Polling**: Increase poll interval after first 5 minutes to reduce API calls
2. **Webhook Integration**: Use GitHub webhooks instead of polling for real-time updates
3. **Parallel Monitoring**: Monitor multiple PRs concurrently with asyncio
4. **Configurable Retries**: Add retry logic for transient GitHub API errors
5. **Metrics Collection**: Track CI duration statistics for capacity planning
6. **Slack Notifications**: Alert team when CI times out or takes unusually long

## Troubleshooting

### CI Wait Times Out But Checks Are Still Running

**Cause**: Some checks may take longer than 30 minutes
**Solution**: Consider breaking the PR into smaller changes or optimizing CI pipeline

### False Timeouts with Completed Checks

**Cause**: GitHub API lag or caching
**Solution**: Poll interval allows for eventual consistency; check GitHub UI to confirm

### No Check Runs Found

**Cause**: 
- PR might not trigger CI (e.g., draft PR, CI disabled for branch)
- CI workflow file might have errors
**Solution**: Check GitHub Actions tab and workflow configuration

### Rate Limit Errors

**Cause**: Too many concurrent waits or other API usage
**Solution**: Monitor rate limit headers and reduce concurrent waits

## Related Documentation

- [GitHub Check Runs API](https://docs.github.com/en/rest/checks/runs)
- [GitHub Commit Status API](https://docs.github.com/en/rest/commits/statuses)
- [GitHub Actions Events](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)

## Changelog

### SDT1-64 (Current)
- **Changed**: Timeout increased from 15 to 30 minutes
- **Added**: Comprehensive test coverage
- **Added**: Documentation and usage examples
- **Added**: CI status check methods in github_client.py

### Previous
- **Initial**: 15-minute timeout with 30-second polling
