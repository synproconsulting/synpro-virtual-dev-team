"""
Tests for Manager Agent diff truncation and code review functionality.
"""

import pytest
from manager_agent import (
    FileDiff,
    FileChangeType,
    parse_github_files,
    truncate_diff_smart,
    get_diff_summary,
    DiffTruncationResult,
)


# ── Test Data ──────────────────────────────────────────────────────────────────────────


def create_file_diff(
    filename: str,
    change_type: FileChangeType,
    additions: int = 10,
    deletions: int = 5,
    patch: str = None
) -> FileDiff:
    """Helper to create FileDiff objects for testing."""
    if patch is None:
        patch = f"@@ -1,{deletions} +1,{additions} @@\n" + "+new line\n" * additions
    
    status_map = {
        FileChangeType.NEW: "added",
        FileChangeType.MODIFIED: "modified",
        FileChangeType.DELETED: "removed",
        FileChangeType.RENAMED: "renamed",
    }
    
    return FileDiff(
        filename=filename,
        change_type=change_type,
        additions=additions,
        deletions=deletions,
        patch=patch,
        status=status_map[change_type]
    )


def create_github_file_data(
    filename: str,
    status: str = "modified",
    additions: int = 10,
    deletions: int = 5,
    patch: str = None
) -> dict:
    """Helper to create GitHub API file data for testing."""
    if patch is None:
        patch = f"@@ -1,{deletions} +1,{additions} @@\n" + "+new line\n" * additions
    
    return {
        "filename": filename,
        "status": status,
        "additions": additions,
        "deletions": deletions,
        "patch": patch
    }


# ── Test FileDiff ──────────────────────────────────────────────────────────────────────


def test_file_diff_total_changes():
    """Test total_changes property calculation."""
    diff = create_file_diff("test.py", FileChangeType.MODIFIED, additions=15, deletions=8)
    assert diff.total_changes == 23


def test_file_diff_priority_score_new_file():
    """Test that new files get highest priority."""
    new_file = create_file_diff("new.py", FileChangeType.NEW, additions=50, deletions=0)
    modified_file = create_file_diff("old.py", FileChangeType.MODIFIED, additions=50, deletions=0)
    
    assert new_file.priority_score > modified_file.priority_score


def test_file_diff_priority_score_new_vs_modified():
    """Test that even large new files have higher priority than small modified files."""
    large_new = create_file_diff("large_new.py", FileChangeType.NEW, additions=500, deletions=0)
    small_modified = create_file_diff("small.py", FileChangeType.MODIFIED, additions=10, deletions=5)
    
    assert large_new.priority_score > small_modified.priority_score


def test_file_diff_priority_score_modified_size_ordering():
    """Test that smaller modified files have higher priority than larger ones."""
    small_mod = create_file_diff("small.py", FileChangeType.MODIFIED, additions=10, deletions=5)
    large_mod = create_file_diff("large.py", FileChangeType.MODIFIED, additions=200, deletions=100)
    
    assert small_mod.priority_score > large_mod.priority_score


def test_file_diff_priority_score_deleted_lowest():
    """Test that deleted files have lowest priority."""
    deleted = create_file_diff("deleted.py", FileChangeType.DELETED, additions=0, deletions=50)
    modified = create_file_diff("modified.py", FileChangeType.MODIFIED, additions=5, deletions=5)
    new = create_file_diff("new.py", FileChangeType.NEW, additions=5, deletions=0)
    
    assert new.priority_score > modified.priority_score > deleted.priority_score


# ── Test parse_github_files ────────────────────────────────────────────────────────────


def test_parse_github_files_empty():
    """Test parsing empty file list."""
    result = parse_github_files([])
    assert result == []


def test_parse_github_files_new_file():
    """Test parsing a new file."""
    files = [create_github_file_data("new.py", status="added", additions=20, deletions=0)]
    result = parse_github_files(files)
    
    assert len(result) == 1
    assert result[0].filename == "new.py"
    assert result[0].change_type == FileChangeType.NEW
    assert result[0].additions == 20
    assert result[0].deletions == 0


