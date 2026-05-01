"""
examples/fix_version_example.py
────────────────────────────────
Example usage of fix version management tools.

This script demonstrates how to:
1. Create or get fix versions with deterministic IDs
2. List existing fix versions
3. Integrate fix versions with sprint planning
4. Handle version lifecycle (unreleased → released → archived)

Before running, ensure environment variables are set:
    JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY, JIRA_BOARD_ID
"""

import os
from datetime import datetime, timedelta
from tools import jira_client


def example_1_create_sprint_versions():
    """Example 1: Create fix versions for multiple sprints."""
    print("=" * 60)
    print("Example 1: Creating Fix Versions for Sprint Planning")
    print("=" * 60)
    
    # Define sprint details
    sprints = [
        {
            "name": "Sprint 1 - Authentication",
            "description": "User authentication and authorization features",
            "weeks": 2,
        },
        {
            "name": "Sprint 2 - Dashboard",
            "description": "Admin dashboard and reporting",
            "weeks": 2,
        },
        {
            "name": "Sprint 3 - Mobile App",
            "description": "Mobile application development",
            "weeks": 2,
        },
    ]
    
    # Create fix versions for each sprint
    start_date = datetime.now()
    
    for i, sprint in enumerate(sprints):
        release_date = start_date + timedelta(weeks=sprint["weeks"] * (i + 1))
        release_date_str = release_date.strftime("%Y-%m-%d")
        
        print(f"\nCreating version for {sprint['name']}...")
        
        result = jira_client.create_or_get_fix_version(
            name=sprint["name"],
            description=sprint["description"],
            release_date=release_date_str,
            archived=False,
            released=False
        )
        
        if result["created"]:
            print(f"  ✓ Created new version: {result['name']} (ID: {result['id']})")
        else:
            print(f"  ℹ Found existing version: {result['name']} (ID: {result['id']})")
        
        print(f"    Release date: {result['release_date']}")
        print(f"    Description: {result['description']}")


def example_2_idempotent_behavior():
    """Example 2: Demonstrate idempotent behavior."""
    print("\n" + "=" * 60)
    print("Example 2: Idempotent Behavior - Same ID Every Time")
    print("=" * 60)
    
    version_name = "Test Version - Idempotent Example"
    
    # Call 1
    print(f"\nFirst call with name '{version_name}'...")
    result1 = jira_client.create_or_get_fix_version(
        name=version_name,
        description="Testing idempotency"
    )
    print(f"  Version ID: {result1['id']}")
    print(f"  Created: {result1['created']}")
    
    # Call 2 - should return same ID
    print(f"\nSecond call with same name...")
    result2 = jira_client.create_or_get_fix_version(
        name=version_name,
        description="Different description"  # This won't change existing version
    )
    print(f"  Version ID: {result2['id']}")
    print(f"  Created: {result2['created']}")
    
    # Call 3 - should still return same ID
    print(f"\nThird call with same name...")
    result3 = jira_client.create_or_get_fix_version(
        name=version_name
    )
    print(f"  Version ID: {result3['id']}")
    print(f"  Created: {result3['created']}")
    
    # Verify all IDs are the same
    print(f"\n✓ All calls returned the same ID: {result1['id'] == result2['id'] == result3['id']}")


def example_3_list_versions():
    """Example 3: List and filter fix versions."""
    print("\n" + "=" * 60)
    print("Example 3: Listing Fix Versions with Filtering")
    print("=" * 60)
    
    # List all unreleased versions
    print("\n1. Unreleased versions only:")
    unreleased = jira_client.list_fix_versions(
        include_archived=False,
        include_released=False
    )
    
    if unreleased:
        for v in unreleased:
            print(f"  • {v['name']} (ID: {v['id']})")
            if v.get('release_date'):
                print(f"    Target release: {v['release_date']}")
    else:
        print("  No unreleased versions found.")
    
    # List all versions (including released)
    print("\n2. All active versions (released + unreleased):")
    all_versions = jira_client.list_fix_versions(
        include_archived=False,
        include_released=True
    )
    
    if all_versions:
        for v in all_versions:
            status = "Released" if v.get('released') else "Unreleased"
            print(f"  • {v['name']} — {status}")
    else:
        print("  No versions found.")


