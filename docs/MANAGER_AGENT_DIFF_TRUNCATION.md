# Manager Agent Diff Truncation

## Overview

The Manager Agent now includes intelligent diff truncation logic that prioritizes new files over modified files when reviewing pull requests. This ensures that the most important changes (new files) are always included in code reviews, even when dealing with large PRs that exceed token limits.

## Feature: Smart Diff Truncation

### Problem

When reviewing large pull requests, the entire diff may exceed LLM token limits. Naively truncating the diff (e.g., by character count) can result in important changes being excluded from the review, particularly new files that represent the core of the feature being implemented.

### Solution

The Manager Agent now uses a priority-based truncation algorithm that:

1. **Prioritizes new files** - New files always get the highest priority
2. **Ranks modified files by size** - Smaller changes are more likely to be reviewed completely
3. **Deprioritizes deleted files** - Deleted code is least critical for review
4. **Respects minimum file count** - Ensures at least N files are included even if slightly exceeding limits
5. **Provides transparency** - Clear reporting of what was truncated and why

### Priority Scoring Algorithm

Files are assigned priority scores based on their change type and size:

```python
Priority Order:
1. NEW files:      10,000 - size (highest priority)
2. MODIFIED files:  5,000 - size (medium priority)  
3. RENAMED files:   2,500 - size (low priority)
4. DELETED files:   1,000 - size (lowest priority)
```

Within each category, smaller changes receive higher priority scores, making them more likely to be included in full.

## API Endpoints

### POST `/api/manager-agent/review-pr`

Review a GitHub pull request with intelligent diff truncation.

**Request:**
```json
{
  "owner": "myorg",
  "repo": "myrepo",
  "pr_number": 123,
  "ticket_key": "SDT1-46",
  "max_diff_chars": 50000
}
```

**Response:**
```json
{
  "review": "## Summary\n...",
  "diff_summary": "Total: 5 files changed, 2 new, 3 modified (+150 -30 lines)",
  "truncation_info": {
    "total_files": 5,
    "included_files": 3,
    "excluded_files": 2,
    "excluded_file_list": ["old_large_file.py", "deleted.py"],
    "total_size": 75000,
    "truncated_size": 48000
  },
  "success": true
}
```

### POST `/api/manager-agent/truncate-diff`

Standalone endpoint to test diff truncation logic.

**Request:**
```json
{
  "files": [
    {
      "filename": "new_feature.py",
      "status": "added",
      "additions": 100,
      "deletions": 0,
      "patch": "@@ diff content @@"
    }
  ],
  "max_chars": 50000,
  "min_files": 3
}
```

**Response:**
```json
{
  "truncated_diff": "=====...",
  "summary": {
    "total_files": 5,
    "included_files": 3,
    "excluded_files": 2,
    "total_size": 75000,
    "truncated_size": 48000,
    "excluded_file_list": ["large_file.py"],
    "diff_summary": "Total: 5 files changed, 2 new, 3 modified"
  },
  "success": true
}
```

### GET `/api/manager-agent/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "manager-agent",
  "features": [
    "smart_diff_truncation",
    "new_file_prioritization",
    "pr_review"
  ]
}
```

## Usage Examples

### Basic PR Review

```python
import httpx

async def review_pr():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/manager-agent/review-pr",
            json={
                "owner": "synpro",
                "repo": "virtual-dev-team",
                "pr_number": 42,
                "ticket_key": "SDT1-46"
            }
        )
        result = response.json()
        print(result["review"])
        
        if result.get("truncation_info"):
            print(f"Excluded {result['truncation_info']['excluded_files']} files")
```

### Custom Diff Truncation

```python
# Test truncation logic with custom files
files = [
    {
        "filename": "new_feature.py",
        "status": "added",
        "additions": 200,
        "deletions": 0,
        "patch": "... diff content ..."
    },
    {
        "filename": "config.py", 
        "status": "modified",
        "additions": 10,
        "deletions": 5,
        "patch": "... diff content ..."
    }
]

