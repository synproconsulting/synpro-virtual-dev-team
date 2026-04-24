"""Auto review functionality for pull requests."""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """PR review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    COMMENTED = "commented"


@dataclass
class PRMetadata:
    """Pull request metadata."""
    pr_id: str
    title: str
    author: str
    branch: str
    target_branch: str
    files_changed: int
    lines_added: int
    lines_removed: int


class PRAutoReview:
    """Automated pull request review system."""

    def __init__(self, team_id: str, review_rules: Optional[Dict[str, Any]] = None) -> None:
        """Initialize PR auto review system.
        
        Args:
            team_id: Team identifier
            review_rules: Optional review rules configuration
        """
        self.team_id = team_id
        self.review_rules = review_rules or self._default_rules()
        self._review_history: List[Dict[str, Any]] = []

    def review_pr(self, pr_metadata: PRMetadata) -> Dict[str, Any]:
        """Perform automated review of a pull request.
        
        Args:
            pr_metadata: Pull request metadata
            
        Returns:
            Dictionary containing review results
        """
        logger.info(f"Starting auto review for PR: {pr_metadata.pr_id}")
        
        checks = self._run_checks(pr_metadata)
        status = self._determine_status(checks)
        comments = self._generate_comments(checks)
        
        review_result = {
            "pr_id": pr_metadata.pr_id,
            "status": status.value,
            "checks": checks,
            "comments": comments,
            "reviewed_at": self._get_timestamp()
        }
        
        self._review_history.append(review_result)
        logger.info(f"Auto review completed for PR {pr_metadata.pr_id}: {status.value}")
        
        return review_result

    def _run_checks(self, pr_metadata: PRMetadata) -> Dict[str, bool]:
        """Run automated checks on PR.
        
        Args:
            pr_metadata: Pull request metadata
            
        Returns:
            Dictionary of check results
        """
        max_files = self.review_rules.get("max_files_changed", 50)
        max_lines = self.review_rules.get("max_lines_changed", 1000)
        
        total_lines = pr_metadata.lines_added + pr_metadata.lines_removed
        
        return {
            "size_check": pr_metadata.files_changed <= max_files,
            "lines_check": total_lines <= max_lines,
            "branch_name_check": self._validate_branch_name(pr_metadata.branch),
            "target_branch_check": pr_metadata.target_branch in ["main", "master", "develop"]
        }

    def _determine_status(self, checks: Dict[str, bool]) -> ReviewStatus:
        """Determine review status based on checks.
        
        Args:
            checks: Dictionary of check results
            
        Returns:
            Review status
        """
        if all(checks.values()):
            return ReviewStatus.APPROVED
        elif checks["size_check"] and checks["lines_check"]:
            return ReviewStatus.COMMENTED
        else:
            return ReviewStatus.CHANGES_REQUESTED

    def _generate_comments(self, checks: Dict[str, bool]) -> List[str]:
        """Generate review comments based on check results.
        
        Args:
            checks: Dictionary of check results
            
        Returns:
            List of comment strings
        """
        comments = []
        
        if not checks["size_check"]:
            comments.append("PR contains too many files. Consider breaking it down.")
        if not checks["lines_check"]:
            comments.append("PR has too many line changes. Consider smaller PRs.")
        if not checks["branch_name_check"]:
            comments.append("Branch name doesn't follow naming conventions.")
        if not checks["target_branch_check"]:
            comments.append("Target branch should be main, master, or develop.")
            
        return comments

    def _validate_branch_name(self, branch: str) -> bool:
        """Validate branch naming convention.
        
        Args:
            branch: Branch name
            
        Returns:
            True if valid, False otherwise
        """
        valid_prefixes = ["feature/", "bugfix/", "hotfix/", "release/"]
        return any(branch.startswith(prefix) for prefix in valid_prefixes)

    def _default_rules(self) -> Dict[str, Any]:
        """Get default review rules."""
        return {
            "max_files_changed": 50,
            "max_lines_changed": 1000
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def get_review_history(self) -> List[Dict[str, Any]]:
        """Get review history.
        
        Returns:
            List of review results
        """
        return self._review_history.copy()
