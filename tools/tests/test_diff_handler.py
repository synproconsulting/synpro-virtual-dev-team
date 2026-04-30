"""
Tests for diff_handler module - intelligent diff truncation.
"""

import pytest
from tools.diff_handler import (
    DiffParser,
    DiffTruncator,
    FileChange,
    ChangeType,
    truncate_diff_smart,
    get_new_files_summary,
)


# ── Sample Diffs ──────────────────────────────────────────────────────────────────────


SAMPLE_NEW_FILE_DIFF = """diff --git a/tools/new_feature.py b/tools/new_feature.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/tools/new_feature.py
@@ -0,0 +1,10 @@
+def new_function():
+    \"\"\"A brand new function.\"\"\"
+    return "Hello, World!"
+
+
+class NewClass:
+    \"\"\"A new class.\"\"\"
+    def __init__(self):
+        self.value = 42
"""

SAMPLE_MODIFIED_FILE_DIFF = """diff --git a/tools/existing.py b/tools/existing.py
index abcdef1..1234567 100644
--- a/tools/existing.py
+++ b/tools/existing.py
@@ -1,5 +1,8 @@
 def existing_function():
-    return "old value"
+    return "new value"
 
 
+def added_function():
+    return "I'm new here"
+
"""

SAMPLE_DELETED_FILE_DIFF = """diff --git a/tools/old_feature.py b/tools/old_feature.py
deleted file mode 100644
index 7654321..0000000
--- a/tools/old_feature.py
+++ /dev/null
@@ -1,5 +0,0 @@
-def old_function():
-    return "deprecated"
-
-# This file is no longer needed
"""

SAMPLE_MULTI_FILE_DIFF = (
    SAMPLE_NEW_FILE_DIFF + "\n\n" +
    SAMPLE_MODIFIED_FILE_DIFF + "\n\n" +
    SAMPLE_DELETED_FILE_DIFF
)


# ── Tests for DiffParser ──────────────────────────────────────────────────────────────


def test_parse_new_file():
    """Test parsing a new file diff."""
    changes = DiffParser.parse_diff(SAMPLE_NEW_FILE_DIFF)
    
    assert len(changes) == 1
    
    file_change = changes[0]
    assert file_change.path == "tools/new_feature.py"
    assert file_change.change_type == ChangeType.NEW
    assert file_change.additions > 0
    assert file_change.deletions == 0


def test_parse_modified_file():
    """Test parsing a modified file diff."""
    changes = DiffParser.parse_diff(SAMPLE_MODIFIED_FILE_DIFF)
    
    assert len(changes) == 1
    
    file_change = changes[0]
    assert file_change.path == "tools/existing.py"
    assert file_change.change_type == ChangeType.MODIFIED
    assert file_change.additions > 0
    assert file_change.deletions > 0


def test_parse_deleted_file():
    """Test parsing a deleted file diff."""
    changes = DiffParser.parse_diff(SAMPLE_DELETED_FILE_DIFF)
    
    assert len(changes) == 1
    
    file_change = changes[0]
    assert file_change.path == "tools/old_feature.py"
    assert file_change.change_type == ChangeType.DELETED
    assert file_change.deletions > 0


def test_parse_multi_file_diff():
    """Test parsing a diff with multiple files."""
    changes = DiffParser.parse_diff(SAMPLE_MULTI_FILE_DIFF)
    
    assert len(changes) == 3
    
    # Should have one of each type
    change_types = {fc.change_type for fc in changes}
    assert ChangeType.NEW in change_types
    assert ChangeType.MODIFIED in change_types
    assert ChangeType.DELETED in change_types


def test_parse_empty_diff():
    """Test parsing an empty diff."""
    changes = DiffParser.parse_diff("")
    assert len(changes) == 0


# ── Tests for FileChange Priority ─────────────────────────────────────────────────────


def test_new_file_priority():
    """Test that new files get highest priority."""
    new_file = FileChange(
        path="test.py",
        change_type=ChangeType.NEW,
        additions=10,
        deletions=0,
        diff_content="",
    )
    
    modified_file = FileChange(
        path="test2.py",
        change_type=ChangeType.MODIFIED,
        additions=10,
        deletions=10,
        diff_content="",
    )
    
    # New files should have higher priority
    assert new_file.priority_score > modified_file.priority_score


