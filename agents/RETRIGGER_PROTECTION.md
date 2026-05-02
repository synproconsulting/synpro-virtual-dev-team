# Manager Agent Retrigger Loop Protection

## Overview

The Manager Agent now includes built-in protection against infinite retrigger loops. This feature prevents scenarios where the same operation is repeatedly attempted on the same Jira issue, which could lead to:

- API rate limiting
- Excessive resource consumption
- System instability
- Workflow deadlocks

## How It Works

### RetriggerTracker

The `RetriggerTracker` class monitors all Manager Agent operations on a per-issue, per-operation basis:

1. **Tracking Window**: Monitors retriggers within a configurable time window (default: 1 hour)
2. **Maximum Retriggers**: Enforces a limit on retrigger attempts (default: 3)
3. **Cooldown Period**: Applies a mandatory cooldown after hitting the limit (default: 5 minutes)
4. **Automatic Cleanup**: Removes old attempts outside the tracking window

### Protected Operations

All Manager Agent workflow operations are protected:

- `start_work()` - Transition to "In Progress"
- `complete_work()` - Transition to "Done"
- `move_to_code_review()` - Transition to "Code Review"
- `move_to_testing()` - Transition to "Testing" or "QA"

## Configuration

### Environment Variables

Set these environment variables to configure retrigger protection globally:

```bash
# Maximum retriggers allowed within the time window
MANAGER_AGENT_MAX_RETRIGGERS=3

# Time window in seconds to track retriggers
MANAGER_AGENT_RETRIGGER_WINDOW=3600

# Cooldown period in seconds after hitting limit
MANAGER_AGENT_COOLDOWN_PERIOD=300
```

### Programmatic Configuration

Configure retrigger protection when creating the Manager Agent:

```python
from agents.manager_agent import create_manager_agent

# Create agent with custom retrigger limits
agent = create_manager_agent(
    max_retriggers=5,          # Allow 5 retriggers
    retrigger_window=7200,     # Within 2 hours
    enable_retrigger_protection=True  # Enable protection (default)
)
```

### Disabling Protection

For testing or special scenarios, you can disable retrigger protection:

```python
agent = create_manager_agent(
    enable_retrigger_protection=False
)
```

⚠️ **Warning**: Only disable protection in controlled environments. Production systems should always have protection enabled.

## Usage Examples

### Basic Usage

The retrigger protection works automatically:

```python
import asyncio
from agents.manager_agent import create_manager_agent

async def main():
    agent = create_manager_agent(max_retriggers=3)
    
    # These will succeed (1st, 2nd, 3rd retrigger)
    result1 = await agent.start_work("SDT1-100")
    result2 = await agent.start_work("SDT1-100")
    result3 = await agent.start_work("SDT1-100")
    
    # This will be blocked (4th retrigger)
    result4 = await agent.start_work("SDT1-100")
    
    if result4.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED:
        print(f"Blocked: {result4.error_message}")
        print(f"Retrigger count: {result4.retrigger_count}")

asyncio.run(main())
```

### Checking Retrigger Status

Check if an operation is allowed before attempting:

```python
can_retrigger, reason = agent.retrigger_tracker.can_retrigger(
    "SDT1-100", 
    "start_work"
)

if can_retrigger:
    result = await agent.start_work("SDT1-100")
else:
    print(f"Cannot retrigger: {reason}")
```

### Manual Reset

Reset retrigger tracking after fixing an issue:

```python
# Reset a specific operation
agent.reset_retriggers("SDT1-100", "start_work")

# Reset all operations for an issue
agent.reset_retriggers("SDT1-100")
```

### Monitoring

Get statistics about retrigger tracking:

```python
stats = agent.get_retrigger_stats()

print(f"Tracked operations: {stats['tracked_operations']}")
print(f"Total attempts: {stats['total_attempts']}")
print(f"Active cooldowns: {stats['active_cooldowns']}")
print(f"Max retriggers: {stats['max_retriggers']}")
print(f"Window: {stats['window_seconds']} seconds")
```

## Return Values

When an operation is blocked, the `TransitionResult` will have:

```python
TransitionResult(
    status=TransitionStatus.MAX_RETRIGGERS_EXCEEDED,
    issue_key="SDT1-100",
    error_message="Maximum retrigger limit (3) exceeded for operation 'start_work' ...",
    retrigger_count=3,  # Number of retriggers within window
)
```

## Best Practices

### 1. Set Appropriate Limits

Choose limits based on your workflow:

- **Development/Testing**: Lower limits (2-3 retriggers) to catch issues quickly
- **Production**: Higher limits (5-8 retriggers) to handle transient failures
- **CI/CD Pipelines**: Moderate limits (3-5 retriggers) with automatic resets

### 2. Monitor Retrigger Events

Log when retriggers are blocked:

```python
result = await agent.start_work(issue_key)

if result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED:
    logger.warning(
        f"Retrigger blocked for {issue_key}: {result.error_message}",
        extra={
            "issue_key": issue_key,
            "operation": "start_work",
            "retrigger_count": result.retrigger_count,
        }
    )
```

### 3. Handle Blocked Operations Gracefully

Don't fail silently when operations are blocked:

```python
result = await agent.start_work(issue_key)

if result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED:
    # Alert operations team
    send_alert(f"Retrigger loop detected for {issue_key}")
    
    # Mark issue for manual review
    await mark_for_manual_review(issue_key)
    
    # Log to monitoring system
    metrics.increment("manager_agent.retrigger_blocked")
```

### 4. Use Resets Carefully

Only reset retrigger tracking when:

