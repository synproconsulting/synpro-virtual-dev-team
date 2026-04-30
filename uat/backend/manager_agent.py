"""
Manager Agent - Code Review and PR Management

This agent reviews pull requests, provides feedback, and manages the development workflow.
Key features:
- Smart diff truncation that prioritizes new files over modified files
- Code quality analysis
- Automated PR reviews
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import anthropic
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# ── Configuration ──────────────────────────────────────────────────────────────────────

MANAGER_AGENT_SYSTEM = """You are a Manager Agent for a software development team.
Your role is to review code changes, ensure quality standards, and provide constructive feedback.

When reviewing pull requests:
1. Check for code quality, clarity, and maintainability
2. Identify potential bugs or issues
3. Suggest improvements and best practices
4. Verify that changes align with the ticket requirements
5. Ensure tests are included for new functionality

Provide feedback in a constructive, helpful tone. Focus on:
- Logic errors or potential bugs
- Code smells and anti-patterns
- Missing error handling
- Performance concerns
- Test coverage
- Documentation

Format your review as:
## Summary
Brief overview of the changes

## Concerns
- List any issues or concerns

## Suggestions
- List improvement suggestions

## Approval
APPROVE / REQUEST_CHANGES / COMMENT"""


def _get_anthropic_client() -> anthropic.Anthropic:
    """Get configured Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")
    return anthropic.Anthropic(api_key=api_key)


def _get_github_headers() -> dict:
    """Get GitHub API headers with authentication."""
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN not configured")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


# ── Diff Analysis Models ──────────────────────────────────────────────────────────────

class FileChangeType(Enum):
    """Type of file change in a PR."""
    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileDiff:
    """Represents a single file's diff in a PR."""
    filename: str
    change_type: FileChangeType
    additions: int
    deletions: int
    patch: str
    status: str  # GitHub API status: "added", "modified", "removed", "renamed"
    
    @property
    def total_changes(self) -> int:
        """Total number of lines changed."""
        return self.additions + self.deletions
    
    @property
    def priority_score(self) -> int:
        """
        Calculate priority score for diff truncation.
        Higher score = higher priority to include in truncated diff.
        
        Priority order:
        1. New files (highest priority)
        2. Modified files with fewer changes (more likely to be reviewed fully)
        3. Modified files with many changes
        4. Deleted files (lowest priority)
        """
        if self.change_type == FileChangeType.NEW:
            # New files get highest priority
            # Smaller new files get slightly higher priority
            return 10000 - min(self.total_changes, 1000)
        elif self.change_type == FileChangeType.MODIFIED:
            # Modified files: prioritize smaller changes
            return 5000 - min(self.total_changes, 4999)
        elif self.change_type == FileChangeType.RENAMED:
            # Renamed files medium priority
            return 2500 - min(self.total_changes, 1000)
        else:  # DELETED
            # Deleted files lowest priority
            return 1000 - min(self.total_changes, 999)


@dataclass
class DiffTruncationResult:
    """Result of diff truncation operation."""
    truncated_diff: str
    total_files: int
    included_files: int
    excluded_files: int
    total_size: int
    truncated_size: int
    excluded_file_list: List[str]


# ── Diff Truncation Logic ──────────────────────────────────────────────────────────────

def parse_github_files(files: List[Dict]) -> List[FileDiff]:
    """
    Parse GitHub API file changes into FileDiff objects.
    
    Args:
        files: List of file change objects from GitHub API
        
    Returns:
        List of FileDiff objects
    """
    result = []
    for file_data in files:
        status = file_data.get("status", "modified")
        
        # Map GitHub status to FileChangeType
        if status == "added":
            change_type = FileChangeType.NEW
        elif status == "removed":
            change_type = FileChangeType.DELETED
        elif status == "renamed":
            change_type = FileChangeType.RENAMED
        else:
            change_type = FileChangeType.MODIFIED
        
        result.append(FileDiff(
            filename=file_data.get("filename", ""),
            change_type=change_type,
            additions=file_data.get("additions", 0),
            deletions=file_data.get("deletions", 0),
            patch=file_data.get("patch", ""),
            status=status
        ))
    
    return result