def test_large_change_affects_priority():
    """Test that larger changes increase priority within same type."""
    small_change = FileChange(
        path="test.py",
        change_type=ChangeType.MODIFIED,
        additions=5,
        deletions=5,
        diff_content="",
    )
    
    large_change = FileChange(
        path="test2.py",
        change_type=ChangeType.MODIFIED,
        additions=100,
        deletions=100,
        diff_content="",
    )
    
    # Larger changes should have higher priority
    assert large_change.priority_score > small_change.priority_score


def test_priority_ordering():
    """Test complete priority ordering."""
    new_file = FileChange("new.py", ChangeType.NEW, 10, 0, "")
    modified_file = FileChange("mod.py", ChangeType.MODIFIED, 10, 10, "")
    renamed_file = FileChange("ren.py", ChangeType.RENAMED, 0, 0, "")
    deleted_file = FileChange("del.py", ChangeType.DELETED, 0, 10, "")
    
    files = [deleted_file, renamed_file, modified_file, new_file]
    sorted_files = sorted(files, key=lambda f: f.priority_score, reverse=True)
    
    # New should be first, deleted should be last
    assert sorted_files[0].change_type == ChangeType.NEW
    assert sorted_files[-1].change_type == ChangeType.DELETED


# ── Tests for DiffTruncator ───────────────────────────────────────────────────────────


def test_no_truncation_when_small():
    """Test that small diffs are not truncated."""
    truncator = DiffTruncator(max_chars=10000)
    
    result, metadata = truncator.truncate_diff(SAMPLE_NEW_FILE_DIFF)
    
    assert not metadata["truncated"]
    assert SAMPLE_NEW_FILE_DIFF in result


def test_truncation_when_large():
    """Test that large diffs are truncated."""
    # Create a very large diff by repeating
    large_diff = SAMPLE_MULTI_FILE_DIFF * 50
    
    truncator = DiffTruncator(max_chars=5000)
    result, metadata = truncator.truncate_diff(large_diff)
    
    assert metadata["truncated"]
    assert len(result) <= 6000  # Some buffer for summaries
    assert metadata["original_size"] > metadata["truncated_size"]


def test_new_files_prioritized_in_truncation():
    """Test that new files are included before modified files when truncating."""
    # Create a diff with both new and modified files
    # Make the modified file content very large
    large_modified = SAMPLE_MODIFIED_FILE_DIFF + ("\n+" + "x" * 100) * 50
    mixed_diff = SAMPLE_NEW_FILE_DIFF + "\n\n" + large_modified
    
    # Set max_chars so we can't fit everything
    truncator = DiffTruncator(max_chars=1000)
    result, metadata = truncator.truncate_diff(mixed_diff)
    
    assert metadata["truncated"]
    
    # New file should be in the result
    assert "tools/new_feature.py" in result
    assert "new file mode" in result
    
    # Verify metadata shows new files were included
    assert metadata["new_files_count"] >= 1


def test_all_files_at_least_summarized():
    """Test that all files are at least mentioned even when heavily truncated."""
    truncator = DiffTruncator(max_chars=2000)
    result, metadata = truncator.truncate_diff(SAMPLE_MULTI_FILE_DIFF)
    
    # All files should be mentioned
    assert "tools/new_feature.py" in result
    assert "tools/existing.py" in result
    assert "tools/old_feature.py" in result


def test_truncation_metadata():
    """Test that truncation metadata is complete."""
    truncator = DiffTruncator(max_chars=500)
    result, metadata = truncator.truncate_diff(SAMPLE_MULTI_FILE_DIFF)
    
    assert "truncated" in metadata
    assert "total_files" in metadata
    assert "files_included_full" in metadata
    assert "files_summarized" in metadata
    assert "original_size" in metadata
    assert "truncated_size" in metadata
    assert "new_files_count" in metadata
    assert "new_files_included" in metadata
    
    assert metadata["total_files"] == 3
    assert metadata["new_files_count"] == 1


def test_truncation_notice_included():
    """Test that truncation notice is added to result."""
    truncator = DiffTruncator(max_chars=500)
    result, metadata = truncator.truncate_diff(SAMPLE_MULTI_FILE_DIFF)
    
    if metadata["truncated"]:
        assert "DIFF TRUNCATION SUMMARY" in result
        assert "Priority order" in result


# ── Tests for Convenience Functions ───────────────────────────────────────────────────


