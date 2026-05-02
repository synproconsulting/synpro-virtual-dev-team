# Manager Agent Retrigger Loop Protection

## Overview

The Manager Agent includes built-in protection against infinite retrigger loops. This feature prevents scenarios where workflow automation continuously retriggers the same operation, consuming resources and potentially causing system instability.

## Problem Statement

In automated workflow systems, certain conditions can create infinite loops:

1. **Network Transients**: Temporary network issues cause operations to fail and retry indefinitely
2. **Workflow Misconfigurations**: Incorrectly configured workflows that retrigger on certain states
3. **Race Conditions**: Concurrent operations that interfere with each other
4. **External System Issues**: Downstream systems (Jira, GitHub) experiencing problems that don't resolve quickly

Without protection, these scenarios can:
- Consume excessive API quota
- Generate spam in issue trackers
- Prevent other work from progressing
- Mask underlying problems
- Cause service degradation

## Solution: Retrigger Loop Cap

The Manager Agent implements a configurable cap on operation retriggers with the following features:

### 1. Operation State Tracking

Each operation is uniquely identified by:
- **Operation Type**: `start_work`, `complete_work`, `move_to_code_review`, `move_to_testing`
- **Issue Key**: The Jira issue being operated on (e.g., "SDT1-60")

This creates an **Operation ID**: `operation_type:issue_key` (e.g., `start_work:SDT1-60`)

### 2. Trigger Counting

For each operation:
- **First Trigger**: Counter initialized to 1
- **Subsequent Triggers**: Counter incremented
- **Success**: Counter reset to 0 (operation state deleted)
- **Failure**: Counter preserved, error recorded

### 3. Limit Enforcement

When trigger count reaches `max_retrigger_count`:
- `RetriggerLimitExceeded` exception raised
- Exception includes:
  - Operation ID
  - Current and maximum counts
  - Operation state summary
  - Error history

### 4. Error History

Each failed trigger records:
- Error message
- Timestamp of first trigger
- Timestamp of last trigger
- Count of errors

## Configuration

### Default Configuration

```python
from agents.manager_agent import create_manager_agent

# Uses default max_retrigger_count = 3
agent = create_manager_agent()
```

### Custom Configuration

```python
# More aggressive limit for testing environments
agent = create_manager_agent(max_retrigger_count=1)

# Higher limit for production with known transient issues
agent = create_manager_agent(max_retrigger_count=5)

# Full configuration
agent = create_manager_agent(
    max_retries=5,           # API retry attempts (separate from retrigger)
    max_retrigger_count=3,   # Operation retrigger limit
    base_delay=1.0,          # Exponential backoff base
    diff_max_chars=50000,    # PR diff truncation limit
)
```

### Configuration Guidelines

| Environment | Recommended Limit | Rationale |
|-------------|------------------|-----------|
| Development | 1-2 | Fail fast to expose issues |
| Testing | 2-3 | Balance between stability and issue detection |
| Staging | 3-5 | Allow for transient issues |
| Production | 3-5 | Protect against runaway loops while handling transients |

## Usage Examples

### Basic Usage

```python
import asyncio
from agents.manager_agent import create_manager_agent, RetriggerLimitExceeded

async def main():
    agent = create_manager_agent(max_retrigger_count=3)
    
    try:
        result = await agent.start_work("SDT1-60")
        print(f"Success! Retrigger count: {result.retrigger_count}")
    except RetriggerLimitExceeded as e:
        print(f"Limit exceeded: {e}")
        # Handle the error appropriately

asyncio.run(main())
```

### Monitoring Operation States

```python
# Check specific operation
state = agent.get_operation_state("start_work", "SDT1-60")
if state:
    print(f"Operation ID: {state['operation_id']}")
    print(f"Trigger count: {state['trigger_count']}")
    print(f"Error count: {state['error_count']}")
    print(f"Recent errors: {state['recent_errors']}")
    print(f"First triggered: {state['first_triggered_at']}")
    print(f"Last triggered: {state['last_triggered_at']}")
```

### Monitoring All Operations

