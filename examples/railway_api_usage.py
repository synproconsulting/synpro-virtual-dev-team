#!/usr/bin/env python3
"""
Railway API Usage Examples

This script demonstrates how to use the Railway API integration
programmatically. Useful for automation, CLI tools, or understanding
the API flow.

Prerequisites:
- Set RAILWAY_API_TOKEN environment variable
- Backend server running on http://localhost:8000

Usage:
    python examples/railway_api_usage.py
"""

import os
import sys
import asyncio
from typing import Optional
import httpx
from datetime import datetime


class RailwayAPIClient:
    """
    Simple client for the Railway API backend.
    
    This wraps the backend API endpoints for easy programmatic access.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def health_check(self) -> dict:
        """Check if Railway API is configured and accessible."""
        response = await self.client.get(f"{self.base_url}/api/railway/health")
        response.raise_for_status()
        return response.json()
    
    async def get_projects(self) -> list:
        """Get all Railway projects."""
        response = await self.client.get(f"{self.base_url}/api/railway/projects")
        response.raise_for_status()
        return response.json()["projects"]
    
    async def get_project_services(self, project_id: str) -> list:
        """Get services in a project."""
        response = await self.client.get(
            f"{self.base_url}/api/railway/projects/{project_id}/services"
        )
        response.raise_for_status()
        return response.json()["services"]
    
    async def get_environment_deployments(
        self, 
        project_id: str, 
        environment: str = "production"
    ) -> dict:
        """Get deployments for an environment."""
        response = await self.client.get(
            f"{self.base_url}/api/railway/projects/{project_id}"
            f"/environments/{environment}/deployments"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_service_deployments(
        self, 
        service_id: str,
        environment_id: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """Get deployments for a service."""
        params = {"limit": limit}
        if environment_id:
            params["environment_id"] = environment_id
        
        response = await self.client.get(
            f"{self.base_url}/api/railway/services/{service_id}/deployments",
            params=params
        )
        response.raise_for_status()
        return response.json()["deployments"]
    
    async def get_deployment_logs(
        self, 
        deployment_id: str, 
        limit: int = 100
    ) -> list:
        """Get logs for a deployment."""
        response = await self.client.get(
            f"{self.base_url}/api/railway/deployments/{deployment_id}/logs",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()["logs"]
    
    async def trigger_deployment(
        self, 
        service_id: str, 
        environment_id: str
    ) -> dict:
        """Trigger a new deployment."""
        response = await self.client.post(
            f"{self.base_url}/api/railway/deployments/trigger",
            json={
                "service_id": service_id,
                "environment_id": environment_id
            }
        )
        response.raise_for_status()
        return response.json()


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_deployment(deployment: dict):
    """Print deployment information in a readable format."""
    print(f"  Service: {deployment.get('serviceName', 'Unknown')}")
    print(f"  Status: {deployment.get('status', 'Unknown')}")
    print(f"  ID: {deployment.get('id', 'Unknown')}")
    print(f"  Created: {deployment.get('createdAt', 'Unknown')}")
    if deployment.get('staticUrl'):
        print(f"  URL: {deployment.get('staticUrl')}")
    print()


async def example_1_health_check():
    """Example 1: Check Railway API health."""
    print_header("Example 1: Health Check")
    
    async with RailwayAPIClient() as client:
        health = await client.health_check()
        
        print(f"Status: {health['status']}")
        print(f"Configured: {health['configured']}")
        
        if health['status'] == 'healthy':
            print(f"Projects available: {health.get('projects_count', 0)}")
            print("✅ Railway API is healthy and ready to use!")
        elif health['status'] == 'unconfigured':
            print("❌ Railway API token not configured")
            print("   Set RAILWAY_API_TOKEN environment variable")
        else:
            print("⚠️  Railway API is configured but not accessible")
            print(f"   Error: {health.get('error', 'Unknown error')}")


async def example_2_list_projects():
    """Example 2: List all Railway projects."""
    print_header("Example 2: List Projects")
    
    async with RailwayAPIClient() as client:
        projects = await client.get_projects()
        
        print(f"Found {len(projects)} project(s):\n")
        
        for project in projects:
            print(f"  Name: {project['name']}")
            print(f"  ID: {project['id']}")
            if project.get('description'):
                print(f"  Description: {project['description']}")
            print(f"  Created: {project['createdAt']}")
            print()


async def example_3_monitor_deployments(project_id: str):
    """Example 3: Monitor deployments in an environment."""
    print_header(f"Example 3: Monitor Deployments")
    
    async with RailwayAPIClient() as client:
        # Get production deployments
        data = await client.get_environment_deployments(
            project_id=project_id,
            environment="production"
        )
        
        deployments = data["deployments"]
        
        print(f"Environment: {data['environment']}")
        print(f"Total deployments: {len(deployments)}\n")
        
        if deployments:
            # Count by status
            status_counts = {}
            for d in deployments:
                status = d['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("Status Summary:")
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")
            
            print("\nRecent Deployments:")
            for deployment in deployments[:5]:  # Show first 5
                print_deployment(deployment)
        else:
            print("No deployments found in this environment.")


async def example_4_service_deployments(service_id: str):
    """Example 4: Get deployments for a specific service."""
    print_header(f"Example 4: Service Deployments")
    
    async with RailwayAPIClient() as client:
        deployments = await client.get_service_deployments(
            service_id=service_id,
            limit=5
        )
        
        print(f"Recent deployments for service {service_id}:\n")
        
        for deployment in deployments:
            print(f"  ID: {deployment['id']}")
            print(f"  Status: {deployment['status']}")
            print(f"  Created: {deployment['createdAt']}")
            print()


async def example_5_deployment_logs(deployment_id: str):
    """Example 5: Retrieve deployment logs."""
    print_header(f"Example 5: Deployment Logs")
    
    async with RailwayAPIClient() as client:
        logs = await client.get_deployment_logs(
            deployment_id=deployment_id,
            limit=20
        )
        
        print(f"Showing {len(logs)} recent log entries:\n")
        
        for log in logs:
            timestamp = log.get('timestamp', 'Unknown')
            severity = log.get('severity', 'INFO')
            message = log.get('message', '')
            
            print(f"[{timestamp}] {severity}: {message}")


async def example_6_trigger_deployment(service_id: str, environment_id: str):
    """Example 6: Trigger a new deployment (CAUTION!)."""
    print_header("Example 6: Trigger Deployment (CAUTION!)")
    
    print("⚠️  WARNING: This will trigger a real deployment!")
    print(f"   Service ID: {service_id}")
    print(f"   Environment ID: {environment_id}")
    
    confirm = input("\nType 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("Deployment cancelled.")
        return
    
    async with RailwayAPIClient() as client:
        result = await client.trigger_deployment(
            service_id=service_id,
            environment_id=environment_id
        )
        
        if result.get('success'):
            deployment = result['deployment']
            print("\n✅ Deployment triggered successfully!")
            print(f"   Deployment ID: {deployment['id']}")
            print(f"   Status: {deployment['status']}")
            print(f"   Created: {deployment['createdAt']}")
        else:
            print("\n❌ Failed to trigger deployment")


async def example_7_watch_deployment(service_id: str, duration: int = 60):
    """Example 7: Watch a deployment in real-time."""
    print_header("Example 7: Watch Deployment Status")
    
    print(f"Monitoring service {service_id} for {duration} seconds...")
    print("Press Ctrl+C to stop\n")
    
    async with RailwayAPIClient() as client:
        try:
            start_time = asyncio.get_event_loop().time()
            last_status = None
            
            while (asyncio.get_event_loop().time() - start_time) < duration:
                deployments = await client.get_service_deployments(
                    service_id=service_id,
                    limit=1
                )
                
                if deployments:
                    deployment = deployments[0]
                    current_status = deployment['status']
                    
                    if current_status != last_status:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Status changed: {current_status}")
                        last_status = current_status
                        
                        if current_status in ['SUCCESS', 'FAILED', 'CRASHED']:
                            print(f"\n✓ Deployment finished with status: {current_status}")
                            break
                
                await asyncio.sleep(5)  # Check every 5 seconds
        
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")


async def main():
    """Run example demonstrations."""
    
    print("\n" + "="*70)
    print("  Railway API Usage Examples")
    print("="*70)
    
    # Check if Railway API is configured
    try:
        async with RailwayAPIClient() as client:
            health = await client.health_check()
            
            if health['status'] != 'healthy':
                print("\n❌ Railway API is not configured or not accessible.")
                print("   Please check your RAILWAY_API_TOKEN environment variable.")
                return
    except Exception as e:
        print(f"\n❌ Cannot connect to backend: {e}")
        print("   Make sure the backend server is running on http://localhost:8000")
        return
    
    # Run examples
    try:
        # Example 1: Health check
        await example_1_health_check()
        
        # Example 2: List projects
        await example_2_list_projects()
        
        # Get first project for remaining examples
        async with RailwayAPIClient() as client:
            projects = await client.get_projects()
            
            if not projects:
                print("\n⚠️  No projects found. Cannot run remaining examples.")
                return
            
            project_id = projects[0]['id']
            
            # Example 3: Monitor deployments
            await example_3_monitor_deployments(project_id)
            
            # For examples 4-7, we need service IDs and deployment IDs
            # These are skipped if not provided as command-line arguments
            
            if len(sys.argv) > 1:
                service_id = sys.argv[1]
                await example_4_service_deployments(service_id)
                
                if len(sys.argv) > 2:
                    deployment_id = sys.argv[2]
                    await example_5_deployment_logs(deployment_id)
            
            # Examples 6 and 7 are commented out for safety
            # Uncomment and provide IDs to test deployment triggering
            
            # if len(sys.argv) > 3:
            #     environment_id = sys.argv[3]
            #     await example_6_trigger_deployment(service_id, environment_id)
            #     await example_7_watch_deployment(service_id)
        
        print_header("Examples Complete")
        print("To run examples with specific services:")
        print("  python examples/railway_api_usage.py [service_id] [deployment_id] [environment_id]")
        print()
    
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
