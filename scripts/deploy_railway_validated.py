#!/usr/bin/env python3
"""
Railway Deployment Script with Validation and Alerting

This script deploys services to Railway with comprehensive validation
and alerting capabilities.
"""

import os
import sys
import argparse
from typing import List, Tuple

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'uat', 'backend'))

from railway_deploy_validator import RailwayDeployValidator, ValidationResult
from railway_alerting import DeploymentAlert, send_deployment_summary


def deploy_service(
    validator: RailwayDeployValidator,
    alerter: DeploymentAlert,
    service_name: str,
    environment: str = "production",
    validate: bool = True,
    commit_sha: str = None,
    branch: str = None
) -> bool:
    """
    Deploy a single service with validation and alerting.
    
    Args:
        validator: Railway deployment validator instance
        alerter: Deployment alerter instance
        service_name: Name of the service to deploy
        environment: Target environment
        validate: Whether to validate deployment status
        commit_sha: Git commit SHA
        branch: Git branch name
        
    Returns:
        True if deployment successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Deploying service: {service_name}")
    print(f"Environment: {environment}")
    print(f"{'='*60}\n")
    
    # Resolve service and environment IDs
    print("Resolving service and environment IDs...")
    service_id, env_id = validator.resolve_service_and_environment(
        service_name,
        environment
    )
    
    if not service_id or not env_id:
        error_msg = f"Failed to resolve IDs for service '{service_name}' in environment '{environment}'"
        print(f"ERROR: {error_msg}")
        alerter.alert_deployment_failure(
            service_name=service_name,
            environment=environment,
            error_message=error_msg,
            commit_sha=commit_sha,
            branch=branch
        )
        return False
    
    print(f"✓ Resolved: service_id={service_id}, env_id={env_id}")
    
    # Trigger redeploy
    print("Triggering redeploy...")
    redeploy_result = validator.trigger_redeploy(service_id, env_id)
    
    if not redeploy_result.success:
        print(f"ERROR: {redeploy_result.message}")
        alerter.alert_deployment_failure(
            service_name=service_name,
            environment=environment,
            error_message=redeploy_result.message,
            commit_sha=commit_sha,
            branch=branch,
            error_details=redeploy_result.error_details
        )
        return False
    
    print(f"✓ Redeploy triggered: {redeploy_result.message}")
    deployment_id = redeploy_result.deployment_id
    
    # Validate deployment if requested
    if validate:
        print("Validating deployment status...")
        validation_result = validator.validate_deployment_status(
            service_id,
            env_id,
            timeout_seconds=300,
            check_interval=10
        )
        
        if not validation_result.success:
            print(f"ERROR: {validation_result.message}")
            alerter.alert_deployment_failure(
                service_name=service_name,
                environment=environment,
                error_message=validation_result.message,
                deployment_id=validation_result.deployment_id or deployment_id,
                commit_sha=commit_sha,
                branch=branch,
                error_details=validation_result.error_details
            )
            return False
        
        print(f"✓ Deployment validated: {validation_result.message}")
        deployment_id = validation_result.deployment_id or deployment_id
    
    # Send success alert
    alerter.alert_deployment_success(
        service_name=service_name,
        environment=environment,
        deployment_id=deployment_id,
        commit_sha=commit_sha,
        branch=branch
    )
    
    print(f"\n✓ Successfully deployed {service_name}")
    return True


def main() -> int:
    """
    Main entry point for Railway deployment script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="Deploy services to Railway with validation and alerting"
    )
    parser.add_argument(
        "--services",
        nargs="+",
        help="Service names to deploy (space-separated)"
    )
    parser.add_argument(
        "--environment",
        default="production",
        help="Target environment (default: production)"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip deployment status validation"
    )
    parser.add_argument(
        "--commit-sha",
        help="Git commit SHA for tracking"
    )
    parser.add_argument(
        "--branch",
        help="Git branch name"
    )
    
    args = parser.parse_args()
    
    # Get required environment variables
    railway_token = os.getenv("RAILWAY_TOKEN")
    project_id = os.getenv("RAILWAY_PROJECT_ID")
    
    if not railway_token or not project_id:
        print("ERROR: RAILWAY_TOKEN and RAILWAY_PROJECT_ID must be set")
        return 1
    
    # Initialize validator and alerter
    validator = RailwayDeployValidator(railway_token, project_id)
    alerter = DeploymentAlert()
    
    # Validate API connectivity
    print("=== Validating Railway API connectivity ===")
    connectivity_result = validator.validate_api_connectivity()
    print(f"Result: {connectivity_result.message}")
    
    if not connectivity_result.success:
        print("FAILED: Cannot connect to Railway API")
        alerter.alert_api_connectivity_failure(
            error_message=connectivity_result.message,
            project_id=project_id
        )
        return 1
    
    # Determine services to deploy
    services_to_deploy = args.services or [
        "synpro-virtual-dev-team",
        "Virtual-Dev-Team-UAT-Frontend"
    ]
    
    print(f"\n=== Deploying {len(services_to_deploy)} service(s) ===")
    for service in services_to_deploy:
        print(f"  - {service}")
    
    # Deploy each service
    successful = 0
    failed = 0
    
    for service_name in services_to_deploy:
        success = deploy_service(
            validator=validator,
            alerter=alerter,
            service_name=service_name,
            environment=args.environment,
            validate=not args.no_validate,
            commit_sha=args.commit_sha,
            branch=args.branch
        )
        
        if success:
            successful += 1
        else:
            failed += 1
    
    # Send summary
    print(f"\n{'='*60}")
    print("=== Deployment Summary ===")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"{'='*60}\n")
    
    build_url = os.getenv("GITHUB_SERVER_URL")
    if build_url:
        repo = os.getenv("GITHUB_REPOSITORY")
        run_id = os.getenv("GITHUB_RUN_ID")
        if repo and run_id:
            build_url = f"{build_url}/{repo}/actions/runs/{run_id}"
    
    send_deployment_summary(
        successful_deploys=successful,
        failed_deploys=failed,
        warnings=0,
        build_url=build_url
    )
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
