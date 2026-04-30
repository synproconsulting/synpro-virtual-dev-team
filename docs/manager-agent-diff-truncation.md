# Manager Agent Diff Truncation

## Overview

The Manager Agent now includes intelligent diff truncation functionality that prioritizes **new files** when reviewing pull requests. This ensures that even when diffs are very large and need to be truncated to fit within token limits, the most important information (new files) is always included.

## Key Features

### 1. Smart Prioritization

Files are prioritized based on a scoring system:

- **New files**: Highest priority (1000 base score)
- **Modified files**: Medium priority (500 base score)
- **Renamed files**: Low-medium priority (300 base score)
- **Deleted files**: Low priority (100 base score)

Additional points are awarded based on the magnitude of changes (up to 500 points), ensuring that files with significant changes are also prioritized.

### 2. Intelligent Truncation

When a diff exceeds the character limit (default 50,000 chars):

1. Files are sorted by priority score (highest first)
2. High-priority files are included in full
3. Lower-priority files are summarized with key metadata
4. A truncation notice is added explaining what was included/summarized

### 3. Complete Coverage

Even when heavily truncated, **every file** is at least mentioned with:
- File path
- Change type (new, modified, deleted)
- Line change statistics (+X/-Y)

## Usage

### Basic Diff Review

```python
from agents.manager_agent import create_manager_agent

agent = create_manager_agent()

# Review a diff
result = agent.review_diff(diff_text, generate_comments=True)

print(f"Truncated: {result.was_truncated}")
print(f"New files: {len(result.new_files_summary)}")
print(f"Comments: {result.review_comments}")
```

### Review and Post to Jira

```python
# Review a PR and post comments to Jira, transitioning to Code Review
review_result, transition_result = await agent.review_and_comment_pr(
    issue_key="SDT1-46",
    diff_text=pr_diff,
)

if transition_result.status == TransitionStatus.SUCCESS:
    print(f"PR reviewed and transitioned to {transition_result.final_status}")
```

### Configuration

```python
# Custom configuration
agent = create_manager_agent(
    max_retries=5,
    base_delay=1.0,
    diff_max_chars=75000,  # Custom diff size limit
)
```

## Architecture

### Components

1. **`DiffParser`** (`tools/diff_handler.py`)
   - Parses Git diffs into structured `FileChange` objects
   - Identifies change types (new, modified, deleted, renamed)
   - Counts line additions and deletions

2. **`DiffTruncator`** (`tools/diff_handler.py`)
   - Implements intelligent truncation algorithm
   - Prioritizes files based on change type and magnitude
   - Generates file summaries and truncation notices

3. **`ManagerAgent.review_diff()`** (`agents/manager_agent.py`)
   - High-level interface for diff review
   - Optionally generates human-readable review comments
   - Formats results for Jira integration

### Data Flow

```
Git Diff Text
      ↓
DiffParser.parse_diff()
      ↓
List[FileChange] (with priority scores)
      ↓
DiffTruncator.truncate_diff()
      ↓
(Truncated Diff, Metadata)
      ↓
ManagerAgent.review_diff()
      ↓
DiffReviewResult (with comments)
```

## Examples

### Example 1: Small PR (No Truncation)

```python
diff_text = """
diff --git a/feature.py b/feature.py
new file mode 100644
+++ b/feature.py
@@ -0,0 +1,5 @@
+def new_feature():
+    return "Hello"
"""

result = agent.review_diff(diff_text)
# result.was_truncated == False
# result.has_new_files == True
# result.truncated_diff contains full diff
```

### Example 2: Large PR with New Files (Truncation)

```python
# 100 files: 3 new, 97 modified
# Only fits ~10 files in token limit

result = agent.review_diff(large_pr_diff)
# result.was_truncated == True
# result.metadata['files_included_full'] == 10
# result.metadata['files_summarized'] == 90

# All 3 new files are included in full (prioritized)
# 7 largest modified files included in full
# Remaining 90 files summarized
```

### Example 3: Review Comments

When `generate_comments=True`, the agent produces helpful comments:

```
✨ This PR introduces 3 new file(s). 
Please ensure all new files have appropriate tests and documentation.

New files:
  - tools/diff_handler.py (+300 lines)
  - tools/tests/test_diff_handler.py (+250 lines)
  - agents/manager_agent.py (+150 lines)

⚠️ Note: This PR is large. Showing 10 file(s) in full and 90 file(s) as summaries.
New files are prioritized in the review.

📊 This is a large PR with 100 files changed. 
Consider breaking it into smaller PRs for easier review.
```

## Testing

Comprehensive tests are included:

### Unit Tests

- **`tools/tests/test_diff_handler.py`**: Tests for DiffParser and DiffTruncator
  - Parsing various diff formats
  - Priority score calculation
  - Truncation algorithm
  - Edge cases (empty diffs, invalid formats)

- **`agents/tests/test_manager_agent.py`**: Tests for ManagerAgent diff review
  - Diff review with/without truncation
  - Comment generation
  - Jira integration
  - Review workflow

### Run Tests

```bash
# Run all diff handler tests
pytest tools/tests/test_diff_handler.py -v

# Run manager agent diff tests
pytest agents/tests/test_manager_agent.py::TestDiffReview -v

# Run specific test
pytest tools/tests/test_diff_handler.py::test_new_files_prioritized_in_truncation -v
```

## Performance

### Metrics

- **Parsing**: O(n) where n = number of lines in diff
- **Sorting**: O(m log m) where m = number of files
- **Truncation**: O(m) single pass through sorted files

### Typical Performance

- Small PR (5 files, 500 lines): ~10ms
- Medium PR (20 files, 2000 lines): ~50ms
- Large PR (100 files, 10000 lines): ~200ms

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `diff_max_chars` | 50,000 | Maximum characters for truncated diff |
| `min_chars_per_file` | 200 | Minimum characters to show per file |
| `summary_chars` | 100 | Characters for file summary when truncated |

## Limitations

1. **Format Support**: Currently supports standard Git unified diff format only
2. **Binary Files**: Binary file changes are detected but content not analyzed
3. **Rename Detection**: Basic rename detection; complex renames may be treated as delete+add
4. **Memory**: Large diffs (>100MB) may cause memory issues; consider pre-filtering

## Future Enhancements

Potential improvements for future iterations:

1. **Semantic Analysis**: Prioritize files based on code semantics (e.g., API changes)
2. **Language-Aware**: Different priorities for different file types
3. **Dependency Analysis**: Prioritize files that affect many other files
4. **Test Coverage**: Highlight files without corresponding tests
5. **Security Focus**: Prioritize security-sensitive files (auth, validation, etc.)

## References

- [Git Diff Format](https://git-scm.com/docs/git-diff)
- [SDT1-46 Jira Ticket](https://your-jira-instance.atlassian.net/browse/SDT1-46)
- [Manager Agent Documentation](./manager-agent.md)
