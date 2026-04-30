"""
Diff Handler - Smart truncation of Git diffs with prioritization.

This module provides intelligent diff truncation that prioritizes:
1. New files (highest priority)
2. Modified files with significant changes
3. Ensures all files are at least represented with a summary

The goal is to fit diffs within token limits while maximizing information
about new files and critical changes.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ChangeType(Enum):
    """Type of file change in a diff."""
    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileChange:
    """Represents a single file change in a diff."""
    path: str
    change_type: ChangeType
    additions: int
    deletions: int
    diff_content: str
    
    @property
    def total_changes(self) -> int:
        """Total number of line changes."""
        return self.additions + self.deletions
    
    @property
    def priority_score(self) -> int:
        """
        Calculate priority score for this file change.
        
        Priority rules:
        1. New files get highest priority (1000 base score)
        2. Modified files get medium priority (500 base score)
        3. Deleted files get low priority (100 base score)
        4. Additional points for total changes (capped at 500)
        
        Returns:
            Priority score (higher = more important)
        """
        if self.change_type == ChangeType.NEW:
            base = 1000
        elif self.change_type == ChangeType.MODIFIED:
            base = 500
        elif self.change_type == ChangeType.DELETED:
            base = 100
        elif self.change_type == ChangeType.RENAMED:
            base = 300
        else:
            base = 0
        
        # Add points for magnitude of changes (capped at 500)
        change_points = min(self.total_changes, 500)
        
        return base + change_points


class DiffParser:
    """
    Parses Git diffs and extracts file changes.
    """
    
    # Regex patterns for parsing git diff
    FILE_HEADER_PATTERN = re.compile(r'^diff --git a/(.*?) b/(.*?)$', re.MULTILINE)
    NEW_FILE_PATTERN = re.compile(r'^new file mode \d+$', re.MULTILINE)
    DELETED_FILE_PATTERN = re.compile(r'^deleted file mode \d+$', re.MULTILINE)
    RENAME_PATTERN = re.compile(r'^rename from (.*?)$.*?^rename to (.*?)$', re.MULTILINE | re.DOTALL)
    STATS_PATTERN = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)
    
    @staticmethod
    def parse_diff(diff_text: str) -> List[FileChange]:
        """
        Parse a Git diff into structured file changes.
        
        Args:
            diff_text: Raw git diff output
        
        Returns:
            List of FileChange objects
        """
        file_changes = []
        
        # Split diff into individual file chunks
        file_chunks = DiffParser._split_into_files(diff_text)
        
        for chunk in file_chunks:
            file_change = DiffParser._parse_file_chunk(chunk)
            if file_change:
                file_changes.append(file_change)
        
        return file_changes
    
    @staticmethod
    def _split_into_files(diff_text: str) -> List[str]:
        """Split diff text into chunks for individual files."""
        # Split on "diff --git" markers
        chunks = re.split(r'(?=^diff --git)', diff_text, flags=re.MULTILINE)
        # Filter out empty chunks
        return [chunk.strip() for chunk in chunks if chunk.strip()]
    
    @staticmethod
    def _parse_file_chunk(chunk: str) -> Optional[FileChange]:
        """Parse a single file's diff chunk."""
        # Extract file path
        file_match = DiffParser.FILE_HEADER_PATTERN.search(chunk)
        if not file_match:
            return None
        
        file_path = file_match.group(2)  # Use the 'b/' path (destination)
        
        # Determine change type
        if DiffParser.NEW_FILE_PATTERN.search(chunk):
            change_type = ChangeType.NEW
        elif DiffParser.DELETED_FILE_PATTERN.search(chunk):
            change_type = ChangeType.DELETED
        elif DiffParser.RENAME_PATTERN.search(chunk):
            change_type = ChangeType.RENAMED
        else:
            change_type = ChangeType.MODIFIED
        
        # Count additions and deletions
        additions = chunk.count('\n+') - chunk.count('\n+++')
        deletions = chunk.count('\n-') - chunk.count('\n---')
        
        return FileChange(
            path=file_path,
            change_type=change_type,
            additions=additions,
            deletions=deletions,
            diff_content=chunk,
        )


