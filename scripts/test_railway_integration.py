#!/usr/bin/env python3
"""
Test script for Railway integration.
Verifies Railway API connectivity and basic operations.

Usage:
    python scripts/test_railway_integration.py
    
Environment Variables Required:
    RAILWAY_API_TOKEN
    RAILWAY_PROJECT_ID
    RAILWAY_ENVIRONMENT_ID (optional)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'uat' / 'backend'
sys.path.insert(0, str(backend_path))

from railway_client import RailwayClient, RailwayClientError


async def test_railway_connection():
    """Test basic Railway API connection."""
    print("=" * 60)
    print("Railway Integration Test")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("1. Checking environment variables...")
    api_token = os.environ.get('RAILWAY_API_TOKEN')
    project_id = os.environ.get('RAILWAY_PROJECT_ID')
    environment_id = os.environ.get('RAILWAY_ENVIRONMENT_ID')
    
    if not api_token:
        print("❌ RAILWAY_API_TOKEN not set")
        return False
    print(f"   ✓ RAILWAY_API_TOKEN: {'*' * 20}{api_token[-4:]}")
    
    if not project_id:
        print("❌ RAILWAY_PROJECT_ID not set")
        return False
    print(f"   ✓ RAILWAY_PROJECT_ID: {project_id}")
    
    if environment_id:
        print(f"   ✓ RAILWAY_ENVIRONMENT_ID: {environment_id}")
    else:
        print("   ℹ RAILWAY_ENVIRONMENT_ID not set (optional)")
    print()
    
    # Initialize client
    print("2. Initializing Railway client...")
    try:
        client = RailwayClient()
        print("   ✓ Client initialized successfully")
    except RailwayClientError as e:
        print(f"   ❌ Failed to initialize client: {e}")
        return False
    print()
    
    # Test project info
    print("3. Fetching project information...")
    try:
        project_info = await client.get_project_info()
        print(f"   ✓ Project: {project_info.get('name', 'Unknown')}")
        print(f"   ✓ ID: {project_info.get('id', 'Unknown')}")
    except RailwayClientError as e:
        print(f"   ❌ Failed to fetch project info: {e}")
        return False
    print()
    
    # Test list services
    print("4. Listing services...")
    try:
        services = await client.list_services()
        print(f"   ✓ Found {len(services)} service(s):")
        for service in services:
            icon = service.icon or "📦"
            print(f"      {icon} {service.name} ({service.id})")
    except RailwayClientError as e:
        print(f"   ❌ Failed to list services: {e}")
        return False
    print()
    
    # Test list environments
    print("5. Listing environments...")
    try:
        environments = await client.list_environments()
        print(f"   ✓ Found {len(environments)} environment(s):")
        for env in environments:
            print(f"      🌍 {env.name} ({env.id})")
            print(f"         Service instances: {len(env.service_instances)}")
    except RailwayClientError as e:
        print(f"   ❌ Failed to list environments: {e}")
        return False
    print()
    
    # Test deployment history
    print("6. Fetching deployment history...")
    try:
        deployments = await client.list_deployments(limit=5)
        print(f"   ✓ Found {len(deployments)} recent deployment(s):")
        for deployment in deployments:
            status_emoji = {
                'SUCCESS': '✅',
                'FAILED': '❌',
                'BUILDING': '🔨',
                'DEPLOYING': '🚀',
                'CRASHED': '💥',
            }.get(deployment.status, '❓')
            print(f"      {status_emoji} {deployment.service_name}")
            print(f"         Status: {deployment.status}")
            print(f"         Environment: {deployment.environment_name}")
            print(f"         Created: {deployment.created_at}")
            if deployment.url:
                print(f"         URL: {deployment.url}")
    except RailwayClientError as e:
        print(f"   ❌ Failed to fetch deployment history: {e}")
        return False
    print()
    
    # Summary
    print("=" * 60)
    print("✅ All Railway integration tests passed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Start the backend: cd uat/backend && uvicorn main:app --reload")
    print("  2. Start the frontend: cd control-centre && npm run dev")
    print("  3. Navigate to UAT Deploy tab in Control Centre")
    print()
    
    return True


async def main():
    """Main entry point."""
    try:
        success = await test_railway_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
