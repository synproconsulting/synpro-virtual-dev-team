"""
tools/pm_validation.py
──────────────────────
Validation utilities for PM Agent actions.

Provides validation checks to ensure PM Agent follows best practices
when creating and managing Jira issues.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ValidationWarning:
    """Represents a validation warning."""
    
    def __init__(self, severity: str, message: str, issue_key: Optional[str] = None):
        """Initialize validation warning.
        
        Args:
            severity: Warning severity ('ERROR', 'WARNING', 'INFO')
            message: Warning message
            issue_key: Optional Jira issue key related to the warning
        """
        self.severity = severity
        self.message = message
        self.issue_key = issue_key
    
    def __str__(self) -> str:
        """Format warning as string."""
        prefix = f"[{self.severity}]"
        if self.issue_key:
            prefix += f" [{self.issue_key}]"
        return f"{prefix} {self.message}"


class PMValidator:
    """Validator for PM Agent actions."""
    
    def __init__(self):
        """Initialize validator."""
        self.warnings: List[ValidationWarning] = []
    
    def clear_warnings(self) -> None:
        """Clear all accumulated warnings."""
        self.warnings = []
    
    def add_warning(
        self,
        severity: str,
        message: str,
        issue_key: Optional[str] = None
    ) -> None:
        """Add a validation warning.
        
        Args:
            severity: Warning severity ('ERROR', 'WARNING', 'INFO')
            message: Warning message
            issue_key: Optional Jira issue key related to the warning
        """
        warning = ValidationWarning(severity, message, issue_key)
        self.warnings.append(warning)
        logger.warning(str(warning))
    
    def get_warnings(self) -> List[ValidationWarning]:
        """Get all accumulated warnings.
        
        Returns:
            List of ValidationWarning objects
        """
        return self.warnings
    
    def has_errors(self) -> bool:
        """Check if any errors have been recorded.
        
        Returns:
            True if any warnings have severity 'ERROR'
        """
        return any(w.severity == "ERROR" for w in self.warnings)
    
    def format_warnings(self) -> str:
        """Format all warnings as a string.
        
        Returns:
            Formatted string of all warnings
        """
        if not self.warnings:
            return "No validation warnings."
        
        lines = ["Validation Warnings:"]
        lines.extend(f"  {str(w)}" for w in self.warnings)
        return "\n".join(lines)
    
    def validate_story_creation(
        self,
        summary: str,
        description: str = "",
        epic_key: Optional[str] = None,
        story_points: Optional[int] = None,
        priority: str = "Medium",
        execution_order: Optional[int] = None,
    ) -> bool:
        """Validate story creation parameters.
        
        Args:
            summary: Story summary
            description: Story description
            epic_key: Parent epic key
            story_points: Story points estimate
            priority: Priority level
            execution_order: Execution order (customfield_10071)
        
        Returns:
            True if validation passed (warnings may still exist), False if critical errors
        """
        has_critical_error = False
        
        # Check execution_order
        if execution_order is None:
            self.add_warning(
                "ERROR",
                "Missing execution_order! Every story MUST have execution_order set. "
                "The Orchestrator depends on execution_order (customfield_10071) to sequence "
                "tickets correctly. Without it, the story cannot be executed in the sprint. "
                "Set execution_order based on dependencies: stories that block others get lower "
                "numbers (1, 2, 3, ...), independent stories get higher numbers."
            )
            has_critical_error = True
        elif execution_order < 1:
            self.add_warning(
                "ERROR",
                f"Invalid execution_order: {execution_order}. Must be >= 1."
            )
            has_critical_error = True
        
        # Check epic link
        if not epic_key:
            self.add_warning(
                "WARNING",
                "Story is not linked to an Epic. Best practice is to link all stories to an Epic "
                "for better organization and tracking."
            )
        
        # Check story points
        if story_points is None:
            self.add_warning(
                "WARNING",
                "Missing story points. Stories should be estimated for sprint planning."
            )
        elif story_points > 8:
            self.add_warning(
                "WARNING",
                f"Story points ({story_points}) exceed 8. Consider splitting this story into "
                f"smaller, more manageable pieces."
            )
        
        # Check summary length
        if len(summary) > 100:
            self.add_warning(
                "WARNING",
                f"Summary is {len(summary)} characters long (recommended: < 100). "
                f"Keep summaries concise."
            )
        
        # Check description
        if not description or len(description.strip()) < 20:
            self.add_warning(
                "WARNING",
                "Story description is too short or missing. Include clear acceptance criteria "
                "and context (Who/What/Why format recommended)."
            )
        
        return not has_critical_error
    
    def validate_backlog_health(self, issues: List[Any]) -> Dict[str, Any]:
        """Validate overall backlog health.
        
        Checks for common issues:
        - Stories without execution_order
        - Stories without epic links
        - Stories without estimates
        - Orphaned stories
        
        Args:
            issues: List of Jira issue objects
        
        Returns:
            Dictionary with validation results and statistics
        """
        stats = {
            "total_stories": 0,
            "missing_execution_order": 0,
            "missing_epic": 0,
            "missing_points": 0,
            "over_estimated": 0,
            "missing_description": 0,
        }
        
        issues_missing_order = []
        
        for issue in issues:
            issue_type = issue.fields.issuetype.name
            
            # Only validate stories
            if issue_type != "Story":
                continue
            
            stats["total_stories"] += 1
            
            # Check execution_order
            execution_order = getattr(issue.fields, "customfield_10071", None)
            if execution_order is None:
                stats["missing_execution_order"] += 1
                issues_missing_order.append(issue.key)
                self.add_warning(
                    "ERROR",
                    "Missing execution_order - this story cannot be executed by the Orchestrator!",
                    issue_key=issue.key
                )
            
            # Check epic link
            epic_link = getattr(issue.fields, "customfield_10014", None) or getattr(
                issue.fields, "parent", None
            )
            if not epic_link:
                stats["missing_epic"] += 1
                self.add_warning(
                    "WARNING",
                    "Story not linked to an Epic",
                    issue_key=issue.key
                )
            
            # Check story points
            story_points = getattr(issue.fields, "customfield_10016", None)
            if story_points is None:
                stats["missing_points"] += 1
                self.add_warning(
                    "WARNING",
                    "Missing story points estimate",
                    issue_key=issue.key
                )
            elif story_points > 8:
                stats["over_estimated"] += 1
                self.add_warning(
                    "WARNING",
                    f"Story points ({story_points}) > 8 - consider splitting",
                    issue_key=issue.key
                )
            
            # Check description
            description = issue.fields.description or ""
            if len(description.strip()) < 20:
                stats["missing_description"] += 1
                self.add_warning(
                    "INFO",
                    "Story description is too short",
                    issue_key=issue.key
                )
        
        return {
            "statistics": stats,
            "issues_missing_execution_order": issues_missing_order,
            "warnings": self.warnings,
        }


# Singleton instance for easy access
_global_validator = PMValidator()


def get_validator() -> PMValidator:
    """Get the global PM validator instance.
    
    Returns:
        Global PMValidator instance
    """
    return _global_validator


def validate_story_creation(
    summary: str,
    description: str = "",
    epic_key: Optional[str] = None,
    story_points: Optional[int] = None,
    priority: str = "Medium",
    execution_order: Optional[int] = None,
) -> str:
    """Validate story creation parameters and return warnings.
    
    This is a convenience function that uses the global validator.
    
    Args:
        summary: Story summary
        description: Story description
        epic_key: Parent epic key
        story_points: Story points estimate
        priority: Priority level
        execution_order: Execution order (customfield_10071)
    
    Returns:
        String containing validation warnings, or success message
    """
    validator = get_validator()
    validator.clear_warnings()
    
    validator.validate_story_creation(
        summary=summary,
        description=description,
        epic_key=epic_key,
        story_points=story_points,
        priority=priority,
        execution_order=execution_order,
    )
    
    if validator.has_errors():
        return f"❌ VALIDATION FAILED\n\n{validator.format_warnings()}"
    elif validator.get_warnings():
        return f"⚠️  VALIDATION WARNINGS\n\n{validator.format_warnings()}"
    else:
        return "✅ Validation passed - no issues found."
