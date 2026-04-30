"""
Demo script for Manager Agent diff truncation features.

This script demonstrates how to use the Manager Agent's smart diff truncation
to review pull requests with prioritization of new files.

Requirements:
- ANTHROPIC_API_KEY environment variable
- GITHUB_TOKEN environment variable
- Backend service running on localhost:8000
"""

import asyncio
import os
import httpx
from typing import Dict, Any


async def demo_truncate_diff():
    """Demo the diff truncation endpoint with sample data."""
    print("=" * 80)
    print("Demo 1: Smart Diff Truncation")
    print("=" * 80)
    
    # Sample diff data simulating a feature PR with:
    # - 2 new files (feature implementation)
    # - 2 modified files (integration)
    # - 1 deleted file (old code)
    
    sample_files = [
        {
            "filename": "features/new_dashboard.tsx",
            "status": "added",
            "additions": 250,
            "deletions": 0,
            "patch": """@@ -0,0 +1,250 @@
+import React from 'react';
+import { DashboardLayout } from './layouts';
+
+export function NewDashboard() {
+  return (
+    <DashboardLayout>
+      <h1>New Dashboard Feature</h1>
+      {/* ... 250 lines of new code ... */}
+    </DashboardLayout>
+  );
+}
"""
        },
        {
            "filename": "features/__init__.py",
            "status": "added",
            "additions": 5,
            "deletions": 0,
            "patch": """@@ -0,0 +1,5 @@
+'''Feature exports'''
+
+from .new_dashboard import NewDashboard
+
+__all__ = ['NewDashboard']
"""
        },
        {
            "filename": "app/routes.py",
            "status": "modified",
            "additions": 15,
            "deletions": 2,
            "patch": """@@ -10,7 +10,20 @@
 from flask import Blueprint
 from controllers import index, about
+from features import NewDashboard
 
 def register_routes(app):
     app.register_blueprint(index)
     app.register_blueprint(about)
+    
+    # Register new dashboard
+    @app.route('/dashboard')
+    def dashboard():
+        return render_template('dashboard.html', 
+                             component=NewDashboard)
"""
        },
        {
            "filename": "app/config.py",
            "status": "modified",
            "additions": 3,
            "deletions": 1,
            "patch": """@@ -45,7 +45,9 @@
 
 # Feature flags
-ENABLE_OLD_DASHBOARD = True
+ENABLE_OLD_DASHBOARD = False
+ENABLE_NEW_DASHBOARD = True
+DASHBOARD_REFRESH_INTERVAL = 30
"""
        },
        {
            "filename": "legacy/old_dashboard.py",
            "status": "removed",
            "additions": 0,
            "deletions": 300,
            "patch": """@@ -1,300 +0,0 @@
-# Old dashboard implementation
-# Being removed in favor of new React-based dashboard
-# ... 300 lines of deleted code ...
"""
        }
    ]
    
    async with httpx.AsyncClient() as client:
        # Test with generous limit - all files should fit
        print("\n1. With generous limit (all files fit):")
        print("-" * 80)
        
        response = await client.post(
            "http://localhost:8000/api/manager-agent/truncate-diff",
            json={
                "files": sample_files,
                "max_chars": 50000,
                "min_files": 3
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            summary = data["summary"]
            print(f"Total files: {summary['total_files']}")
            print(f"Included: {summary['included_files']}")
            print(f"Excluded: {summary['excluded_files']}")
            print(f"Summary: {summary['diff_summary']}")
            print(f"Size: {summary['truncated_size']:,} chars")
        else:
            print(f"Error: {response.status_code} - {response.text}")
        
        # Test with tight limit - should prioritize new files
        print("\n2. With tight limit (must prioritize):")
        print("-" * 80)
        
        response = await client.post(
            "http://localhost:8000/api/manager-agent/truncate-diff",
            json={
                "files": sample_files,
                "max_chars": 1500,  # Very tight limit
                "min_files": 2
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            summary = data["summary"]
            print(f"Total files: {summary['total_files']}")
            print(f"Included: {summary['included_files']}")
            print(f"Excluded: {summary['excluded_files']}")
            
            if summary['excluded_files'] > 0:
                print(f"\nExcluded files:")
                for filename in summary['excluded_file_list']:
                    print(f"  - {filename}")
                
                print(f"\nNote: New files prioritized over modified/deleted files")
            
            print(f"\nTruncation notice excerpt:")
            diff = data["truncated_diff"]
            if "DIFF TRUNCATED" in diff:
                # Extract and show the truncation notice
                start = diff.find("DIFF TRUNCATED")
                end = diff.find("=" * 80, start + 1)
                if end > start:
                    print(diff[start:end + 80])
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def demo_review_pr():
    """Demo the PR review endpoint (requires real GitHub PR)."""
    print("\n" + "=" * 80)
    print("Demo 2: Pull Request Review")
    print("=" * 80)
    
    # Check for required environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not github_token or not anthropic_key:
        print("\nSkipping PR review demo - requires GITHUB_TOKEN and ANTHROPIC_API_KEY")
        print("Set these environment variables to test PR review functionality.")
        return
    
    print("\nTo review a PR, make a request like:")
    print("""
    POST /api/manager-agent/review-pr
    {
        "owner": "your-org",
        "repo": "your-repo",
        "pr_number": 42,
        "ticket_key": "SDT1-46",
        "max_diff_chars": 50000
    }
    """)
    
    print("\nThis will:")
    print("  1. Fetch PR details from GitHub")
    print("  2. Get all file changes with diffs")
    print("  3. Truncate intelligently (prioritizing new files)")
    print("  4. Generate AI code review using Claude")
    print("  5. Return review with truncation metadata")


async def demo_priority_algorithm():
    """Demo the priority scoring algorithm."""
    print("\n" + "=" * 80)
    print("Demo 3: Priority Scoring Algorithm")
    print("=" * 80)
    
    print("\nFile change types and their priority ranges:")
    print("-" * 80)
    
    priority_examples = [
        ("NEW file (10 lines)", "added", 10, 0, 9990),
        ("NEW file (100 lines)", "added", 100, 0, 9900),
        ("NEW file (1000+ lines)", "added", 1500, 0, 9000),
        ("MODIFIED (10 lines)", "modified", 8, 2, 5000 - 10),
        ("MODIFIED (100 lines)", "modified", 80, 20, 5000 - 100),
        ("MODIFIED (1000+ lines)", "modified", 800, 200, 1),
        ("RENAMED (any size)", "renamed", 50, 0, 2500 - 50),
        ("DELETED (any size)", "removed", 0, 100, 1000 - 100),
    ]
    
    print(f"{'Description':<25} {'Type':<12} {'Changes':<10} {'Priority':<10}")
    print("-" * 80)
    
    for desc, status, adds, dels, priority in priority_examples:
        changes = f"+{adds}/-{dels}"
        print(f"{desc:<25} {status:<12} {changes:<10} {priority:<10}")
    
    print("\nKey insights:")
    print("  • NEW files always get priority 9,000-10,000 (highest)")
    print("  • MODIFIED files get priority 1-5,000 (medium)")
    print("  • Smaller changes within a category rank higher")
    print("  • DELETED files get lowest priority (often excluded first)")


async def demo_practical_scenario():
    """Demo a practical real-world scenario."""
    print("\n" + "=" * 80)
    print("Demo 4: Practical Scenario - Large Feature PR")
    print("=" * 80)
    
    print("\nScenario: Feature PR with 10 files, token limit too small for all")
    print("-" * 80)
    
    # Simulate a realistic feature PR
    pr_files = [
        # Core feature (new files) - highest priority
        ("features/user_dashboard.tsx", "added", 300, 0),
        ("features/dashboard_widgets.tsx", "added", 200, 0),
        ("features/dashboard_api.ts", "added", 150, 0),
        
        # Tests (new files) - high priority
        ("tests/test_dashboard.test.tsx", "added", 100, 0),
        
        # Integration points (modified) - medium priority
        ("app/routes.tsx", "modified", 20, 5),
        ("app/config.ts", "modified", 10, 2),
        
        # Documentation (modified) - medium priority
        ("README.md", "modified", 30, 10),
        
        # Package updates (modified) - medium priority
        ("package.json", "modified", 5, 1),
        
        # Old code removal (deleted) - lowest priority
        ("legacy/old_widgets.tsx", "removed", 0, 250),
        ("legacy/old_api.ts", "removed", 0, 180),
    ]
    
    files_data = [
        {
            "filename": filename,
            "status": status,
            "additions": adds,
            "deletions": dels,
            "patch": f"@@ Patch content for {filename}\n" + ("+" * min(adds, 10))
        }
        for filename, status, adds, dels in pr_files
    ]
    
    async with httpx.AsyncClient() as client:
        # Test with limit that fits only ~5 files
        response = await client.post(
            "http://localhost:8000/api/manager-agent/truncate-diff",
            json={
                "files": files_data,
                "max_chars": 3000,
                "min_files": 3
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            summary = data["summary"]
            
            print(f"\nInput: {summary['total_files']} files")
            print(f"Output: {summary['included_files']} included, {summary['excluded_files']} excluded")
            print(f"\nIncluded files (in truncated diff):")
            
            # Parse which files were included
            diff = data["truncated_diff"]
            for filename, status, adds, dels in pr_files:
                if filename in diff and "excluded" not in diff[:diff.find(filename)].lower():
                    priority = "NEW" if status == "added" else "MODIFIED" if status == "modified" else "DELETED"
                    print(f"  ✓ {filename} [{priority}] (+{adds}/-{dels})")
            
            if summary['excluded_files'] > 0:
                print(f"\nExcluded files:")
                for filename in summary['excluded_file_list']:
                    # Find the file data
                    for fname, status, adds, dels in pr_files:
                        if fname == filename:
                            priority = "NEW" if status == "added" else "MODIFIED" if status == "modified" else "DELETED"
                            print(f"  ✗ {filename} [{priority}] (+{adds}/-{dels})")
                            break
            
            print(f"\nResult: Core feature files (new) prioritized for review!")
            print(f"Deleted legacy files excluded as they're less critical.")
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "Manager Agent Diff Truncation Demo" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        await demo_truncate_diff()
        await demo_review_pr()
        await demo_priority_algorithm()
        await demo_practical_scenario()
        
        print("\n" + "=" * 80)
        print("Demo Complete!")
        print("=" * 80)
        print("\nFor more information, see: docs/MANAGER_AGENT_DIFF_TRUNCATION.md")
        
    except httpx.ConnectError:
        print("\n" + "!" * 80)
        print("ERROR: Could not connect to backend service")
        print("!" * 80)
        print("\nPlease ensure the backend is running:")
        print("  cd uat/backend")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