```python
# Get all tracked operations
all_states = agent.get_all_operation_states()

for state in all_states:
    if state['trigger_count'] >= 2:
        print(f"⚠ Warning: {state['operation_id']} approaching limit")
        print(f"  Trigger count: {state['trigger_count']}")
        print(f"  Recent errors: {state['recent_errors']}")
```

### Clearing Operation States

```python
# Clear all states (e.g., after manual intervention)
cleared_count = agent.clear_all_operation_states()
print(f"Cleared {cleared_count} operation states")

# Or clear specific operation after resolving the issue
agent._reset_retrigger_count("start_work", "SDT1-60")
```

### Integration with Orchestrator

```python
async def execute_ticket_with_protection(agent, issue_key):
    """Execute a ticket with retrigger protection."""
    try:
        # Start work
        result = await agent.start_work(issue_key)
        if result.status != TransitionStatus.SUCCESS:
            raise Exception(f"Failed to start work: {result.error_message}")
        
        # ... implementation work happens ...
        
        # Move to code review
        result = await agent.move_to_code_review(issue_key)
        if result.status != TransitionStatus.SUCCESS:
            raise Exception(f"Failed to move to review: {result.error_message}")
        
    except RetriggerLimitExceeded as e:
        # Log the issue and move on
        print(f"Retrigger limit exceeded for {issue_key}: {e}")
        
        # Get state for debugging
        for operation_type in ["start_work", "move_to_code_review"]:
            state = agent.get_operation_state(operation_type, issue_key)
            if state:
                print(f"State for {operation_type}: {state}")
        
        # Clear states and mark for manual intervention
        agent.clear_all_operation_states()
        raise TicketExecutionError(f"Manual intervention required for {issue_key}")
```

## How It Works: Detailed Flow

### Successful Operation Flow

```
1. Orchestrator calls agent.start_work("SDT1-60")
   ↓
2. Manager Agent checks retrigger count
   - Operation ID: "start_work:SDT1-60" not found
   - Create new OperationState with trigger_count=1
   ↓
3. Execute Jira API call
   - Success! Transition to "In Progress"
   ↓
4. Reset retrigger count
   - Delete OperationState for "start_work:SDT1-60"
   ↓
5. Return TransitionResult
   - status: SUCCESS
   - retrigger_count: 1
```

### Failed Operation with Retrigger

```
1. Orchestrator calls agent.move_to_code_review("SDT1-60")
   ↓
2. Manager Agent checks retrigger count
   - Operation ID: "move_to_code_review:SDT1-60" not found
   - Create new OperationState with trigger_count=1
   ↓
3. Execute Jira API call
   - Failure! Network timeout
   ↓
4. Record error in OperationState
   - error_history: ["Network timeout"]
   - trigger_count remains 1
   ↓
5. Return TransitionResult
   - status: FAILED
   - error_message: "Network timeout"
   - retrigger_count: 1
   ↓
6. Orchestrator retriggers agent.move_to_code_review("SDT1-60")
   ↓
7. Manager Agent checks retrigger count
   - Operation ID: "move_to_code_review:SDT1-60" found
   - Increment trigger_count to 2
   ↓
8. Execute Jira API call
   - Still failing! Network timeout
   ↓
9. Record error
   - error_history: ["Network timeout", "Network timeout"]
   - trigger_count remains 2
   ↓
10. Orchestrator retriggers agent.move_to_code_review("SDT1-60")
    ↓
11. Manager Agent checks retrigger count
    - trigger_count=3 equals max_retrigger_count
    - Raise RetriggerLimitExceeded exception
    ↓
12. Orchestrator catches exception
    - Log error
    - Clear operation states
    - Mark ticket for manual intervention
```

### Different Operations Are Independent

```
Scenario: start_work succeeds but move_to_code_review fails

1. agent.start_work("SDT1-60")
   - trigger_count: 1
   - Success → count reset
   
2. agent.move_to_code_review("SDT1-60")
   - trigger_count: 1 (different operation ID)
   - Failure → count preserved
   
3. Retry: agent.move_to_code_review("SDT1-60")
   - trigger_count: 2
   - Failure → count preserved
   
4. Retry: agent.move_to_code_review("SDT1-60")
   - trigger_count: 3
   - Failure → count preserved
   
5. Retry: agent.move_to_code_review("SDT1-60")
   - RetriggerLimitExceeded raised
   
6. agent.start_work("SDT1-61")
   - Different issue, different operation ID
   - trigger_count: 1
   - Works fine!
```