- You've identified and fixed the root cause
- Manual intervention is required
- Testing workflows in development

```python
# Good: Reset after fixing the issue
if issue_resolved(issue_key):
    agent.reset_retriggers(issue_key)
    result = await agent.start_work(issue_key)

# Bad: Blindly resetting on every failure
# This defeats the purpose of protection
```

### 5. Different Operations Are Independent

Operations are tracked separately, so blocking `start_work` doesn't affect `complete_work`:

```python
# These are tracked independently
await agent.start_work("SDT1-100")  # Track: ("SDT1-100", "start_work")
await agent.complete_work("SDT1-100")  # Track: ("SDT1-100", "complete_work")
```

## Troubleshooting

### Operation Blocked Unexpectedly

**Symptom**: Operations are blocked even though you haven't called them many times.

**Possible Causes**:
1. Old attempts within the tracking window
2. Cooldown period still active
3. Multiple processes calling the same operation

**Solution**:
```python
# Check retrigger count
count = agent.retrigger_tracker.get_retrigger_count(issue_key, operation)
print(f"Current retrigger count: {count}")

# Check if in cooldown
can_retrigger, reason = agent.retrigger_tracker.can_retrigger(issue_key, operation)
print(f"Can retrigger: {can_retrigger}, Reason: {reason}")

# If appropriate, reset tracking
agent.reset_retriggers(issue_key, operation)
```

### Too Many False Positives

**Symptom**: Legitimate operations are being blocked too frequently.

**Solution**: Increase the retrigger limit or window:

```python
agent = create_manager_agent(
    max_retriggers=10,      # Increase from default 3
    retrigger_window=7200,  # Increase to 2 hours
)
```

### Infinite Loops Still Occurring

**Symptom**: System still experiences infinite loops despite protection.

**Possible Causes**:
1. Protection disabled
2. Different operations being called in rotation
3. Multiple agent instances with separate trackers

**Solution**:
1. Verify protection is enabled
2. Implement shared state (database-backed tracker)
3. Add circuit breakers at the workflow level

## Implementation Details

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Manager Agent                                                │
│                                                               │
│  ┌───────────────────┐         ┌──────────────────────┐    │
│  │ Public Methods    │────────▶│ RetriggerTracker     │    │
│  │                   │         │                       │    │
│  │ • start_work()    │         │ • can_retrigger()    │    │
│  │ • complete_work() │         │ • record_retrigger() │    │
│  │ • move_to_*()     │         │ • reset_retriggers() │    │
│  └───────────────────┘         └──────────────────────┘    │
│           │                              │                   │
│           │                              │                   │
│           ▼                              ▼                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │ JiraRetryClient (HTTP retry logic)                  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Data Structures

```python
# Tracking key
(issue_key: str, operation: str) -> Tuple[str, str]

# Attempt history
{
    ("SDT1-100", "start_work"): [
        RetriggerAttempt(timestamp=..., operation="start_work", ...),
        RetriggerAttempt(timestamp=..., operation="start_work", ...),
    ]
}

# Cooldown tracking
{
    ("SDT1-100", "start_work"): datetime(2024, 1, 15, 14, 30, 0)
}
```

### Time Window Sliding

The tracker uses a sliding window:

```
Time →
│←──────── 1 hour window ────────→│
├─────┬─────┬─────┬─────┬─────┬──┤
   ❌    ❌    ✓     ✓     ✓    Now
 (old) (old)        (counted)
```

Attempts older than the window are automatically removed.

## Testing

Run the comprehensive test suite:

```bash
# Run all Manager Agent tests
pytest agents/tests/test_manager_agent.py -v

# Run only retrigger protection tests
pytest agents/tests/test_manager_agent.py::TestRetriggerTracker -v
pytest agents/tests/test_manager_agent.py::TestRetriggerProtection -v

# Run with coverage
pytest agents/tests/test_manager_agent.py --cov=agents.manager_agent --cov-report=html
```

## Migration Guide

### Existing Code

Existing code will continue to work with retrigger protection enabled by default:

```python
# Old code - still works, now with protection
agent = create_manager_agent()
result = await agent.start_work("SDT1-100")
```

### Handling New Status

Update code to handle the new status:

```python
result = await agent.start_work("SDT1-100")

# Old code only checked for SUCCESS/FAILED
if result.status == TransitionStatus.SUCCESS:
    # Handle success
elif result.status == TransitionStatus.FAILED:
    # Handle failure

# New code should also check for MAX_RETRIGGERS_EXCEEDED
elif result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED:
    # Handle retrigger loop detection
    logger.error(f"Retrigger loop detected: {result.error_message}")
```

## Performance Impact

The retrigger protection has minimal performance overhead:

- **Memory**: O(n) where n = number of unique (issue, operation) combinations
- **CPU**: O(1) for checks, O(m) for cleanup where m = attempts per operation
- **Latency**: < 1ms additional latency per operation

Automatic cleanup ensures memory usage stays bounded even for long-running processes.

## Future Enhancements

Potential improvements being considered:

1. **Persistent Storage**: Store tracking data in database for multi-instance deployments
2. **Metrics Export**: Export retrigger metrics to Prometheus/Grafana
3. **Adaptive Limits**: Automatically adjust limits based on error rates
4. **Circuit Breaker Integration**: Integrate with circuit breaker patterns
5. **Notification Hooks**: Call webhooks when retriggers are blocked

## Support

For questions or issues related to retrigger protection:

1. Check this documentation
2. Review test cases in `agents/tests/test_manager_agent.py`
3. File an issue with detailed logs and reproduction steps
