"""
tools/validation.py
───────────────────
Validation utilities for PM Agent operations.
Ensures data quality and completeness in Jira issue management.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


def validate_execution_order(
    execution_order: Optional[int],
    issue_key: Optional[str] = None,
) -> str:
    """Validate that execution_order is set on a story.
    
    Args:
        execution_order: The execution order value to validate
        issue_key: Optional issue key for logging context
    
    Returns:
        A warning message if execution_order is missing, empty string otherwise
    
    The execution_order field (customfield_10071) is critical for the Orchestrator
    to sequence ticket execution correctly. Stories without this field will not be
    picked up by the automated workflow, blocking sprint progress.
    """
    if execution_order is None:
        context = f" ({issue_key})" if issue_key else ""
        warning = (
            f"⚠️  WARNING: execution_order not set{context}. "
            "This story will not be sequenced correctly by the Orchestrator. "
            "Set execution_order based on dependencies: blockers get lower numbers, "
            "blocked stories get higher numbers."
        )
        logger.warning(warning)
        return warning
    
    return ""


def validate_story_creation(
    summary: str,
    epic_key: Optional[str] = None,
    execution_order: Optional[int] = None,
) -> list[str]:
    """Validate all required fields for story creation.
    
    Args:
        summary: The story summary
        epic_key: Optional epic key the story is linked to
        execution_order: The execution order value
    
    Returns:
        A list of warning messages for any validation issues
    """
    warnings = []
    
    # Check execution_order
    exec_warning = validate_execution_order(execution_order)
    if exec_warning:
        warnings.append(exec_warning)
    
    # Check epic linkage (informational, not critical)
    if not epic_key:
        warnings.append(
            "ℹ️  INFO: Story not linked to an Epic. "
            "Consider grouping related stories under an Epic for better organization."
        )
    
    # Check summary length
    if len(summary) > 100:
        warnings.append(
            f"ℹ️  INFO: Summary is {len(summary)} characters (recommended: <100). "
            "Consider shortening for better readability in Jira views."
        )
    
    return warnings