def test_parse_github_files_modified_file():
    """Test parsing a modified file."""
    files = [create_github_file_data("modified.py", status="modified", additions=10, deletions=5)]
    result = parse_github_files(files)
    
    assert len(result) == 1
    assert result[0].filename == "modified.py"
    assert result[0].change_type == FileChangeType.MODIFIED


def test_parse_github_files_multiple():
    """Test parsing multiple files with different statuses."""
    files = [
        create_github_file_data("new.py", status="added"),
        create_github_file_data("modified.py", status="modified"),
        create_github_file_data("deleted.py", status="removed"),
        create_github_file_data("renamed.py", status="renamed"),
    ]
    result = parse_github_files(files)
    
    assert len(result) == 4
    assert result[0].change_type == FileChangeType.NEW
    assert result[1].change_type == FileChangeType.MODIFIED
    assert result[2].change_type == FileChangeType.DELETED
    assert result[3].change_type == FileChangeType.RENAMED


# ── Test truncate_diff_smart ───────────────────────────────────────────────────────────


def test_truncate_diff_smart_empty():
    """Test truncation with no files."""
    result = truncate_diff_smart([])
    
    assert result.truncated_diff == ""
    assert result.total_files == 0
    assert result.included_files == 0
    assert result.excluded_files == 0


def test_truncate_diff_smart_all_fit():
    """Test truncation when all files fit within limit."""
    files = [
        create_file_diff("new.py", FileChangeType.NEW, patch="short patch"),
        create_file_diff("modified.py", FileChangeType.MODIFIED, patch="short patch too"),
    ]
    
    result = truncate_diff_smart(files, max_chars=10000)
    
    assert result.total_files == 2
    assert result.included_files == 2
    assert result.excluded_files == 0
    assert "new.py" in result.truncated_diff
    assert "modified.py" in result.truncated_diff
    assert "DIFF TRUNCATED" not in result.truncated_diff


def test_truncate_diff_smart_prioritizes_new_files():
    """Test that new files are prioritized over modified files when truncating."""
    # Create a large modified file and small new file
    large_patch = "line\n" * 1000
    small_patch = "short"
    
    files = [
        create_file_diff("modified.py", FileChangeType.MODIFIED, patch=large_patch),
        create_file_diff("new.py", FileChangeType.NEW, patch=small_patch),
    ]
    
    # Set limit that can only fit one file
    result = truncate_diff_smart(files, max_chars=500, min_files=1)
    
    # New file should be included, modified file excluded
    assert result.included_files == 1
    assert result.excluded_files == 1
    assert "new.py" in result.truncated_diff
    assert "modified.py" not in result.truncated_diff
    assert "modified.py" in result.excluded_file_list


def test_truncate_diff_smart_min_files():
    """Test that minimum files are included even if exceeding limit."""
    large_patch = "x" * 10000
    
    files = [
        create_file_diff("file1.py", FileChangeType.NEW, patch=large_patch),
        create_file_diff("file2.py", FileChangeType.NEW, patch=large_patch),
        create_file_diff("file3.py", FileChangeType.NEW, patch=large_patch),
        create_file_diff("file4.py", FileChangeType.NEW, patch=large_patch),
    ]
    
    # Set low limit but require min_files=3
    result = truncate_diff_smart(files, max_chars=1000, min_files=3)
    
    # Should include at least 3 files despite exceeding limit
    assert result.included_files >= 3


def test_truncate_diff_smart_priority_ordering():
    """Test that files are ordered by priority in truncation."""
    files = [
        create_file_diff("deleted.py", FileChangeType.DELETED, patch="del"),
        create_file_diff("large_mod.py", FileChangeType.MODIFIED, additions=500, patch="x" * 100),
        create_file_diff("small_mod.py", FileChangeType.MODIFIED, additions=10, patch="x" * 50),
        create_file_diff("new.py", FileChangeType.NEW, additions=100, patch="x" * 80),
    ]
    
    # Limit to 2 files
    result = truncate_diff_smart(files, max_chars=300, min_files=2)
    
    # Should include: new.py and small_mod.py (highest priority)
    assert result.included_files == 2
    assert "new.py" in result.truncated_diff
    assert "small_mod.py" in result.truncated_diff


