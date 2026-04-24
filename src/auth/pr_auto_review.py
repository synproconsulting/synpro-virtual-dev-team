"""Automatic PR review functionality with configurable rules."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """PR review status enumeration."""
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    PENDING = "pending"
    COMMENTED = "commented"


@dataclass
class ReviewRule:
    """Configuration for automated review rules."""
    
    name: str
    description: str
    enabled: bool = True
    severity: str = "warning"  # info, warning, error


@dataclass
class PRData:
    """Pull request data structure."""
    
    pr_number: int
    title: str
    description: str
    files_changed: List[str]
    lines_added: int
    lines_removed: int
    author: str
    branch: str


class PRAutoReview:
    """Automated PR review system with configurable rules."""
    
    def __init__(self, rules: Optional[List[ReviewRule]] = None):
        """Initialize auto review with rules.
        
        Args:
            rules: List of review rules to apply
        """
        self.rules = rules or self._default_rules()
        self._review_cache: Dict[int, Dict[str, Any]] = {}
        logger.info(f"PRAutoReview initialized with {len(self.rules)} rules")
    
    def _default_rules(self) -> List[ReviewRule]:
        """Get default review rules.
        
        Returns:
            List of default ReviewRule objects
        """
        return [
            ReviewRule("pr_title", "PR title must follow convention"),
            ReviewRule("pr_size", "PR should not exceed 500 lines"),
            ReviewRule("test_coverage", "Tests must be included"),
            ReviewRule("no_secrets", "No hardcoded secrets allowed", severity="error")
        ]
    
    async def review_pr(self, pr_data: PRData) -> Dict[str, Any]:
        """Perform automated review on a pull request.
        
        Args:
            pr_data: Pull request data to review
            
        Returns:
            Dictionary containing review results and comments
        """
        comments: List[Dict[str, str]] = []
        violations: List[str] = []
        status = ReviewStatus.APPROVED
        
        # Apply each enabled rule
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            result = await self._apply_rule(rule, pr_data)
            if not result["passed"]:
                violations.append(rule.name)
                comments.append({
                    "rule": rule.name,
                    "message": result["message"],
                    "severity": rule.severity
                })
                
                if rule.severity == "error":
                    status = ReviewStatus.CHANGES_REQUESTED
                elif status == ReviewStatus.APPROVED:
                    status = ReviewStatus.COMMENTED
        
        review_result = {
            "pr_number": pr_data.pr_number,
            "status": status.value,
            "comments": comments,
            "violations": violations,
            "reviewed_at": "now"
        }
        
        self._review_cache[pr_data.pr_number] = review_result
        logger.info(f"PR #{pr_data.pr_number} reviewed: {status.value}")
        
        return review_result
    
    async def _apply_rule(self, rule: ReviewRule, pr_data: PRData) -> Dict[str, Any]:
        """Apply a single review rule to PR data.
        
        Args:
            rule: Rule to apply
            pr_data: PR data to check
            
        Returns:
            Dictionary with passed status and message
        """
        if rule.name == "pr_title":
            return self._check_title(pr_data.title)
        elif rule.name == "pr_size":
            return self._check_size(pr_data.lines_added + pr_data.lines_removed)
        elif rule.name == "test_coverage":
            return self._check_tests(pr_data.files_changed)
        elif rule.name == "no_secrets":
            return self._check_secrets(pr_data.description)
        
        return {"passed": True, "message": ""}
    
    def _check_title(self, title: str) -> Dict[str, Any]:
        """Check if PR title follows convention."""
        pattern = r"^\[\w+-\d+\]"
        if re.match(pattern, title):
            return {"passed": True, "message": ""}
        return {"passed": False, "message": "PR title should start with [TICKET-ID]"}
    
    def _check_size(self, total_lines: int) -> Dict[str, Any]:
        """Check if PR size is reasonable."""
        if total_lines <= 500:
            return {"passed": True, "message": ""}
        return {"passed": False, "message": f"PR too large: {total_lines} lines (max 500)"}
    
    def _check_tests(self, files: List[str]) -> Dict[str, Any]:
        """Check if tests are included."""
        has_tests = any("test_" in f for f in files)
        if has_tests:
            return {"passed": True, "message": ""}
        return {"passed": False, "message": "No test files found in PR"}
    
    def _check_secrets(self, description: str) -> Dict[str, Any]:
        """Check for potential hardcoded secrets."""
        secret_patterns = [r"api[_-]?key", r"password\s*=", r"secret\s*="]
        for pattern in secret_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return {"passed": False, "message": "Potential hardcoded secret detected"}
        return {"passed": True, "message": ""}
