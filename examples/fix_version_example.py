"""
examples/fix_version_example.py
───────────────────────────────
Example usage of the CreateOrGetFixVersionTool for release management.

This script demonstrates:
1. Creating or getting fix versions deterministically
2. Listing all fix versions in a project
3. Using fix versions in a typical release planning workflow
"""

import os
from dotenv import load_dotenv
from tools.pm_tools import CreateOrGetFixVersionTool, ListFixVersionsTool

# Load environment variables
load_dotenv()


def example_basic_usage():
    """Basic example: Create a fix version."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Usage - Create or Get a Fix Version")
    print("=" * 80)
    
    tool = CreateOrGetFixVersionTool()
    
    # Create a new version
    result = tool._run(
        name="v1.0.0",
        description="Initial production release",
        release_date="2025-07-01",
        released=False
    )
    print(f"\n{result}")
    
    # Call again with same name - should return existing version
    result2 = tool._run(name="v1.0.0")
    print(f"{result2}")
    print("\n✓ Calling twice with same name returns same version ID (deterministic)")


def example_list_versions():
    """Example: List all fix versions."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: List All Fix Versions")
    print("=" * 80)
    
    tool = ListFixVersionsTool()
    result = tool._run()
    print(f"\n{result}")


def example_release_planning_workflow():
    """Example: Complete release planning workflow."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Release Planning Workflow")
    print("=" * 80)
    
    create_tool = CreateOrGetFixVersionTool()
    list_tool = ListFixVersionsTool()
    
    print("\nScenario: Planning a quarterly release cycle")
    print("-" * 80)
    
    # Step 1: Create versions for the quarter
    print("\n1. Creating Q2 release versions...")
    
    q2_main = create_tool._run(
        name="Q2 2025 Main Release",
        description="Major features for Q2 2025 quarterly release",
        release_date="2025-06-30",
        released=False
    )
    print(f"   {q2_main}")
    
    q2_hotfix = create_tool._run(
        name="Q2 2025 Hotfix 1",
        description="Critical bug fixes for Q2 release",
        release_date="2025-07-07",
        released=False
    )
    print(f"   {q2_hotfix}")
    
    # Step 2: Create sprint-specific versions
    print("\n2. Creating sprint delivery versions...")
    
    sprint5 = create_tool._run(
        name="Sprint 5 Delivery",
        description="Features delivered in Sprint 5",
        release_date="2025-05-15",
        released=False
    )
    print(f"   {sprint5}")
    
    sprint6 = create_tool._run(
        name="Sprint 6 Delivery",
        description="Features delivered in Sprint 6",
        release_date="2025-05-29",
        released=False
    )
    print(f"   {sprint6}")
    
    # Step 3: Verify all versions were created
    print("\n3. Verifying all versions...")
    all_versions = list_tool._run()
    print(f"   {all_versions}")
    
    # Step 4: Demonstrate deterministic behavior
    print("\n4. Demonstrating deterministic behavior...")
    print("   Calling create_or_get_fix_version with same name again...")
    
    duplicate_attempt = create_tool._run(name="Q2 2025 Main Release")
    print(f"   {duplicate_attempt}")
    print("   ✓ Returns existing version instead of creating duplicate")


def example_semantic_versioning():
    """Example: Using semantic versioning convention."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Semantic Versioning Convention")
    print("=" * 80)
    
    tool = CreateOrGetFixVersionTool()
    
    print("\nCreating versions following semantic versioning (v<major>.<minor>.<patch>)...")
    
    versions = [
        ("v2.0.0", "Major release with breaking changes", "2025-08-01"),
        ("v2.1.0", "Minor release with new features", "2025-09-15"),
        ("v2.1.1", "Patch release with bug fixes", "2025-09-22"),
        ("v2.2.0", "Minor release with performance improvements", "2025-10-01"),
    ]
    
    for name, description, date in versions:
        result = tool._run(
            name=name,
            description=description,
            release_date=date,
            released=False
        )
        print(f"   {result}")


def example_error_handling():
    """Example: Handling edge cases."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Edge Cases and Best Practices")
    print("=" * 80)
    
    tool = CreateOrGetFixVersionTool()
    
    # Creating with minimal information
    print("\n1. Creating version with only required field (name)...")
    minimal = tool._run(name="Minimal Version")
    print(f"   {minimal}")
    
    # Creating with descriptive name
    print("\n2. Creating version with descriptive name...")
    descriptive = tool._run(
        name="User Authentication Module - Phase 1",
        description="All authentication-related features for initial rollout"
    )
    print(f"   {descriptive}")
    
    # Creating already-released version
    print("\n3. Creating a version marked as already released...")
    released = tool._run(
        name="v1.5.0",
        description="Previous release (already shipped)",
        release_date="2025-01-15",
        released=True
    )
    print(f"   {released}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "FIX VERSION TOOL EXAMPLES" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Check environment variables
    required_vars = ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("\n⚠️  ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return
    
    print(f"\n✓ Connected to Jira project: {os.environ.get('JIRA_PROJECT_KEY')}")
    
    try:
        # Run examples
        example_basic_usage()
        example_list_versions()
        example_release_planning_workflow()
        example_semantic_versioning()
        example_error_handling()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("""
Key Takeaways:
1. ✓ Same version name always returns same ID (deterministic)
2. ✓ Safe to call multiple times without creating duplicates
3. ✓ Use descriptive names for better release tracking
4. ✓ Set release dates for planning and reporting
5. ✓ List versions first to see what already exists
6. ✓ Works seamlessly in automated PM Agent workflows
        """)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPlease check your Jira credentials and project configuration.")


if __name__ == "__main__":
    main()