def example_4_semantic_versioning():
    """Example 4: Use semantic versioning pattern."""
    print("\n" + "=" * 60)
    print("Example 4: Semantic Versioning Pattern")
    print("=" * 60)
    
    versions = [
        ("v1.0.0", "Initial release with core features"),
        ("v1.1.0", "Minor update with bug fixes"),
        ("v1.2.0", "New reporting features"),
        ("v2.0.0", "Major update with breaking changes"),
    ]
    
    for version_name, description in versions:
        print(f"\nCreating/getting {version_name}...")
        
        result = jira_client.create_or_get_fix_version(
            name=version_name,
            description=description
        )
        
        action = "Created" if result["created"] else "Found"
        print(f"  {action}: {version_name} (ID: {result['id']})")


def example_5_sprint_integration():
    """Example 5: Integrate fix versions with sprint creation."""
    print("\n" + "=" * 60)
    print("Example 5: Sprint + Fix Version Integration")
    print("=" * 60)
    
    sprint_name = "Sprint 5"
    version_name = "Sprint 5 - API Integration"
    
    # Step 1: Create fix version
    print(f"\nStep 1: Creating fix version '{version_name}'...")
    version_result = jira_client.create_or_get_fix_version(
        name=version_name,
        description="API integration and third-party services",
        release_date=(datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d")
    )
    print(f"  Version ID: {version_result['id']}")
    
    # Step 2: Create sprint
    print(f"\nStep 2: Creating sprint '{sprint_name}'...")
    try:
        sprint_result = jira_client.create_sprint(
            name=sprint_name,
            goal="Complete API integration",
            start_date=(datetime.now()).isoformat() + "Z",
            end_date=(datetime.now() + timedelta(weeks=2)).isoformat() + "Z"
        )
        print(f"  Sprint ID: {sprint_result['id']}")
        print(f"  Sprint Name: {sprint_result['name']}")
        
        print(f"\n✓ Sprint and fix version created successfully!")
        print(f"  Use version ID {version_result['id']} to tag issues in this sprint.")
    except Exception as e:
        print(f"  Note: Sprint creation skipped ({str(e)})")
        print(f"  But fix version is ready to use!")


def example_6_version_lifecycle():
    """Example 6: Demonstrate version lifecycle management."""
    print("\n" + "=" * 60)
    print("Example 6: Version Lifecycle Management")
    print("=" * 60)
    
    print("\n1. Create unreleased version:")
    version = jira_client.create_or_get_fix_version(
        name="v1.3.0 - Feature Release",
        description="New features for Q2",
        released=False,
        archived=False
    )
    print(f"  Created: {version['name']}")
    print(f"  Status: Unreleased")
    
    print("\n2. Later, you can mark it as released:")
    print("  (Use Jira API to update: released=True)")
    
    print("\n3. Eventually, archive old versions:")
    print("  (Use Jira API to update: archived=True)")
    
    print("\n4. List only active (unreleased, non-archived) versions:")
    active = jira_client.list_fix_versions(
        include_archived=False,
        include_released=False
    )
    print(f"  Active versions: {len(active)}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Fix Version Management Examples" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\nThese examples demonstrate the new deterministic fix version tools.")
    
    try:
        # Check environment variables
        required_vars = ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
        missing = [var for var in required_vars if not os.environ.get(var)]
        
        if missing:
            print(f"\n⚠ Missing environment variables: {', '.join(missing)}")
            print("Please set these variables before running the examples.")
            return
        
        # Run examples
        example_1_create_sprint_versions()
        example_2_idempotent_behavior()
        example_3_list_versions()
        example_4_semantic_versioning()
        example_5_sprint_integration()
        example_6_version_lifecycle()
        
        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. View the versions in your Jira project")
        print("  2. Use the version IDs to tag issues")
        print("  3. Integrate with your sprint planning workflow")
        print("\nSee docs/fix_version_management.md for more details.")
        print()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure your Jira credentials and project settings are correct.")


if __name__ == "__main__":
    main()