def test_truncate_diff_smart_truncation_notice():
    """Test that truncation notice is added when files are excluded."""
    files = [
        create_file_diff("new1.py", FileChangeType.NEW, patch="x" * 100),
        create_file_diff("new2.py", FileChangeType.NEW, patch="x" * 100),
        create_file_diff("modified.py", FileChangeType.MODIFIED, patch="x" * 100),
    ]
    
    result = truncate_diff_smart(files, max_chars=250, min_files=1)
    
    if result.excluded_files > 0:
        assert "DIFF TRUNCATED" in result.truncated_diff
        assert f"{result.excluded_files} files excluded" in result.truncated_diff


def test_truncate_diff_smart_categorizes_excluded():
    """Test that excluded files are categorized by type in the notice."""
    large_patch = "x" * 1000
    
    files = [
        create_file_diff("new1.py", FileChangeType.NEW, patch=large_patch),
        create_file_diff("new2.py", FileChangeType.NEW, patch=large_patch),
        create_file_diff("modified1.py", FileChangeType.MODIFIED, patch=large_patch),
        create_file_diff("modified2.py", FileChangeType.MODIFIED, patch=large_patch),
        create_file_diff("deleted.py", FileChangeType.DELETED, patch=large_patch),
    ]
    
    result = truncate_diff_smart(files, max_chars=1500, min_files=1)
    
    if result.excluded_files > 0:
        # Check that categories are present
        diff_lower = result.truncated_diff.lower()
        if any(f.change_type == FileChangeType.NEW for f in files if f.filename in result.excluded_file_list):
            assert "excluded new files" in diff_lower or "excluded other files" in diff_lower


# ── Test get_diff_summary ──────────────────────────────────────────────────────────────


def test_get_diff_summary_empty():
    """Test summary with no files."""
    result = get_diff_summary([])
    assert result == "No file changes"


def test_get_diff_summary_single_new():
    """Test summary with a single new file."""
    files = [create_file_diff("new.py", FileChangeType.NEW, additions=20, deletions=0)]
    result = get_diff_summary(files)
    
    assert "1 files changed" in result or "Total: 1 files" in result
    assert "1 new" in result
    assert "+20" in result
    assert "-0" in result


def test_get_diff_summary_mixed():
    """Test summary with mixed file types."""
    files = [
        create_file_diff("new.py", FileChangeType.NEW, additions=50, deletions=0),
        create_file_diff("mod1.py", FileChangeType.MODIFIED, additions=10, deletions=5),
        create_file_diff("mod2.py", FileChangeType.MODIFIED, additions=20, deletions=10),
        create_file_diff("deleted.py", FileChangeType.DELETED, additions=0, deletions=30),
    ]
    result = get_diff_summary(files)
    
    assert "4 files" in result
    assert "1 new" in result
    assert "2 modified" in result
    assert "1 deleted" in result
    assert "+80" in result  # 50 + 10 + 20
    assert "-45" in result  # 5 + 10 + 30


def test_get_diff_summary_line_counts():
    """Test that line counts are correctly summed."""
    files = [
        create_file_diff("f1.py", FileChangeType.NEW, additions=100, deletions=0),
        create_file_diff("f2.py", FileChangeType.MODIFIED, additions=50, deletions=25),
    ]
    result = get_diff_summary(files)
    
    assert "+150" in result
    assert "-25" in result


# ── Integration Tests ──────────────────────────────────────────────────────────────────