response = await client.post(
    "http://localhost:8000/api/manager-agent/truncate-diff",
    json={
        "files": files,
        "max_chars": 10000,
        "min_files": 2
    }
)

print(response.json()["truncated_diff"])
```

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY` - Required for AI-powered code reviews
- `GITHUB_TOKEN` - Required for fetching PR data from GitHub API

### Default Settings

- `max_diff_chars`: 50,000 characters (configurable per request)
- `min_files`: 3 files minimum (even if exceeding char limit)
- Model: `claude-sonnet-4-5` (Claude 3.5 Sonnet)
- Review max tokens: 3,000

## Truncation Output Format

When files are excluded due to truncation, a clear notice is appended to the diff:

```
================================================================================
DIFF TRUNCATED: 3 files excluded to fit token limit

Excluded NEW files (1):
  - new_large_component.tsx (+500 -0)

Excluded MODIFIED files (2):
  - legacy_module.py (+200 -180)
  - vendor/library.js (+100 -95)

================================================================================
```

This ensures reviewers understand:
- What was truncated
- Why it was truncated (token limits)
- Which specific files were excluded
- The size of excluded changes

## Testing

Comprehensive tests are available in `uat/backend/tests/test_manager_agent.py`:

```bash
# Run all manager agent tests
pytest uat/backend/tests/test_manager_agent.py -v

# Run specific test
pytest uat/backend/tests/test_manager_agent.py::test_truncate_diff_smart_prioritizes_new_files -v

# Run with coverage
pytest uat/backend/tests/test_manager_agent.py --cov=manager_agent --cov-report=html
```

### Key Test Scenarios

1. **Priority ordering** - Verifies new files > modified files > deleted files
2. **Size-based prioritization** - Smaller changes get higher priority within categories
3. **Minimum files guarantee** - At least N files included even if exceeding limit
4. **Truncation notices** - Proper categorization and reporting of excluded files
5. **Edge cases** - Empty diffs, all files fit, single large file, etc.

## Implementation Details

### Core Components

1. **FileDiff dataclass** - Represents a single file's changes with priority scoring
2. **parse_github_files()** - Converts GitHub API response to FileDiff objects
3. **truncate_diff_smart()** - Priority-based truncation algorithm
4. **get_diff_summary()** - Human-readable summary of changes

### Algorithm Flow

```
1. Parse GitHub files → FileDiff objects
2. Calculate priority score for each file
3. Sort files by priority (descending)
4. Include files until max_chars reached
5. Ensure min_files included (even if over limit)
6. Generate truncation notice if needed
7. Format final diff with metadata
```

### Priority Score Calculation

```python
def priority_score(file: FileDiff) -> int:
    if file.change_type == NEW:
        return 10000 - min(file.total_changes, 1000)
    elif file.change_type == MODIFIED:
        return 5000 - min(file.total_changes, 4999)
    elif file.change_type == RENAMED:
        return 2500 - min(file.total_changes, 1000)
    else:  # DELETED
        return 1000 - min(file.total_changes, 999)
```

This ensures:
- New files always score 9,000-10,000
- Modified files score 1-5,000
- Deleted files score 1-1,000
- Within categories, smaller = higher score

## Performance Considerations

- **Efficient sorting**: O(n log n) where n = number of files
- **Linear truncation**: Single pass through sorted files
- **String building**: Pre-allocated list with join (not concatenation)
- **GitHub API**: Cached responses, single request per PR

## Future Enhancements

Potential improvements for future iterations:

1. **File type awareness** - Further prioritize test files, config files, etc.
2. **Dependency analysis** - Include files that are imported by high-priority files
3. **Incremental reviews** - Review in chunks for very large PRs
4. **Smart context** - Include surrounding context for modified sections
5. **Configurable priorities** - Allow custom priority rules per project
6. **Caching** - Cache truncated diffs for repeated reviews

## Related Tickets

- **SDT1-46**: Initial implementation of improved diff truncation
- **SDT1-47**: Router refactoring (prerequisite)

## References

- [GitHub REST API - Pull Requests](https://docs.github.com/en/rest/pulls)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