## API Reference

### Exception: `RetriggerLimitExceeded`

Raised when an operation exceeds its retrigger limit.

```python
class RetriggerLimitExceeded(Exception):
    """Exception raised when retrigger limit is exceeded."""
    pass
```

### Class: `OperationState`

Tracks the state of an operation to prevent infinite retrigger loops.

**Attributes:**
- `operation_id` (str): Unique identifier for the operation
- `issue_key` (str): Jira issue key
- `operation_type` (str): Type of operation
- `trigger_count` (int): Number of times operation has been triggered
- `first_triggered_at` (datetime): Timestamp of first trigger
- `last_triggered_at` (datetime): Timestamp of most recent trigger
- `error_history` (List[str]): List of error messages

**Methods:**
- `increment_trigger(error_message: Optional[str] = None) -> int`: Increment trigger count
- `is_limit_exceeded(max_count: int) -> bool`: Check if limit exceeded
- `get_summary() -> Dict[str, Any]`: Get operation state summary

### ManagerAgent Methods

**Retrigger Management:**

```python
def _check_and_increment_retrigger(
    self,
    operation_type: str,
    issue_key: str,
    error_message: Optional[str] = None,
) -> int:
    """Check retrigger count and increment. Raises RetriggerLimitExceeded if limit exceeded."""
    
def _reset_retrigger_count(
    self,
    operation_type: str,
    issue_key: str,
) -> None:
    """Reset retrigger count for an operation (e.g., after success)."""
    
def get_operation_state(
    self,
    operation_type: str,
    issue_key: str,
) -> Optional[Dict[str, Any]]:
    """Get current state of an operation."""
    
def get_all_operation_states(self) -> List[Dict[str, Any]]:
    """Get all tracked operation states."""
    
def clear_all_operation_states(self) -> int:
    """Clear all tracked operation states. Returns number of states cleared."""
```

**Workflow Operations (all protected by retrigger cap):**

```python
async def start_work(
    self,
    issue_key: str,
    assignee: Optional[str] = None,
    comment: Optional[str] = None,
) -> TransitionResult:
    """Transition an issue to 'In Progress' status."""
    
async def complete_work(
    self,
    issue_key: str,
    comment: Optional[str] = None,
) -> TransitionResult:
    """Transition an issue to 'Done' status."""
    
async def move_to_code_review(
    self,
    issue_key: str,
    comment: Optional[str] = None,
) -> TransitionResult:
    """Transition an issue to 'Code Review' status."""
    
async def move_to_testing(
    self,
    issue_key: str,
    comment: Optional[str] = None,
) -> TransitionResult:
    """Transition an issue to 'Testing' or 'QA' status."""
    
async def review_and_comment_pr(
    self,
    issue_key: str,
    diff_text: str,
) -> Tuple[DiffReviewResult, TransitionResult]:
    """Review a PR diff and post review comments to Jira."""
```

## Best Practices

### 1. Choose Appropriate Limits

```python
# Development: Fail fast
dev_agent = create_manager_agent(max_retrigger_count=1)

# Production: Allow for transients
prod_agent = create_manager_agent(max_retrigger_count=3)
```

### 2. Monitor Operation States

```python
# Regular health check
def check_agent_health(agent):
    states = agent.get_all_operation_states()
    high_count = [s for s in states if s['trigger_count'] >= 2]
    
    if high_count:
        for state in high_count:
            print(f"Warning: {state['operation_id']} at {state['trigger_count']} triggers")
            print(f"Recent errors: {state['recent_errors']}")
```

### 3. Handle Exceptions Gracefully

