# Manager Agent Retrigger Loop Prevention

## Overview

The Manager Agent automatically handles merge conflicts by closing conflicted PRs and retriggering Auto Implement to create fresh implementations from the latest `main` branch. However, if conflicts persist across multiple attempts, this can create an infinite loop that wastes resources and never resolves the underlying issue.

**SDT1-60** implements a configurable cap on retrigger attempts to prevent infinite loops.

## How It Works

### Retrigger Tracking

When the Manager Agent detects a merge conflict, it:

1. **Counts previous retrigger attempts** by scanning closed PRs for the same ticket
2. **Checks against the cap** (default: 3 attempts)
3. **Either triggers or blocks** based on the count

### Detection Logic

The system counts a retrigger by looking for:
- PRs with matching ticket key in branch name or title
- Comments containing "Merge conflict detected" or "retriggering"

### Behavior by Attempt Count

| Attempt | Behavior |
|---------|----------|
| 1-2     | Retriggers normally with attempt counter displayed |
| 3       | Last attempt - posts warning that this is the final retry |
| 4+      | **Blocks retrigger**, posts detailed failure message, notifies Jira |

## Configuration

### Environment Variable

```bash
MAX_RETRIGGER_ATTEMPTS=3  # default value
```

Set this in GitHub Actions secrets to customize:

```yaml
env:
  MAX_RETRIGGER_ATTEMPTS: ${{ secrets.MAX_RETRIGGER_ATTEMPTS || '3' }}
```

### Recommended Values

- **3** (default): Good balance for most projects
- **5**: For projects with frequent legitimate conflicts
- **1**: For zero-tolerance testing (not recommended for production)

## Messages

### During Retriggers (Attempts 1-N)

Posted to PR:
```
🔄 **Auto Implement retriggered** (attempt 2/3)

A fresh implementation will be created from the latest `main` branch.
```

### When Cap Reached

Posted to PR:
```
🛑 **Manager Agent: Retrigger cap reached (3 attempts)**

This ticket `SDT1-60` has been retriggered 3 times due to merge conflicts.
Manual intervention is required to resolve the underlying issue.

**Possible causes:**
- Persistent conflicts with files being modified by other PRs
- Ticket requires changes to shared infrastructure files
- Implementation strategy needs manual adjustment

**Next steps:**
1. Review the merge conflicts in the closed PRs
2. Manually implement the ticket or adjust the requirements
3. Check if dependencies need to be updated in Jira
```

Posted to Jira:
```
Auto Implement retrigger cap reached after 3 attempts. Manual intervention required. See PR #123 for details.
```

## Observability

### Logs

The Manager Agent logs retrigger attempts:

```
Triggering Auto Implement for SDT1-60 (attempt 2/3)
Auto Implement triggered for SDT1-60 (attempt 2/3)
```

When cap is reached:
```
RETRIGGER CAP REACHED for SDT1-60: 3 attempts
```

### GitHub

All retrigger attempts leave comments on the closed PRs, creating an audit trail:
1. PR #101: First attempt (original implementation)
2. PR #102: "Auto Implement retriggered (attempt 2/3)"
3. PR #103: "Auto Implement retriggered (attempt 3/3)"
4. PR #104: "Retrigger cap reached (3 attempts)" - workflow NOT dispatched

### Jira

When the cap is reached, a comment is automatically posted to the Jira ticket explaining the failure and requesting manual intervention.

## Common Scenarios

### Scenario 1: Temporary Conflict

**Timeline:**
- Attempt 1: Conflicts with recently merged PR
- Attempt 2: Succeeds after pulling latest main

**Result:** ✅ Resolved automatically

---

### Scenario 2: Persistent Conflict

**Timeline:**
- Attempt 1-3: All conflict with shared file `config.py`
- Attempt 4: Blocked by cap

**Action Required:** 
- Manual review of `config.py` changes
- Either manually implement or split ticket into smaller chunks
- Consider updating execution order in Jira if dependency issue

---

### Scenario 3: Dependency Issue

**Timeline:**
- Ticket depends on SDT1-50 which is stuck
- Attempts 1-3: All conflict with files from SDT1-50

**Action Required:**
- Fix SDT1-50 first
- Update execution_order in Jira to run this ticket after SDT1-50
- Close cap-reached PR manually - will auto-retry once SDT1-50 merges

## Testing

Run the test suite:

```bash
pytest tests/test_ci_manager_agent.py -v
```

Key test cases:
- `test_get_retrigger_count_with_retriggers`: Validates counting logic
- `test_trigger_auto_implement_cap_reached`: Validates blocking behavior
- `test_trigger_auto_implement_tracks_attempt_number`: Validates messaging
- `test_review_pr_handles_conflict_during_merge`: End-to-end conflict handling

## Troubleshooting

### False Positives

**Problem:** Cap reached but conflicts were different each time

**Solution:** Increase `MAX_RETRIGGER_ATTEMPTS` or manually retrigger:
```bash
python ci_manager_agent.py --pr <PR_NUMBER>
```

### False Negatives

**Problem:** Loop continues despite cap

**Cause:** Comments might not contain expected keywords

**Solution:** 
1. Check closed PRs for actual comment text
2. Update detection keywords in `get_retrigger_count()` if needed

### Manual Override

To manually retrigger after cap is reached:

1. Ensure the underlying conflict is resolved
2. Create a new branch manually:
   ```bash
   git checkout main
   git pull
   git checkout -b feature/sdt1-60-manual-fix
   # make changes
   git push
   ```
3. Open PR - this resets the retrigger counter (new branch pattern)

## Architecture

### Key Functions

```python
def get_retrigger_count(ticket_key: str) -> int:
    """Count how many times Auto Implement has been triggered for this ticket."""
    # Scans closed PRs for retrigger comments
    
def trigger_auto_implement(ticket_key, summary, feedback, pr_number) -> bool:
    """Dispatch Auto Implement with loop prevention."""
    # Checks cap before triggering workflow
    # Returns False if cap reached
```

### Integration Points

1. **Review logic** (`review_pr`):
   - Detects merge conflicts
   - Calls `trigger_auto_implement`
   
2. **GitHub API**:
   - Fetches PR history
   - Posts status comments
   
3. **Jira API**:
   - Posts failure notifications
   
4. **GitHub Actions**:
   - Receives workflow dispatch if under cap
   - Auto Implement workflow starts fresh implementation

## Migration Notes

This feature is **backward compatible**:
- Existing PRs are unaffected
- Default cap (3) matches expected behavior
- No configuration changes required

To roll back, simply revert to the previous version of `ci_manager_agent.py`.

## Related Tickets

- **SDT1-29**: Original Auto Review implementation
- **SDT1-60**: This feature (retrigger loop prevention)
- **SDT1-36**: Dependency management (related to execution order)