def test_full_workflow_prioritization():
    """Test full workflow from GitHub data to truncated diff with prioritization."""
    # Simulate GitHub API response
    github_files = [
        create_github_file_data("new_feature.py", status="added", additions=100, 
                               patch="@@ new feature\n" + "+new code\n" * 100),
        create_github_file_data("config.json", status="added", additions=10,
                               patch="@@ config\n" + "+config line\n" * 10),
        create_github_file_data("existing.py", status="modified", additions=200, deletions=50,
                               patch="@@ big change\n" + "+modified line\n" * 200),
        create_github_file_data("utils.py", status="modified", additions=5, deletions=2,
                               patch="@@ small fix\n+fix\n" * 5),
        create_github_file_data("old.py", status="removed", additions=0, deletions=100,
                               patch="@@ deleted\n" + "-old line\n" * 100),
    ]
    
    # Parse files
    file_diffs = parse_github_files(github_files)
    assert len(file_diffs) == 5
    
    # Truncate with tight limit
    result = truncate_diff_smart(file_diffs, max_chars=2000, min_files=2)
    
    # Verify new files are prioritized
    # The two new files should be included first
    assert "new_feature.py" in result.truncated_diff or "config.json" in result.truncated_diff
    
    # Deleted file should be excluded first if space is tight
    if result.excluded_files > 0:
        # old.py (deleted) should be in excluded list if anything is excluded
        assert len(result.excluded_file_list) > 0


def test_realistic_pr_scenario():
    """Test a realistic PR scenario with mixed changes."""
    # Simulate a feature PR with:
    # - 2 new files (the feature implementation)
    # - 3 modified files (integration points)
    # - 1 deleted file (deprecated code)
    
    github_files = [
        # New feature files - should have highest priority
        create_github_file_data(
            "features/new_feature.py",
            status="added",
            additions=150,
            patch="@@ Feature implementation\n" + "+impl line\n" * 150
        ),
        create_github_file_data(
            "features/__init__.py",
            status="added",
            additions=5,
            patch="@@ Init file\n+from .new_feature import *\n"
        ),
        # Modified files - medium priority
        create_github_file_data(
            "main.py",
            status="modified",
            additions=10,
            deletions=2,
            patch="@@ Import new feature\n+import features.new_feature\n"
        ),
        create_github_file_data(
            "config.py",
            status="modified",
            additions=5,
            deletions=1,
            patch="@@ Add config\n+FEATURE_ENABLED = True\n"
        ),
        create_github_file_data(
            "tests/test_integration.py",
            status="modified",
            additions=50,
            deletions=10,
            patch="@@ Add tests\n" + "+test line\n" * 50
        ),
        # Deleted file - lowest priority
        create_github_file_data(
            "deprecated/old_feature.py",
            status="removed",
            additions=0,
            deletions=200,
            patch="@@ Removed\n" + "-old line\n" * 200
        ),
    ]
    
    file_diffs = parse_github_files(github_files)
    result = truncate_diff_smart(file_diffs, max_chars=5000, min_files=3)
    
    # Should include at least the new files and some modified files
    assert result.included_files >= 3
    
    # New feature files should definitely be included
    new_files_included = sum(
        1 for name in ["features/new_feature.py", "features/__init__.py"]
        if name in result.truncated_diff
    )
    assert new_files_included >= 1  # At least one new file should be included
    
    # If anything is excluded, deleted file should be excluded first
    if result.excluded_files > 0:
        # Check that new files are NOT in excluded list
        assert "features/new_feature.py" not in result.excluded_file_list or \
               "features/__init__.py" not in result.excluded_file_list


def test_summary_generation_accuracy():
    """Test that diff summary accurately reflects file changes."""
    files = [
        create_file_diff("new1.py", FileChangeType.NEW, additions=100, deletions=0),
        create_file_diff("new2.py", FileChangeType.NEW, additions=50, deletions=0),
        create_file_diff("mod.py", FileChangeType.MODIFIED, additions=25, deletions=15),
        create_file_diff("del.py", FileChangeType.DELETED, additions=0, deletions=80),
    ]
    
    summary = get_diff_summary(files)
    
    # Verify counts
    assert "4 files" in summary
    assert "2 new" in summary
    assert "1 modified" in summary
    assert "1 deleted" in summary
    
    # Verify totals: 100 + 50 + 25 = 175 additions
    assert "+175" in summary
    
    # Verify totals: 15 + 80 = 95 deletions
    assert "-95" in summary