```python
async def safe_transition(agent, operation, issue_key, **kwargs):
    """Execute transition with proper error handling."""
    try:
        operation_func = getattr(agent, operation)
        result = await operation_func(issue_key, **kwargs)
        
        if result.status == TransitionStatus.SUCCESS:
            print(f"✓ {operation} succeeded for {issue_key}")
            return result
        else:
            print(f"✗ {operation} failed for {issue_key}: {result.error_message}")
            return result
            
    except RetriggerLimitExceeded as e:
        print(f"⚠ Retrigger limit exceeded for {operation} on {issue_key}")
        
        # Get operation state for debugging
        state = agent.get_operation_state(operation, issue_key)
        if state:
            print(f"Operation state: {state}")
        
        # Clear state and re-raise for orchestrator to handle
        agent._reset_retrigger_count(operation, issue_key)
        raise
```

### 4. Clear States After Manual Intervention

```python
# After manually fixing an issue in Jira
agent._reset_retrigger_count("move_to_code_review", "SDT1-60")

# Or clear all if multiple issues were fixed
agent.clear_all_operation_states()
```

### 5. Log Retrigger Events

```python
import logging

logger = logging.getLogger(__name__)

async def execute_with_logging(agent, operation, issue_key):
    try:
        result = await getattr(agent, operation)(issue_key)
        
        # Log retrigger count
        if result.retrigger_count > 1:
            logger.warning(
                f"{operation} on {issue_key} required {result.retrigger_count} triggers"
            )
        
        return result
        
    except RetriggerLimitExceeded as e:
        logger.error(f"Retrigger limit exceeded: {e}")
        raise
```

## Troubleshooting

### Symptom: RetriggerLimitExceeded raised frequently

**Possible Causes:**
1. Network connectivity issues
2. Jira API rate limiting
3. Invalid workflow transitions
4. External system downtime

**Solutions:**
1. Check network connectivity and DNS resolution
2. Verify Jira API credentials and quotas
3. Validate workflow transitions are available for issue type
4. Increase `max_retrigger_count` if transients are expected
5. Implement backoff at orchestrator level

### Symptom: Operation states not clearing after success

**Possible Causes:**
1. Exception raised before state reset
2. Bug in state management logic

**Solutions:**
1. Check logs for exceptions during operation
2. Manually clear states: `agent.clear_all_operation_states()`
3. Review operation code flow

### Symptom: Different operations interfering with each other

**Possible Causes:**
1. Bug in operation ID generation

**Solutions:**
1. Verify operation IDs are unique: `operation_type:issue_key`
2. Check that different operations have different operation_type values

## Testing

### Unit Tests

```bash
# Test retrigger protection specifically
pytest agents/tests/test_manager_agent.py::TestManagerAgentRetrigger -v

# Test operation state tracking
pytest agents/tests/test_manager_agent.py::TestOperationState -v
```

### Integration Tests

```python
# Test scenario: Operation fails multiple times then succeeds
@pytest.mark.asyncio
async def test_retrigger_recovery():
    agent = create_manager_agent(max_retrigger_count=3)
    
    with patch.object(agent.client, "transition_issue_by_name") as mock:
        # Fail twice, then succeed
        mock.side_effect = [
            TransitionResult(status=TransitionStatus.FAILED, 
                           error_message="Temp failure"),
            TransitionResult(status=TransitionStatus.FAILED, 
                           error_message="Temp failure"),
            TransitionResult(status=TransitionStatus.SUCCESS),
        ]
        
        # First two calls fail but don't raise
        await agent.start_work("TEST-1")
        await agent.start_work("TEST-1")
        
        # Third succeeds and resets counter
        result = await agent.start_work("TEST-1")
        assert result.status == TransitionStatus.SUCCESS
        
        # Fourth call works (counter was reset)
        result = await agent.start_work("TEST-1")
        assert result.status == TransitionStatus.SUCCESS
```

## Future Enhancements

1. **Persistent State**: Store operation states in database for cross-restart tracking
2. **Configurable Per-Operation Limits**: Different limits for different operation types
3. **Time-Based Reset**: Auto-reset counts after time period
4. **Metrics Export**: Export retrigger metrics to monitoring systems
5. **Adaptive Limits**: Dynamically adjust limits based on success rate
6. **Circuit Breaker**: Temporarily disable operations after repeated failures

## Related Documentation

- [Manager Agent README](../agents/README.md)
- [Orchestrator Documentation](./orchestrator_resume_capability.md)
- [Jira Integration Guide](./jira_integration.md)