def truncate_diff_smart(
    file_diffs: List[FileDiff],
    max_chars: int = 50000,
    min_files: int = 3
) -> DiffTruncationResult:
    """
    Intelligently truncate diff to fit within token limits while prioritizing new files.
    
    Strategy:
    1. Sort files by priority score (new files first)
    2. Include as many high-priority files as possible
    3. Always include at least min_files if possible
    4. Track what was excluded for reporting
    
    Args:
        file_diffs: List of FileDiff objects
        max_chars: Maximum character count for truncated diff
        min_files: Minimum number of files to include (even if exceeding max_chars slightly)
        
    Returns:
        DiffTruncationResult with truncated diff and metadata
    """
    if not file_diffs:
        return DiffTruncationResult(
            truncated_diff="",
            total_files=0,
            included_files=0,
            excluded_files=0,
            total_size=0,
            truncated_size=0,
            excluded_file_list=[]
        )
    
    # Sort by priority score (highest first)
    sorted_files = sorted(file_diffs, key=lambda f: f.priority_score, reverse=True)
    
    # Calculate total size
    total_size = sum(len(f.patch) for f in file_diffs)
    
    # Build truncated diff
    included_files = []
    excluded_files = []
    current_size = 0
    
    for idx, file_diff in enumerate(sorted_files):
        file_size = len(file_diff.patch) + len(file_diff.filename) + 100  # overhead
        
        # Always include minimum files, even if slightly over limit
        if idx < min_files or (current_size + file_size <= max_chars):
            included_files.append(file_diff)
            current_size += file_size
        else:
            excluded_files.append(file_diff)
    
    # Format the truncated diff
    diff_parts = []
    
    for file_diff in included_files:
        change_marker = {
            FileChangeType.NEW: "NEW FILE",
            FileChangeType.MODIFIED: "MODIFIED",
            FileChangeType.DELETED: "DELETED",
            FileChangeType.RENAMED: "RENAMED"
        }[file_diff.change_type]
        
        diff_parts.append(
            f"{'='*80}\n"
            f"File: {file_diff.filename} [{change_marker}]\n"
            f"Changes: +{file_diff.additions} -{file_diff.deletions}\n"
            f"{'='*80}\n"
            f"{file_diff.patch}\n"
        )
    
    # Add truncation notice if files were excluded
    if excluded_files:
        new_excluded = [f for f in excluded_files if f.change_type == FileChangeType.NEW]
        modified_excluded = [f for f in excluded_files if f.change_type == FileChangeType.MODIFIED]
        other_excluded = [f for f in excluded_files 
                         if f.change_type not in (FileChangeType.NEW, FileChangeType.MODIFIED)]
        
        diff_parts.append(f"\n{'='*80}\n")
        diff_parts.append(f"DIFF TRUNCATED: {len(excluded_files)} files excluded to fit token limit\n")
        
        if new_excluded:
            diff_parts.append(f"\nExcluded NEW files ({len(new_excluded)}):\n")
            for f in new_excluded:
                diff_parts.append(f"  - {f.filename} (+{f.additions} -{f.deletions})\n")
        
        if modified_excluded:
            diff_parts.append(f"\nExcluded MODIFIED files ({len(modified_excluded)}):\n")
            for f in modified_excluded:
                diff_parts.append(f"  - {f.filename} (+{f.additions} -{f.deletions})\n")
        
        if other_excluded:
            diff_parts.append(f"\nExcluded other files ({len(other_excluded)}):\n")
            for f in other_excluded:
                diff_parts.append(f"  - {f.filename} [{f.change_type.value}]\n")
        
        diff_parts.append(f"{'='*80}\n")
    
    truncated_diff = "".join(diff_parts)
    
    return DiffTruncationResult(
        truncated_diff=truncated_diff,
        total_files=len(file_diffs),
        included_files=len(included_files),
        excluded_files=len(excluded_files),
        total_size=total_size,
        truncated_size=len(truncated_diff),
        excluded_file_list=[f.filename for f in excluded_files]
    )


def get_diff_summary(file_diffs: List[FileDiff]) -> str:
    """
    Generate a summary of the diff for context.
    
    Args:
        file_diffs: List of FileDiff objects
        
    Returns:
        Human-readable summary string
    """
    if not file_diffs:
        return "No file changes"
    
    new_files = [f for f in file_diffs if f.change_type == FileChangeType.NEW]
    modified_files = [f for f in file_diffs if f.change_type == FileChangeType.MODIFIED]
    deleted_files = [f for f in file_diffs if f.change_type == FileChangeType.DELETED]
    renamed_files = [f for f in file_diffs if f.change_type == FileChangeType.RENAMED]
    
    total_additions = sum(f.additions for f in file_diffs)
    total_deletions = sum(f.deletions for f in file_diffs)
    
    parts = [f"Total: {len(file_diffs)} files changed"]
    
    if new_files:
        parts.append(f"{len(new_files)} new")
    if modified_files:
        parts.append(f"{len(modified_files)} modified")
    if deleted_files:
        parts.append(f"{len(deleted_files)} deleted")
    if renamed_files:
        parts.append(f"{len(renamed_files)} renamed")
    
    parts.append(f"(+{total_additions} -{total_deletions} lines)")
    
    return ", ".join(parts)


# ── API Models ──────────────────────────────────────────────────────────────────────────

class ReviewPRRequest(BaseModel):
    """Request to review a pull request."""
    owner: str
    repo: str
    pr_number: int
    ticket_key: Optional[str] = None
    max_diff_chars: int = 50000