class DiffTruncator:
    """
    Intelligently truncates diffs to fit within token/character limits.
    
    Prioritizes new files and important changes while ensuring all files
    are at least mentioned with a summary.
    """
    
    def __init__(
        self,
        max_chars: int = 50000,
        min_chars_per_file: int = 200,
        summary_chars: int = 100,
    ):
        """
        Initialize the diff truncator.
        
        Args:
            max_chars: Maximum total characters for truncated diff
            min_chars_per_file: Minimum characters to show per file (if space allows)
            summary_chars: Characters for file summary when truncated
        """
        self.max_chars = max_chars
        self.min_chars_per_file = min_chars_per_file
        self.summary_chars = summary_chars
    
    def truncate_diff(self, diff_text: str) -> Tuple[str, Dict[str, any]]:
        """
        Truncate a diff with intelligent prioritization.
        
        Args:
            diff_text: Raw git diff output
        
        Returns:
            Tuple of (truncated_diff, metadata_dict)
            metadata includes stats about truncation
        """
        # Parse the diff
        file_changes = DiffParser.parse_diff(diff_text)
        
        if not file_changes:
            return diff_text, {"truncated": False, "total_files": 0}
        
        # Check if truncation is needed
        total_size = sum(len(fc.diff_content) for fc in file_changes)
        
        if total_size <= self.max_chars:
            return diff_text, {
                "truncated": False,
                "total_files": len(file_changes),
                "total_size": total_size,
            }
        
        # Sort files by priority (highest first)
        sorted_files = sorted(
            file_changes,
            key=lambda fc: fc.priority_score,
            reverse=True,
        )
        
        # Build truncated diff
        result_parts = []
        remaining_chars = self.max_chars
        files_included_full = []
        files_summarized = []
        
        # First pass: Include high-priority files fully
        for file_change in sorted_files:
            file_size = len(file_change.diff_content)
            
            # Reserve space for file summaries of remaining files
            files_left = len(sorted_files) - len(files_included_full) - len(files_summarized)
            reserved = files_left * self.summary_chars
            
            if file_size + reserved <= remaining_chars:
                # Include full diff
                result_parts.append(file_change.diff_content)
                files_included_full.append(file_change)
                remaining_chars -= file_size
            else:
                # Create summary for this file
                summary = self._create_file_summary(file_change)
                result_parts.append(summary)
                files_summarized.append(file_change)
                remaining_chars -= len(summary)
        
        truncated_diff = "\n\n".join(result_parts)
        
        # Add truncation notice at the end
        truncation_notice = self._create_truncation_notice(
            total_files=len(file_changes),
            files_included=len(files_included_full),
            files_summarized=len(files_summarized),
            sorted_files=sorted_files,
        )
        truncated_diff += "\n\n" + truncation_notice
        
        metadata = {
            "truncated": True,
            "total_files": len(file_changes),
            "files_included_full": len(files_included_full),
            "files_summarized": len(files_summarized),
            "original_size": total_size,
            "truncated_size": len(truncated_diff),
            "new_files_count": sum(1 for fc in file_changes if fc.change_type == ChangeType.NEW),
            "new_files_included": sum(1 for fc in files_included_full if fc.change_type == ChangeType.NEW),
        }
        
        return truncated_diff, metadata
    
    def _create_file_summary(self, file_change: FileChange) -> str:
        """
        Create a concise summary for a file change.
        
        Args:
            file_change: FileChange object
        
        Returns:
            Summary string
        """
        change_icon = {
            ChangeType.NEW: "🆕",
            ChangeType.MODIFIED: "✏️",
            ChangeType.DELETED: "🗑️",
            ChangeType.RENAMED: "📝",
        }.get(file_change.change_type, "📄")
        
        return (
            f"{'=' * 80}\n"
            f"{change_icon} {file_change.path}\n"
            f"{'=' * 80}\n"
            f"Change type: {file_change.change_type.value.upper()}\n"
            f"Lines changed: +{file_change.additions} -{file_change.deletions}\n"
            f"[Full diff truncated to save space]\n"
        )
    
    def _create_truncation_notice(
        self,
        total_files: int,
        files_included: int,
        files_summarized: int,
        sorted_files: List[FileChange],
    ) -> str:
        """Create a notice explaining the truncation."""
        notice_lines = [
            "=" * 80,
            "📊 DIFF TRUNCATION SUMMARY",
            "=" * 80,
            f"Total files changed: {total_files}",
            f"Files shown in full: {files_included}",
            f"Files summarized: {files_summarized}",
            "",
            "Priority order (new files prioritized):",
        ]
        
        for i, fc in enumerate(sorted_files[:10], 1):  # Show top 10
            change_icon = {
                ChangeType.NEW: "🆕",
                ChangeType.MODIFIED: "✏️",
                ChangeType.DELETED: "🗑️",
                ChangeType.RENAMED: "📝",
            }.get(fc.change_type, "📄")
            
            included = "✓" if fc in sorted_files[:files_included] else "📝"
            notice_lines.append(
                f"  {i}. {included} {change_icon} {fc.path} "
                f"(+{fc.additions}/-{fc.deletions}, priority: {fc.priority_score})"
            )
        
        if total_files > 10:
            notice_lines.append(f"  ... and {total_files - 10} more files")
        
        notice_lines.append("=" * 80)
        
        return "\n".join(notice_lines)


def truncate_diff_smart(
    diff_text: str,
    max_chars: int = 50000,
) -> Tuple[str, Dict[str, any]]:
    """
    Convenience function to truncate a diff with smart prioritization.
    
    Args:
        diff_text: Raw git diff output
        max_chars: Maximum characters for result
    
    Returns:
        Tuple of (truncated_diff, metadata)
    """
    truncator = DiffTruncator(max_chars=max_chars)
    return truncator.truncate_diff(diff_text)


def get_new_files_summary(diff_text: str) -> List[Dict[str, any]]:
    """
    Extract summary of all new files from a diff.
    
    Args:
        diff_text: Raw git diff output
    
    Returns:
        List of dictionaries with new file information
    """
    file_changes = DiffParser.parse_diff(diff_text)
    new_files = [fc for fc in file_changes if fc.change_type == ChangeType.NEW]
    
    return [
        {
            "path": fc.path,
            "additions": fc.additions,
            "deletions": fc.deletions,
            "priority_score": fc.priority_score,
        }
        for fc in new_files
    ]