def test_truncate_diff_smart():
    """Test the convenience function."""
    result, metadata = truncate_diff_smart(SAMPLE_MULTI_FILE_DIFF, max_chars=500)
    
    assert isinstance(result, str)
    assert isinstance(metadata, dict)
    assert "truncated" in metadata


def test_get_new_files_summary():
    """Test extracting new files summary."""
    summary = get_new_files_summary(SAMPLE_MULTI_FILE_DIFF)
    
    assert len(summary) == 1
    assert summary[0]["path"] == "tools/new_feature.py"
    assert "additions" in summary[0]
    assert "priority_score" in summary[0]


def test_get_new_files_summary_no_new_files():
    """Test summary when there are no new files."""
    summary = get_new_files_summary(SAMPLE_MODIFIED_FILE_DIFF)
    assert len(summary) == 0


# ── Integration Tests ─────────────────────────────────────────────────────────────────


def test_realistic_pr_scenario():
    """Test a realistic PR scenario with multiple file types."""
    # Simulate a PR with:
    # - 2 new files (high priority)
    # - 3 modified files (medium priority)
    # - 1 deleted file (low priority)
    
    new_files = [
        """diff --git a/feature/new1.py b/feature/new1.py
new file mode 100644
--- /dev/null
+++ b/feature/new1.py
@@ -0,0 +1,50 @@
""" + "\n+".join([f"+line {i}" for i in range(50)]),
        """diff --git a/feature/new2.py b/feature/new2.py
new file mode 100644
--- /dev/null
+++ b/feature/new2.py
@@ -0,0 +1,30 @@
""" + "\n+".join([f"+line {i}" for i in range(30)]),
    ]
    
    modified_files = [
        """diff --git a/existing/mod1.py b/existing/mod1.py
index abc..def 100644
--- a/existing/mod1.py
+++ b/existing/mod1.py
@@ -1,20 +1,25 @@
""" + "\n+".join([f"+changed {i}" for i in range(20)]),
        """diff --git a/existing/mod2.py b/existing/mod2.py
index ghi..jkl 100644
--- a/existing/mod2.py
+++ b/existing/mod2.py
@@ -1,10 +1,15 @@
""" + "\n+".join([f"+changed {i}" for i in range(10)]),
    ]
    
    pr_diff = "\n\n".join(new_files + modified_files)
    
    truncator = DiffTruncator(max_chars=2000)
    result, metadata = truncator.truncate_diff(pr_diff)
    
    # Both new files should be prioritized
    assert metadata["new_files_count"] == 2
    
    # Check that new files appear in result
    assert "feature/new1.py" in result
    assert "feature/new2.py" in result


def test_extreme_truncation():
    """Test behavior with extreme truncation limits."""
    # Very small max_chars
    truncator = DiffTruncator(max_chars=500)
    result, metadata = truncator.truncate_diff(SAMPLE_MULTI_FILE_DIFF)
    
    # Should still produce valid output
    assert len(result) > 0
    assert metadata["total_files"] == 3
    
    # Should include truncation notice
    assert "TRUNCATION" in result.upper()


def test_priority_score_calculation():
    """Test the priority score calculation logic."""
    # New file with 50 changes
    new_large = FileChange("new.py", ChangeType.NEW, 50, 0, "")
    assert new_large.priority_score == 1050  # 1000 + 50
    
    # Modified file with 50 changes
    mod_large = FileChange("mod.py", ChangeType.MODIFIED, 25, 25, "")
    assert mod_large.priority_score == 550  # 500 + 50
    
    # Deleted file
    deleted = FileChange("del.py", ChangeType.DELETED, 0, 20, "")
    assert deleted.priority_score == 120  # 100 + 20
    
    # Very large file (changes capped at 500)
    huge = FileChange("huge.py", ChangeType.MODIFIED, 1000, 1000, "")
    assert huge.priority_score == 1000  # 500 + 500 (capped)


def test_empty_and_edge_cases():
    """Test edge cases and empty inputs."""
    truncator = DiffTruncator()
    
    # Empty diff
    result, metadata = truncator.truncate_diff("")
    assert metadata["total_files"] == 0
    assert not metadata["truncated"]
    
    # Whitespace only
    result, metadata = truncator.truncate_diff("   \n\n   ")
    assert metadata["total_files"] == 0
    
    # Invalid diff format
    result, metadata = truncator.truncate_diff("not a valid diff")
    assert metadata["total_files"] == 0