class ReviewPRResponse(BaseModel):
    """Response from PR review."""
    review: str
    diff_summary: str
    truncation_info: Optional[Dict] = None
    success: bool = True


class TruncateDiffRequest(BaseModel):
    """Request to truncate a diff."""
    files: List[Dict]
    max_chars: int = 50000
    min_files: int = 3


class TruncateDiffResponse(BaseModel):
    """Response from diff truncation."""
    truncated_diff: str
    summary: Dict
    success: bool = True


# ── Router ──────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/manager-agent", tags=["manager-agent"])


@router.post("/review-pr", response_model=ReviewPRResponse)
async def review_pull_request(request: ReviewPRRequest):
    """
    Review a GitHub pull request using the Manager Agent.
    
    Fetches PR details and diff, truncates intelligently to prioritize new files,
    and generates AI-powered code review feedback.
    """
    try:
        # Fetch PR details from GitHub
        async with httpx.AsyncClient() as client:
            pr_url = f"https://api.github.com/repos/{request.owner}/{request.repo}/pulls/{request.pr_number}"
            pr_response = await client.get(pr_url, headers=_get_github_headers(), timeout=15.0)
            
            if pr_response.status_code != 200:
                raise HTTPException(
                    status_code=pr_response.status_code,
                    detail=f"Failed to fetch PR: {pr_response.text}"
                )
            
            pr_data = pr_response.json()
            
            # Fetch PR files
            files_url = f"{pr_url}/files"
            files_response = await client.get(files_url, headers=_get_github_headers(), timeout=15.0)
            
            if files_response.status_code != 200:
                raise HTTPException(
                    status_code=files_response.status_code,
                    detail=f"Failed to fetch PR files: {files_response.text}"
                )
            
            files_data = files_response.json()
        
        # Parse and truncate diff
        file_diffs = parse_github_files(files_data)
        truncation_result = truncate_diff_smart(
            file_diffs,
            max_chars=request.max_diff_chars,
            min_files=3
        )
        
        diff_summary = get_diff_summary(file_diffs)
        
        # Prepare context for review
        pr_title = pr_data.get("title", "")
        pr_body = pr_data.get("body", "")
        
        review_prompt = f"""Please review this pull request:

**Title:** {pr_title}
**Ticket:** {request.ticket_key or "N/A"}

**Description:**
{pr_body or "No description provided"}

**Changes Summary:**
{diff_summary}

**Diff:**
{truncation_result.truncated_diff}

Please provide a thorough code review focusing on:
1. Logic correctness and potential bugs
2. Code quality and maintainability
3. Best practices and patterns
4. Test coverage
5. Documentation

{f"Note: This diff was truncated. {truncation_result.excluded_files} files were excluded." if truncation_result.excluded_files > 0 else ""}
"""
        
        # Generate review using Claude
        client = _get_anthropic_client()
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=3000,
            system=MANAGER_AGENT_SYSTEM,
            messages=[{"role": "user", "content": review_prompt}]
        )
        
        review_text = response.content[0].text
        
        # Prepare truncation info
        truncation_info = None
        if truncation_result.excluded_files > 0:
            truncation_info = {
                "total_files": truncation_result.total_files,
                "included_files": truncation_result.included_files,
                "excluded_files": truncation_result.excluded_files,
                "excluded_file_list": truncation_result.excluded_file_list,
                "total_size": truncation_result.total_size,
                "truncated_size": truncation_result.truncated_size
            }
        
        return ReviewPRResponse(
            review=review_text,
            diff_summary=diff_summary,
            truncation_info=truncation_info,
            success=True
        )
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reviewing PR: {str(e)}")


@router.post("/truncate-diff", response_model=TruncateDiffResponse)
async def truncate_diff(request: TruncateDiffRequest):
    """
    Truncate a diff intelligently, prioritizing new files.
    
    This endpoint can be used standalone to test diff truncation logic
    or by other services that need smart diff truncation.
    """
    try:
        file_diffs = parse_github_files(request.files)
        truncation_result = truncate_diff_smart(
            file_diffs,
            max_chars=request.max_chars,
            min_files=request.min_files
        )
        
        summary = {
            "total_files": truncation_result.total_files,
            "included_files": truncation_result.included_files,
            "excluded_files": truncation_result.excluded_files,
            "total_size": truncation_result.total_size,
            "truncated_size": truncation_result.truncated_size,
            "excluded_file_list": truncation_result.excluded_file_list,
            "diff_summary": get_diff_summary(file_diffs)
        }
        
        return TruncateDiffResponse(
            truncated_diff=truncation_result.truncated_diff,
            summary=summary,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error truncating diff: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for Manager Agent."""
    return {
        "status": "ok",
        "service": "manager-agent",
        "features": [
            "smart_diff_truncation",
            "new_file_prioritization",
            "pr_review"
        ]
    }
