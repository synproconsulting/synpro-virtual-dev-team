"""
Example: Using PM Agent to create stories with dependencies.

This script demonstrates how the PM Agent can:
1. Create related stories
2. Establish blocker relationships with issue links
3. Set execution order based on dependencies
4. List dependencies for verification

Run this after setting up JIRA environment variables.
"""

import os
from tools import jira_client


def example_create_dependent_stories():
    """Example: Create a set of stories with dependencies."""
    
    print("=" * 80)
    print("PM Agent Dependencies Example")
    print("=" * 80)
    print()
    
    # Step 1: Create an Epic
    print("Step 1: Creating Epic...")
    epic_result = jira_client.create_epic(
        summary="User Profile Management",
        description="Enable users to view and edit their profile information"
    )
    epic_key = epic_result["key"]
    print(f"✓ Created Epic: {epic_key}")
    print()
    
    # Step 2: Create Story A (foundational work)
    print("Step 2: Creating Story A (Database Schema)...")
    story_a = jira_client.create_story(
        summary="Design user profile database schema",
        description=(
            "As a developer, I need a database schema for user profiles "
            "so that we can store and retrieve profile information.\n\n"
            "Acceptance Criteria:\n"
            "- Schema supports username, email, bio, avatar URL\n"
            "- Migration script created\n"
            "- Unit tests for models"
        ),
        epic_key=epic_key,
        story_points=3,
        priority="High",
        execution_order=1
    )
    story_a_key = story_a["key"]
    print(f"✓ Created Story A: {story_a_key} (execution_order=1)")
    print()
    
    # Step 3: Create Story B (depends on A)
    print("Step 3: Creating Story B (API Endpoint)...")
    story_b = jira_client.create_story(
        summary="Build GET /profile API endpoint",
        description=(
            "As a frontend developer, I need an API to retrieve user profile data "
            "so that I can display it in the UI.\n\n"
            "Acceptance Criteria:\n"
            "- GET /api/profile/:userId returns profile data\n"
            "- Authentication required\n"
            "- Returns 404 for non-existent users\n"
            "- Integration tests pass"
        ),
        epic_key=epic_key,
        story_points=5,
        priority="High",
        execution_order=2
    )
    story_b_key = story_b["key"]
    print(f"✓ Created Story B: {story_b_key} (execution_order=2)")
    print()
    
    # Step 4: Create Story C (depends on B)
    print("Step 4: Creating Story C (Update Endpoint)...")
    story_c = jira_client.create_story(
        summary="Build PUT /profile API endpoint",
        description=(
            "As a user, I want to update my profile information "
            "so that my profile stays current.\n\n"
            "Acceptance Criteria:\n"
            "- PUT /api/profile/:userId updates profile data\n"
            "- Validation for all fields\n"
            "- Can only update own profile\n"
            "- Integration tests pass"
        ),
        epic_key=epic_key,
        story_points=5,
        priority="Medium",
        execution_order=3
    )
    story_c_key = story_c["key"]
    print(f"✓ Created Story C: {story_c_key} (execution_order=3)")
    print()
    
    # Step 5: Create Story D (depends on B and C)
    print("Step 5: Creating Story D (Frontend UI)...")
    story_d = jira_client.create_story(
        summary="Build profile page UI component",
        description=(
            "As a user, I want to see and edit my profile on a dedicated page "
            "so that I can manage my account information.\n\n"
            "Acceptance Criteria:\n"
            "- Profile page shows all user data\n"
            "- Edit mode with form validation\n"
            "- Save button updates via API\n"
            "- Loading and error states"
        ),
        epic_key=epic_key,
        story_points=8,
        priority="Medium",
        execution_order=4
    )
    story_d_key = story_d["key"]
    print(f"✓ Created Story D: {story_d_key} (execution_order=4)")
    print()
    
    # Step 6: Create dependency links
    print("Step 6: Creating blocker links...")
    print(f"  Creating link: {story_a_key} blocks {story_b_key}")
    jira_client.create_issue_link(
        inward_issue_key=story_b_key,
        outward_issue_key=story_a_key,
        link_type="Blocks"
    )
    print(f"  ✓ Link created")
    
    print(f"  Creating link: {story_b_key} blocks {story_c_key}")
    jira_client.create_issue_link(
        inward_issue_key=story_c_key,
        outward_issue_key=story_b_key,
        link_type="Blocks"
    )
    print(f"  ✓ Link created")
    
    print(f"  Creating link: {story_b_key} blocks {story_d_key}")
    jira_client.create_issue_link(
        inward_issue_key=story_d_key,
        outward_issue_key=story_b_key,
        link_type="Blocks"
    )
    print(f"  ✓ Link created")
    
    print(f"  Creating link: {story_c_key} blocks {story_d_key}")
    jira_client.create_issue_link(
        inward_issue_key=story_d_key,
        outward_issue_key=story_c_key,
        link_type="Blocks"
    )
    print(f"  ✓ Link created")
    print()
    
    # Step 7: Add comments explaining the dependencies
    print("Step 7: Adding explanatory comments...")
    jira_client.add_comment(
        story_b_key,
        "This story is blocked by the database schema work. "
        "We need the data model in place before building the API endpoint."
    )
    print(f"  ✓ Comment added to {story_b_key}")
    
    jira_client.add_comment(
        story_d_key,
        "This story depends on both GET and PUT endpoints. "
        "The UI needs to fetch profile data (GET) and save changes (PUT). "
        "Both must be complete before starting frontend work."
    )
    print(f"  ✓ Comment added to {story_d_key}")
    print()
    
    # Step 8: Verify links
    print("Step 8: Verifying dependencies...")
    print()
    
    print(f"Links for {story_a_key}:")
    links_a = jira_client.list_issue_links(story_a_key)
    if links_a:
        for link in links_a:
            print(f"  • {link['relationship']} {link['related_issue']}")
    else:
        print("  (No links)")
    print()
    
    print(f"Links for {story_b_key}:")
    links_b = jira_client.list_issue_links(story_b_key)
    for link in links_b:
        print(f"  • {link['relationship']} {link['related_issue']}")
    print()
    
    print(f"Links for {story_d_key}:")
    links_d = jira_client.list_issue_links(story_d_key)
    for link in links_d:
        print(f"  • {link['relationship']} {link['related_issue']}")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Epic: {epic_key}")
    print(f"Stories created: {story_a_key}, {story_b_key}, {story_c_key}, {story_d_key}")
    print()
    print("Dependency Chain:")
    print(f"  1. {story_a_key} (execution_order=1) → Database schema")
    print(f"       ↓ blocks")
    print(f"  2. {story_b_key} (execution_order=2) → GET endpoint")
    print(f"       ↓ blocks")
    print(f"  3. {story_c_key} (execution_order=3) → PUT endpoint")
    print(f"       ↓ blocks")
    print(f"  4. {story_d_key} (execution_order=4) → Frontend UI")
    print()
    print("✓ All stories created with proper dependencies and execution order")
    print()


if __name__ == "__main__":
    # Check environment variables
    required_vars = [
        "JIRA_URL",
        "JIRA_EMAIL", 
        "JIRA_API_TOKEN",
        "JIRA_PROJECT_KEY",
        "JIRA_BOARD_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please set these variables before running this example.")
        exit(1)
    
    try:
        example_create_dependent_stories()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
