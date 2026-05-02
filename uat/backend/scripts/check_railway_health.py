#!/usr/bin/env python3
"""
check_railway_health.py
=======================
Script to check Railway deployment health status.
Used in CI/CD to validate deployments and alert on issues.

Environment variables required:
- RAILWAY_API_TOKEN: Railway API authentication token
- RAILWAY_PROJECT_ID: Railway project ID to monitor
- RAILWAY_SERVICE_ID: Railway service ID to monitor (optional)
- ALERT_WEBHOOK_URL: Webhook URL for alerts (optional)
"""

import os
import sys
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from railway_api import RailwayClient, RailwayAPIError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeploymentHealthStatus:
    """Enumeration of deployment health statuses."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RailwayHealthChecker:
    """Check Railway deployment health and report issues."""
    
    def __init__(
        self,
        railway_client: RailwayClient,
        project_id: str,
        service_id: Optional[str] = None,
        alert_webhook_url: Optional[str] = None
    ):
        """
        Initialize health checker.
        
        Args:
            railway_client: Railway API client
            project_id: Railway project ID
            service_id: Specific service ID to check (if None, checks all services)
            alert_webhook_url: Optional webhook URL for sending alerts
        """
        self.client = railway_client
        self.project_id = project_id
        self.service_id = service_id
        self.alert_webhook_url = alert_webhook_url
    
    async def check_deployment_status(
        self,
        service_id: str,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Check deployment status for a specific service.
        
        Args:
            service_id: Railway service ID
            service_name: Human-readable service name
            
        Returns:
            Dictionary with health status and details
        """
        try:
            deployments = await self.client.get_service_deployments(service_id, limit=5)
            
            if not deployments:
                return {
                    "service_id": service_id,
                    "service_name": service_name,
                    "status": DeploymentHealthStatus.UNKNOWN,
                    "message": "No deployments found",
                    "latest_deployment": None
                }
            
            latest = deployments[0]
            deployment_status = latest.get("status", "UNKNOWN")
            
            # Determine health based on deployment status
            if deployment_status == "SUCCESS":
                health_status = DeploymentHealthStatus.HEALTHY
                message = f"Latest deployment successful (ID: {latest['id']})"
            elif deployment_status in ["BUILDING", "DEPLOYING", "QUEUED"]:
                health_status = DeploymentHealthStatus.DEGRADED
                message = f"Deployment in progress: {deployment_status} (ID: {latest['id']})"
            elif deployment_status in ["FAILED", "CRASHED", "REMOVED"]:
                health_status = DeploymentHealthStatus.UNHEALTHY
                message = f"Latest deployment failed: {deployment_status} (ID: {latest['id']})"
            else:
                health_status = DeploymentHealthStatus.UNKNOWN
                message = f"Unknown deployment status: {deployment_status}"
            
            # Check for multiple recent failures
            recent_failures = [
                d for d in deployments
                if d.get("status") in ["FAILED", "CRASHED"]
            ]
            
            if len(recent_failures) >= 2:
                health_status = DeploymentHealthStatus.UNHEALTHY
                message += f" | {len(recent_failures)} recent failures detected"
            
            return {
                "service_id": service_id,
                "service_name": service_name,
                "status": health_status,
                "message": message,
                "latest_deployment": latest,
                "recent_failures": len(recent_failures),
                "total_recent_deployments": len(deployments)
            }
        
        except RailwayAPIError as e:
            logger.error(f"Error checking deployment status for {service_name}: {e}")
            return {
                "service_id": service_id,
                "service_name": service_name,
                "status": DeploymentHealthStatus.UNKNOWN,
                "message": f"API error: {str(e)}",
                "latest_deployment": None,
                "error": str(e)
            }
    
    async def check_all_services(self) -> List[Dict[str, Any]]:
        """
        Check health of all services in the project.
        
        Returns:
            List of health status dictionaries for each service
        """
        try:
            services = await self.client.get_project_services(self.project_id)
            logger.info(f"Checking health of {len(services)} services")
            
            results = []
            for service in services:
                service_id = service["id"]
                service_name = service["name"]
                
                # Skip if we're only checking a specific service
                if self.service_id and service_id != self.service_id:
                    continue
                
                logger.info(f"Checking service: {service_name} ({service_id})")
                result = await self.check_deployment_status(service_id, service_name)
                results.append(result)
            
            return results
        
        except RailwayAPIError as e:
            logger.error(f"Error fetching services: {e}")
            raise
    
    def analyze_health_results(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze health check results and produce summary.
        
        Args:
            results: List of health check results
            
        Returns:
            Summary dictionary with overall health and statistics
        """
        total_services = len(results)
        
        healthy = sum(
            1 for r in results
            if r["status"] == DeploymentHealthStatus.HEALTHY
        )
        degraded = sum(
            1 for r in results
            if r["status"] == DeploymentHealthStatus.DEGRADED
        )
        unhealthy = sum(
            1 for r in results
            if r["status"] == DeploymentHealthStatus.UNHEALTHY
        )
        unknown = sum(
            1 for r in results
            if r["status"] == DeploymentHealthStatus.UNKNOWN
        )
        
        # Determine overall health
        if unhealthy > 0:
            overall_status = DeploymentHealthStatus.UNHEALTHY
        elif degraded > 0 or unknown > 0:
            overall_status = DeploymentHealthStatus.DEGRADED
        else:
            overall_status = DeploymentHealthStatus.HEALTHY
        
        summary = {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "total_services": total_services,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "unknown": unknown,
            "results": results
        }
        
        return summary
    
    async def send_alert(self, summary: Dict[str, Any]) -> None:
        """
        Send alert if webhook URL is configured.
        
        Args:
            summary: Health check summary
        """
        if not self.alert_webhook_url:
            logger.info("No alert webhook configured, skipping alert")
            return
        
        if summary["overall_status"] == DeploymentHealthStatus.HEALTHY:
            logger.info("All services healthy, no alert needed")
            return
        
        # Prepare alert payload
        unhealthy_services = [
            r for r in summary["results"]
            if r["status"] == DeploymentHealthStatus.UNHEALTHY
        ]
        
        degraded_services = [
            r for r in summary["results"]
            if r["status"] == DeploymentHealthStatus.DEGRADED
        ]
        
        alert_message = f"⚠️ Railway Deployment Health Alert\n\n"
        alert_message += f"Overall Status: {summary['overall_status'].upper()}\n"
        alert_message += f"Total Services: {summary['total_services']}\n"
        alert_message += f"Healthy: {summary['healthy']} | "
        alert_message += f"Degraded: {summary['degraded']} | "
        alert_message += f"Unhealthy: {summary['unhealthy']}\n\n"
        
        if unhealthy_services:
            alert_message += "🚨 Unhealthy Services:\n"
            for svc in unhealthy_services:
                alert_message += f"  - {svc['service_name']}: {svc['message']}\n"
        
        if degraded_services:
            alert_message += "\n⚠️ Degraded Services:\n"
            for svc in degraded_services:
                alert_message += f"  - {svc['service_name']}: {svc['message']}\n"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.alert_webhook_url,
                    json={"text": alert_message}
                )
                response.raise_for_status()
                logger.info("Alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def run_health_check(self) -> Dict[str, Any]:
        """
        Run complete health check process.
        
        Returns:
            Health check summary
        """
        logger.info("Starting Railway deployment health check")
        logger.info(f"Project ID: {self.project_id}")
        if self.service_id:
            logger.info(f"Service ID: {self.service_id}")
        
        # Check service health
        results = await self.check_all_services()
        
        # Analyze results
        summary = self.analyze_health_results(results)
        
        # Log summary
        logger.info("-" * 60)
        logger.info("Health Check Summary")
        logger.info("-" * 60)
        logger.info(f"Overall Status: {summary['overall_status'].upper()}")
        logger.info(f"Total Services: {summary['total_services']}")
        logger.info(f"Healthy: {summary['healthy']}")
        logger.info(f"Degraded: {summary['degraded']}")
        logger.info(f"Unhealthy: {summary['unhealthy']}")
        logger.info(f"Unknown: {summary['unknown']}")
        logger.info("-" * 60)
        
        # Send alert if needed
        await self.send_alert(summary)
        
        return summary


async def main() -> int:
    """
    Main entry point for health check script.
    
    Returns:
        Exit code (0 for healthy, 1 for unhealthy)
    """
    # Validate environment variables
    api_token = os.environ.get("RAILWAY_API_TOKEN")
    if not api_token:
        logger.error("RAILWAY_API_TOKEN environment variable not set")
        return 1
    
    project_id = os.environ.get("RAILWAY_PROJECT_ID")
    if not project_id:
        logger.error("RAILWAY_PROJECT_ID environment variable not set")
        return 1
    
    service_id = os.environ.get("RAILWAY_SERVICE_ID")
    alert_webhook_url = os.environ.get("ALERT_WEBHOOK_URL")
    
    try:
        # Create client and health checker
        client = RailwayClient(api_token=api_token)
        health_checker = RailwayHealthChecker(
            railway_client=client,
            project_id=project_id,
            service_id=service_id,
            alert_webhook_url=alert_webhook_url
        )
        
        # Run health check
        summary = await health_checker.run_health_check()
        
        # Write summary to file for CI artifacts
        output_file = "health_check_results.json"
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Health check results written to {output_file}")
        
        # Exit with error if unhealthy
        if summary["overall_status"] == DeploymentHealthStatus.UNHEALTHY:
            logger.error("Health check failed: unhealthy services detected")
            return 1
        
        logger.info("Health check passed")
        return 0
    
    except Exception as e:
        logger.error(f"Health check failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
