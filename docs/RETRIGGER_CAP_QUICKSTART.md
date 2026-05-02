# Manager Agent Retrigger Cap - Quick Start

## 🎯 What This Fixes

Prevents infinite loops when PRs repeatedly fail with merge conflicts. Instead of creating dozens of failed PRs, the system now:
- Tries up to **3 times** (configurable)
- Then **stops** and alerts you
- Provides **clear next steps**

## 🔍 How to Tell If It's Working

### Normal Retrigger (Attempts 1-3)

Look for this comment on closed PRs:

```
🔄 Auto Implement retriggered (attempt 2/3)

A fresh implementation will be created from the latest `main` branch.
```

✅ **This is expected** - the system is handling conflicts automatically.

### Cap Reached (Attempt 4+)

Look for this comment:

```
🛑 Manager Agent: Retrigger cap reached (3 attempts)

This ticket `SDT1-XX` has been retriggered 3 times due to merge conflicts.
Manual intervention is required to resolve the underlying issue.
```

⚠️ **Action required** - see troubleshooting below.

## 🛠️ Troubleshooting

### When Cap is Reached

**Step 1: Check Jira**
- Open the ticket in Jira
- Look for a comment explaining the cap was reached
- Note any patterns in the conflict messages

**Step 2: Review Closed PRs**
- Find all closed PRs for this ticket (search: `[TICKET-KEY]`)
- Look at the file conflicts in each PR
- Identify if the same files conflict each time

**Step 3: Common Fixes**

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Same file conflicts each time | Another PR is modifying that file | Wait for that PR to merge first |
| Config file conflicts | Shared infrastructure change | Manually merge or adjust ticket scope |
| Multiple file conflicts | Wrong execution order | Update `execution_order` in Jira |
| Test file conflicts | Test data changes on main | Rebase and manually resolve |

**Step 4: Resolution Options**

**Option A: Wait and retry** (if another PR is the cause)
1. Wait for the conflicting PR to merge
2. Manually trigger: `workflow_dispatch` → `auto-implement.yml`
3. Use ticket key and summary from original ticket

**Option B: Manual implementation**
1. Create branch: `feature/[ticket-key]-manual-fix`
2. Implement the ticket manually
3. Ensure tests pass
4. Open PR normally

**Option C: Adjust ticket**
1. Break ticket into smaller pieces
2. Update dependencies in Jira
3. Change execution order if needed

## ⚙️ Configuration

### Default Settings

```yaml
MAX_RETRIGGER_ATTEMPTS: 3  # default
```

### Customize (if needed)

Add to GitHub Actions secrets:

```
MAX_RETRIGGER_ATTEMPTS = 5
```

Then update `.github/workflows/auto-review.yml`:

```yaml
env:
  MAX_RETRIGGER_ATTEMPTS: ${{ secrets.MAX_RETRIGGER_ATTEMPTS || '3' }}
```

### Recommended Values

- **1**: Testing only (stops after first conflict)
- **3**: Production default (good balance)
- **5**: High-conflict environments
- **10+**: Not recommended (defeats the purpose)

## 📊 Monitoring

### GitHub Actions Logs

Search for:
```
Triggering Auto Implement for SDT1-XX (attempt N/3)
```

or

```
RETRIGGER CAP REACHED for SDT1-XX: 3 attempts
```

### PR Comments

Each closed PR from a retrigger has a comment with:
- Attempt number
- Reason for closing (merge conflict)
- Next steps

### Jira

Tickets that hit the cap get a comment:
```
Auto Implement retrigger cap reached after 3 attempts.
Manual intervention required. See PR #XXX for details.
```

## 🧪 Testing

### Unit Tests

```bash
pytest tests/test_ci_manager_agent.py -v
```

### Integration Tests

```bash
RUN_INTEGRATION_TESTS=1 pytest tests/integration/test_retrigger_loop_prevention.py -v -s
```

### Manual Test

1. Create a test ticket with known conflicts
2. Trigger Auto Implement 4 times
3. Verify cap message appears on 4th attempt

## 📞 Support

### Check Status

```bash
# Count retriggers for a ticket
python -c "
import ci_manager_agent as agent
import os
os.environ['GITHUB_TOKEN'] = 'your-token'
os.environ['GITHUB_USERNAME'] = 'your-username'
os.environ['GITHUB_REPO'] = 'your-repo'
print(agent.get_retrigger_count('SDT1-XX'))
"
```

### Force Retrigger (emergency)

If you've fixed the issue and need to bypass the cap:

```bash
# Create a new branch with different name
git checkout -b feature/sdt1-xx-manual-v2
# ... implement ...
git push
# Open PR - this resets the counter
```

### Logs

Check these logs when debugging:
- **GitHub Actions**: Workflow run logs for auto-implement and auto-review
- **PR Comments**: Full audit trail of retrigger attempts
- **Jira Comments**: Status updates and cap notifications

## 🔗 Related Docs

- [Full Documentation](./manager-agent-retrigger-cap.md)
- [Changelog](./CHANGELOG.md)
- [Auto Review Workflow](../.github/workflows/auto-review.yml)

## ⚡ Quick Commands

```bash
# Run unit tests
pytest tests/test_ci_manager_agent.py::TestRetriggerLoopPrevention -v

# Check retrigger count (replace values)
export GITHUB_TOKEN=your_token
export GITHUB_USERNAME=your_username
export GITHUB_REPO=your_repo
python -c "import ci_manager_agent; print(agent.get_retrigger_count('SDT1-60'))"

# View cap setting
python -c "import ci_manager_agent; print(f'Cap: {agent.MAX_RETRIGGER_ATTEMPTS}')"
```
