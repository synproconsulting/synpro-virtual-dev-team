"""
examples/pm_validation_example.py
──────────────────────────────────
Example usage of PM Agent validation tools.

This script demonstrates how to use the validation tools to ensure
stories meet quality standards before creation.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.pm_validation import validate_story_creation, get_validator


def example_1_valid_story():
    """Example: Validate a well-formed story."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Valid Story")
    print("=" * 70)
    
    result = validate_story_creation(
        summary="Implement user authentication",
        description=(
            "As a user, I want to authenticate with email and password "
            "so that I can access my account securely.\n\n"
            "Acceptance Criteria:\n"
            "1. User can enter email and password\n"
            "2. Valid credentials redirect to dashboard\n"
            "3. Invalid credentials show error message\n"
            "4. Password is hashed before storage"
        ),
        epic_key="SDT1-10",
        story_points=5,
        priority="High",
        execution_order=1,
    )
    
    print(result)


def example_2_missing_execution_order():
    """Example: Validate a story missing execution_order (CRITICAL ERROR)."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Missing execution_order (CRITICAL)")
    print("=" * 70)
    
    result = validate_story_creation(
        summary="Add user profile page",
        description="Create a page where users can view and edit their profile information.",
        epic_key="SDT1-10",
        story_points=3,
        priority="Medium",
        execution_order=None,  # ❌ MISSING - CRITICAL ERROR!
    )
    
    print(result)


def example_3_multiple_warnings():
    """Example: Validate a story with multiple warnings."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Story with Multiple Warnings")
    print("=" * 70)
    
    result = validate_story_creation(
        summary="This is an extremely long summary that exceeds the recommended 100 character limit and should generate a warning",
        description="Short",  # Too short
        epic_key=None,  # Missing
        story_points=13,  # Too high (> 8)
        priority="Low",
        execution_order=5,  # ✓ At least execution_order is set
    )
    
    print(result)


def example_4_backlog_validation():
    """Example: Validate backlog health."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Backlog Validation")
    print("=" * 70)
    print("(This example requires actual Jira connection)")
    print("\nTo validate your backlog:")
    print("  1. Ensure Jira environment variables are set")
    print("  2. Use the validate_backlog tool in PM Agent")
    print("  3. Or import and call directly:")
    print()
    print("     from tools.pm_tools import ValidateBacklogTool")
    print("     tool = ValidateBacklogTool()")
    print("     result = tool._run()")
    print("     print(result)")


def example_5_programmatic_validation():
    """Example: Programmatic validation with custom logic."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Programmatic Validation")
    print("=" * 70)
    
    validator = get_validator()
    validator.clear_warnings()
    
    # Validate multiple stories and collect issues
    stories = [
        {
            "summary": "Story 1",
            "description": "A good description with enough content.",
            "execution_order": 1,
            "story_points": 3,
            "epic_key": "SDT1-1",
        },
        {
            "summary": "Story 2",
            "description": "Another good description.",
            "execution_order": None,  # Missing!
            "story_points": 5,
            "epic_key": "SDT1-1",
        },
        {
            "summary": "Story 3",
            "description": "Yet another good description.",
            "execution_order": 3,
            "story_points": None,  # Missing
            "epic_key": None,  # Missing
        },
    ]
    
    critical_issues = []
    
    for i, story in enumerate(stories, 1):
        validator.clear_warnings()
        is_valid = validator.validate_story_creation(**story)
        
        print(f"\nStory {i}: {story['summary']}")
        print(f"  Valid: {is_valid}")
        
        if validator.has_errors():
            print(f"  ❌ ERRORS:")
            for w in validator.get_warnings():
                if w.severity == "ERROR":
                    print(f"     • {w.message}")
            critical_issues.append(story["summary"])
        
        if not validator.has_errors() and validator.get_warnings():
            print(f"  ⚠️  WARNINGS:")
            for w in validator.get_warnings():
                if w.severity == "WARNING":
                    print(f"     • {w.message}")
    
    print("\n" + "-" * 70)
    print(f"Stories with critical issues: {len(critical_issues)}")
    if critical_issues:
        print(f"  {', '.join(critical_issues)}")


def example_6_validation_workflow():
    """Example: Recommended workflow for story creation."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Recommended Workflow")
    print("=" * 70)
    
    print("\nStep 1: Define story parameters")
    story_params = {
        "summary": "Implement password reset flow",
        "description": (
            "As a user, I want to reset my password if I forget it.\n\n"
            "Acceptance Criteria:\n"
            "1. User can request password reset via email\n"
            "2. Reset link expires after 1 hour\n"
            "3. User can set new password via reset link\n"
            "4. Old password is invalidated after reset"
        ),
        "epic_key": "SDT1-10",
        "story_points": 5,
        "priority": "High",
        "execution_order": 2,
    }
    
    print("✓ Story defined")
    
    print("\nStep 2: Validate before creating")
    result = validate_story_creation(**story_params)
    print(result)
    
    print("\nStep 3: Check validation result")
    if "FAILED" in result:
        print("❌ Validation failed - fix issues before creating story")
        return
    elif "WARNINGS" in result:
        print("⚠️  Warnings present - review before creating")
        print("   (But can proceed if warnings are acceptable)")
    else:
        print("✅ Validation passed - safe to create story")
    
    print("\nStep 4: Create story (if validation passed)")
    print("   create_story(**story_params)")
    print("   # Story created successfully")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("PM AGENT VALIDATION EXAMPLES")
    print("=" * 70)
    
    examples = [
        example_1_valid_story,
        example_2_missing_execution_order,
        example_3_multiple_warnings,
        example_4_backlog_validation,
        example_5_programmatic_validation,
        example_6_validation_workflow,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • ALWAYS validate stories before creation")
    print("  • execution_order is REQUIRED for Orchestrator execution")
    print("  • Fix ERROR-level issues immediately")
    print("  • Address WARNING-level issues for best practices")
    print("  • Use validate_backlog to audit overall health")
    print("\n")


if __name__ == "__main__":
    main()
