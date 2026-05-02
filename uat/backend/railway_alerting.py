"""
Railway Deployment Alerting

Provides alerting capabilities for Railway deployment events via Slack webhooks.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import requests


class DeploymentAlert:
    """Handles deployment alerts via Slack webhooks."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize deployment alerting.
        
        Args:
            webhook_url: Slack webhook URL (defaults to SLACK_WEBHOOK_URL env var)
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
    
    def send_slack_notification(
        self,
        message: str,
        color: str = "#36a64f",
        fields: Optional[list] = None,
        title: Optional[str] = None
    ) -> bool:
        """
        Send a Slack notification via webhook.
        
        Args:
            message: Main message text
            color: Attachment color (green, red, yellow hex codes)
            fields: List of field dictionaries for Slack attachment
            title: Optional title for the message
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.webhook_url:
            print("WARNING: No Slack webhook URL configured, skipping notification")
            return False
        
        try:
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title or "Railway Deployment Notification",
                        "text": message,
                        "fields": fields or [],
                        "footer": "Railway CI/CD Pipeline",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Slack notification: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending Slack notification: {e}")
            return False
    
    def alert_deployment_success(
        self,
        service_name: str,
        environment: str,
        deployment_id: str,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None
    ) -> bool:
        """
        Send success alert for a deployment.
        
        Args:
            service_name: Name of the deployed service
            environment: Target environment
            deployment_id: Railway deployment ID
            commit_sha: Git commit SHA
            branch: Git branch name
            
        Returns:
            True if alert sent successfully
        """
        fields = [
            {"title": "Service", "value": service_name, "short": True},
            {"title": "Environment", "value": environment, "short": True},
            {"title": "Deployment ID", "value": deployment_id, "short": False}
        ]
        
        if commit_sha:
            fields.append({
                "title": "Commit",
                "value": commit_sha[:7],
                "short": True
            })
        
        if branch:
            fields.append({
                "title": "Branch",
                "value": branch,
                "short": True
            })
        
        return self.send_slack_notification(
            message=f"✅ Deployment successful for {service_name}",
            color="#36a64f",  # Green
            fields=fields,
            title="Deployment Success"
        )
    
    def alert_deployment_failure(
        self,
        service_name: str,
        environment: str,
        error_message: str,
        deployment_id: Optional[str] = None,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send failure alert for a deployment.
        
        Args:
            service_name: Name of the service
            environment: Target environment
            error_message: Error description
            deployment_id: Railway deployment ID
            commit_sha: Git commit SHA
            branch: Git branch name
            error_details: Additional error details
            
        Returns:
            True if alert sent successfully
        """
        fields = [
            {"title": "Service", "value": service_name, "short": True},
            {"title": "Environment", "value": environment, "short": True},
            {"title": "Error", "value": error_message, "short": False}
        ]
        
        if deployment_id:
            fields.append({
                "title": "Deployment ID",
                "value": deployment_id,
                "short": True
            })
        
        if commit_sha:
            fields.append({
                "title": "Commit",
                "value": commit_sha[:7],
                "short": True
            })
        
        if branch:
            fields.append({
                "title": "Branch",
                "value": branch,
                "short": True
            })
        
        if error_details:
            fields.append({
                "title": "Details",
                "value": f"```{json.dumps(error_details, indent=2)[:500]}```",
                "short": False
            })
        
        return self.send_slack_notification(
            message=f"❌ Deployment failed for {service_name}",
            color="#ff0000",  # Red
            fields=fields,
            title="Deployment Failure"
        )
    
    def alert_validation_warning(
        self,
        message: str,
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send warning alert for validation issues.
        
        Args:
            message: Warning message
            service_name: Optional service name
            details: Optional additional details
            
        Returns:
            True if alert sent successfully
        """
        fields = []
        
        if service_name:
            fields.append({
                "title": "Service",
                "value": service_name,
                "short": True
            })
        
        if details:
            fields.append({
                "title": "Details",
                "value": f"```{json.dumps(details, indent=2)[:500]}```",
                "short": False
            })
        
        return self.send_slack_notification(
            message=f"⚠️  {message}",
            color="#ffaa00",  # Orange/Yellow
            fields=fields,
            title="Deployment Warning"
        )
    
    def alert_api_connectivity_failure(
        self,
        error_message: str,
        project_id: str
    ) -> bool:
        """
        Send alert for Railway API connectivity issues.
        
        Args:
            error_message: Error description
            project_id: Railway project ID
            
        Returns:
            True if alert sent successfully
        """
        fields = [
            {"title": "Project ID", "value": project_id, "short": True},
            {"title": "Error", "value": error_message, "short": False}
        ]
        
        return self.send_slack_notification(
            message="🔌 Railway API connectivity check failed",
            color="#ff0000",  # Red
            fields=fields,
            title="API Connectivity Failure"
        )


def send_deployment_summary(
    webhook_url: Optional[str] = None,
    successful_deploys: int = 0,
    failed_deploys: int = 0,
    warnings: int = 0,
    build_url: Optional[str] = None
) -> bool:
    """
    Send a deployment summary notification.
    
    Args:
        webhook_url: Slack webhook URL
        successful_deploys: Count of successful deployments
        failed_deploys: Count of failed deployments
        warnings: Count of warnings
        build_url: CI build URL
        
    Returns:
        True if notification sent successfully
    """
    alerter = DeploymentAlert(webhook_url)
    
    if failed_deploys > 0:
        color = "#ff0000"  # Red
        emoji = "❌"
        status = "Failed"
    elif warnings > 0:
        color = "#ffaa00"  # Orange
        emoji = "⚠️"
        status = "Completed with warnings"
    else:
        color = "#36a64f"  # Green
        emoji = "✅"
        status = "Success"
    
    fields = [
        {"title": "Successful", "value": str(successful_deploys), "short": True},
        {"title": "Failed", "value": str(failed_deploys), "short": True},
        {"title": "Warnings", "value": str(warnings), "short": True}
    ]
    
    if build_url:
        fields.append({
            "title": "Build URL",
            "value": build_url,
            "short": False
        })
    
    return alerter.send_slack_notification(
        message=f"{emoji} Deployment pipeline {status}",
        color=color,
        fields=fields,
        title="Deployment Pipeline Summary"
    )
