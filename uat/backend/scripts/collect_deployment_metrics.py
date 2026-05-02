#!/usr/bin/env python3
"""
collect_deployment_metrics.py
==============================
Script to collect Railway deployment metrics for monitoring and analysis.
Generates metrics report that can be used for dashboards and alerting.

Environment variables required:
- RAILWAY_API_TOKEN: Railway API authentication token
- RAILWAY_PROJECT_ID: Railway project ID to collect metrics from
"""

import os
import sys
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from railway_api import RailwayClient, RailwayAPIError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeploymentMetricsCollector:
    """Collect and analyze Railway deployment metrics."""
    
    def __init__(self, railway_client: RailwayClient, project_id: str):
        """
        Initialize metrics collector.
        
        Args:
            railway_client: Railway API client
            project_id: Railway project ID
        """
        self.client = railway_client
        self.project_id = project_id
    
    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse ISO 8601 timestamp string.
        
        Args:
            timestamp_str: ISO 8601 timestamp string
            
        Returns:
            datetime object or None if parsing fails
        """
        try:
            # Handle both with and without microseconds
            if "." in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None
    
    def calculate_build_time(
        self,
        created_at: str,
        updated_at: Optional[str]
    ) -> Optional[float]:
        """
        Calculate build time in seconds.
        
        Args:
            created_at: Deployment creation timestamp
            updated_at: Deployment completion timestamp
            
        Returns:
            Build time in seconds or None if calculation fails
        """
        if not updated_at:
            return None
        
        created = self.parse_timestamp(created_at)
        updated = self.parse_timestamp(updated_at)
        
        if created and updated:
            delta = updated - created
            return delta.total_seconds()
        
        return None
    
    async def collect_service_metrics(
        self,
        service_id: str,
        service_name: str,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Collect metrics for a specific service.
        
        Args:
            service_id: Railway service ID
            service_name: Human-readable service name
            lookback_days: Number of days to look back for deployments
            
        Returns:
            Dictionary with service metrics
        """
        try:
            # Get recent deployments (Railway limits to most recent)
            deployments = await self.client.get_service_deployments(
                service_id,
                limit=50  # Get more for better statistics
            )
            
            if not deployments:
                return {
                    "service_id": service_id,
                    "service_name": service_name,
                    "total_deployments": 0,
                    "message": "No deployments found"
                }
            
            # Filter deployments within lookback period
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            recent_deployments = []
            
            for deployment in deployments:
                created_at = self.parse_timestamp(deployment.get("createdAt", ""))
                if created_at and created_at >= cutoff_date:
                    recent_deployments.append(deployment)
            
            # Calculate statistics
            total = len(recent_deployments)
            
            status_counts = defaultdict(int)
            build_times = []
            
            for deployment in recent_deployments:
                status = deployment.get("status", "UNKNOWN")
                status_counts[status] += 1
                
                # Calculate build time if available
                build_time = self.calculate_build_time(
                    deployment.get("createdAt", ""),
                    deployment.get("updatedAt")
                )
                if build_time:
                    build_times.append(build_time)
            
            # Calculate success rate
            successful = status_counts.get("SUCCESS", 0)
            failed = status_counts.get("FAILED", 0) + status_counts.get("CRASHED", 0)
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # Calculate average build time
            avg_build_time = (
                sum(build_times) / len(build_times) if build_times else None
            )
            
            # Get latest deployment info
            latest = recent_deployments[0] if recent_deployments else None
            
            metrics = {
                "service_id": service_id,
                "service_name": service_name,
                "lookback_days": lookback_days,
                "total_deployments": total,
                "successful_deployments": successful,
                "failed_deployments": failed,
                "in_progress_deployments": (
                    status_counts.get("BUILDING", 0) +
                    status_counts.get("DEPLOYING", 0) +
                    status_counts.get("QUEUED", 0)
                ),
                "success_rate": round(success_rate, 2),
                "avg_build_time_seconds": (
                    round(avg_build_time, 2) if avg_build_time else None
                ),
                "min_build_time_seconds": (
                    round(min(build_times), 2) if build_times else None
                ),
                "max_build_time_seconds": (
                    round(max(build_times), 2) if build_times else None
                ),
                "status_breakdown": dict(status_counts),
                "latest_deployment": {
                    "id": latest.get("id"),
                    "status": latest.get("status"),
                    "created_at": latest.get("createdAt")
                } if latest else None
            }
            
            return metrics
        
        except RailwayAPIError as e:
            logger.error(f"Error collecting metrics for {service_name}: {e}")
            return {
                "service_id": service_id,
                "service_name": service_name,
                "error": str(e)
            }
    
    async def collect_project_metrics(
        self,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Collect metrics for all services in the project.
        
        Args:
            lookback_days: Number of days to look back for deployments
            
        Returns:
            Dictionary with project-wide metrics
        """
        logger.info(f"Collecting metrics for project {self.project_id}")
        
        try:
            # Get all services
            services = await self.client.get_project_services(self.project_id)
            logger.info(f"Found {len(services)} services")
            
            # Collect metrics for each service
            service_metrics = []
            for service in services:
                service_id = service["id"]
                service_name = service["name"]
                
                logger.info(f"Collecting metrics for service: {service_name}")
                metrics = await self.collect_service_metrics(
                    service_id,
                    service_name,
                    lookback_days
                )
                service_metrics.append(metrics)
            
            # Calculate aggregate metrics
            total_deployments = sum(
                m.get("total_deployments", 0) for m in service_metrics
            )
            total_successful = sum(
                m.get("successful_deployments", 0) for m in service_metrics
            )
            total_failed = sum(
                m.get("failed_deployments", 0) for m in service_metrics
            )
            
            overall_success_rate = (
                (total_successful / total_deployments * 100)
                if total_deployments > 0 else 0
            )
            
            # Calculate average build time across all services
            all_build_times = [
                m.get("avg_build_time_seconds")
                for m in service_metrics
                if m.get("avg_build_time_seconds") is not None
            ]
            avg_build_time = (
                sum(all_build_times) / len(all_build_times)
                if all_build_times else None
            )
            
            project_metrics = {
                "project_id": self.project_id,
                "timestamp": datetime.utcnow().isoformat(),
                "lookback_days": lookback_days,
                "total_services": len(services),
                "total_deployments": total_deployments,
                "successful_deployments": total_successful,
                "failed_deployments": total_failed,
                "overall_success_rate": round(overall_success_rate, 2),
                "avg_build_time_seconds": (
                    round(avg_build_time, 2) if avg_build_time else None
                ),
                "services": service_metrics
            }
            
            return project_metrics
        
        except RailwayAPIError as e:
            logger.error(f"Error collecting project metrics: {e}")
            raise
    
    def generate_summary_report(self, metrics: Dict[str, Any]) -> str:
        """
        Generate human-readable summary report.
        
        Args:
            metrics: Project metrics dictionary
            
        Returns:
            Formatted summary report string
        """
        report = []
        report.append("=" * 70)
        report.append("Railway Deployment Metrics Report")
        report.append("=" * 70)
        report.append(f"Project ID: {metrics['project_id']}")
        report.append(f"Generated: {metrics['timestamp']}")
        report.append(f"Lookback Period: {metrics['lookback_days']} days")
        report.append("-" * 70)
        report.append("\nProject-wide Summary:")
        report.append(f"  Total Services: {metrics['total_services']}")
        report.append(f"  Total Deployments: {metrics['total_deployments']}")
        report.append(f"  Successful: {metrics['successful_deployments']}")
        report.append(f"  Failed: {metrics['failed_deployments']}")
        report.append(f"  Success Rate: {metrics['overall_success_rate']}%")
        
        if metrics['avg_build_time_seconds']:
            report.append(
                f"  Avg Build Time: {metrics['avg_build_time_seconds']}s "
                f"({metrics['avg_build_time_seconds'] / 60:.1f} min)"
            )
        
        report.append("\n" + "-" * 70)
        report.append("Per-Service Metrics:")
        report.append("-" * 70)
        
        for service in metrics['services']:
            if "error" in service:
                report.append(f"\n{service['service_name']}: ERROR - {service['error']}")
                continue
            
            report.append(f"\n{service['service_name']}:")
            report.append(f"  Deployments: {service['total_deployments']}")
            report.append(f"  Success Rate: {service['success_rate']}%")
            
            if service['avg_build_time_seconds']:
                report.append(
                    f"  Avg Build Time: {service['avg_build_time_seconds']}s"
                )
            
            if service['latest_deployment']:
                latest = service['latest_deployment']
                report.append(
                    f"  Latest: {latest['status']} ({latest['created_at']})"
                )
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)


async def main() -> int:
    """
    Main entry point for metrics collection script.
    
    Returns:
        Exit code (0 for success, 1 for error)
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
    
    try:
        # Create client and collector
        client = RailwayClient(api_token=api_token)
        collector = DeploymentMetricsCollector(
            railway_client=client,
            project_id=project_id
        )
        
        # Collect metrics
        metrics = await collector.collect_project_metrics(lookback_days=30)
        
        # Generate summary report
        summary = collector.generate_summary_report(metrics)
        print(summary)
        
        # Write metrics to JSON file for CI artifacts
        output_file = "metrics.json"
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics written to {output_file}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
