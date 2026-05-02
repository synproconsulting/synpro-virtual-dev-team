#!/usr/bin/env python3
"""
Token rotation verification script.

This script verifies that token rotation was successful by testing
connectivity and authentication with all relevant services.

Usage:
    python3 verify_token_rotation.py --environment production
    python3 verify_token_rotation.py --environment staging --service jira
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests


class VerificationError(Exception):
    """Base exception for verification errors."""
    pass


class TokenVerifier:
    """Verifies token rotation for various services."""

    def __init__(self, environment: str, service: Optional[str] = None):
        """
        Initialize token verifier.

        Args:
            environment: Target environment (development, staging, production)
            service: Specific service to verify (if None, verify all)
        """
        self.environment = environment
        self.service = service
        self.namespace = environment

        # Load configuration
        self.config = self._load_config()

        # Results tracking
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": environment,
            "checks": [],
            "overall_status": "unknown",
        }

    def _load_config(self) -> Dict:
        """Load environment configuration."""
        # In production, this would load from a config file or environment
        # For now, return default configuration
        return {
            "jira_base_url": os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net"),
            "jira_email": os.getenv("JIRA_EMAIL", "service-account@example.com"),
            "github_api_url": "https://api.github.com",
            "openai_api_url": "https://api.openai.com/v1",
        }

    def _get_secret_value(self, secret_key: str) -> Optional[str]:
        """
        Get secret value from Kubernetes.

        Args:
            secret_key: Secret key to retrieve

        Returns:
            Secret value or None if not found
        """
        try:
            command = [
                "kubectl",
                "get",
                "secret",
                "sdt1-secrets",
                "-n",
                self.namespace,
                "-o",
                f"jsonpath={{.data.{secret_key}}}",
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout:
                import base64
                return base64.b64decode(result.stdout).decode("utf-8")

            return None

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to get secret {secret_key}: {e}")
            return None

    def _run_check(
        self, check_name: str, check_func, critical: bool = True
    ) -> Dict:
        """
        Run a verification check.

        Args:
            check_name: Name of the check
            check_func: Function to execute for the check
            critical: Whether failure is critical

        Returns:
            Check result dictionary
        """
        print(f"[CHECK] {check_name}...", end=" ")

        check_result = {
            "name": check_name,
            "critical": critical,
            "status": "unknown",
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            success, message = check_func()
            check_result["status"] = "passed" if success else "failed"
            check_result["message"] = message

            if success:
                print("✓ PASSED")
            else:
                print(f"✗ FAILED: {message}")

        except Exception as e:
            check_result["status"] = "error"
            check_result["message"] = str(e)
            print(f"✗ ERROR: {e}")

        self.results["checks"].append(check_result)
        return check_result

    def verify_jira_token(self) -> Tuple[bool, str]:
        """
        Verify Jira API token.

        Returns:
            Tuple of (success, message)
        """
        token = self._get_secret_value("JIRA_API_TOKEN")
        if not token:
            return False, "Failed to retrieve Jira token from secrets"

        try:
            # Test API call to get current user
            url = f"{self.config['jira_base_url']}/rest/api/3/myself"
            auth = (self.config["jira_email"], token)
            headers = {"Accept": "application/json"}

            response = requests.get(url, auth=auth, headers=headers, timeout=10)

            if response.status_code == 200:
                user_data = response.json()
                return True, f"Successfully authenticated as {user_data.get('displayName', 'unknown')}"
            else:
                return False, f"API returned status {response.status_code}: {response.text}"

        except requests.RequestException as e:
            return False, f"Request failed: {e}"

    def verify_openai_key(self) -> Tuple[bool, str]:
        """
        Verify OpenAI API key.

        Returns:
            Tuple of (success, message)
        """
        api_key = self._get_secret_value("OPENAI_API_KEY")
        if not api_key:
            return False, "Failed to retrieve OpenAI key from secrets"

        try:
            # Test API call to list models
            url = f"{self.config['openai_api_url']}/models"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                models = response.json()
                model_count = len(models.get("data", []))
                return True, f"Successfully authenticated, {model_count} models available"
            else:
                return False, f"API returned status {response.status_code}: {response.text}"

        except requests.RequestException as e:
            return False, f"Request failed: {e}"

    def verify_github_token(self) -> Tuple[bool, str]:
        """
        Verify GitHub API token.

        Returns:
            Tuple of (success, message)
        """
        token = self._get_secret_value("GITHUB_TOKEN")
        if not token:
            return False, "Failed to retrieve GitHub token from secrets"

        try:
            # Test API call to get authenticated user
            url = f"{self.config['github_api_url']}/user"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                user_data = response.json()
                return True, f"Successfully authenticated as {user_data.get('login', 'unknown')}"
            else:
                return False, f"API returned status {response.status_code}: {response.text}"

        except requests.RequestException as e:
            return False, f"Request failed: {e}"

    def verify_jwt_secret(self) -> Tuple[bool, str]:
        """
        Verify JWT secret is set correctly.

        Returns:
            Tuple of (success, message)
        """
        jwt_secret = self._get_secret_value("JWT_SECRET_KEY")
        if not jwt_secret:
            return False, "Failed to retrieve JWT secret from secrets"

        # Check secret length (should be at least 32 characters)
        if len(jwt_secret) < 32:
            return False, f"JWT secret too short: {len(jwt_secret)} chars (minimum 32)"

        return True, f"JWT secret configured (length: {len(jwt_secret)} chars)"

    def verify_database_connection(self) -> Tuple[bool, str]:
        """
        Verify database connection with new password.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Try to connect via a backend pod
            command = [
                "kubectl",
                "exec",
                "-n",
                self.namespace,
                "deployment/uat-backend",
                "--",
                "python3",
                "-c",
                "from database import test_connection; test_connection()",
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return True, "Database connection successful"
            else:
                return False, f"Database connection failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Database connection check timed out"
        except subprocess.CalledProcessError as e:
            return False, f"Database connection check failed: {e}"

    def verify_kubernetes_deployments(self) -> Tuple[bool, str]:
        """
        Verify all deployments are running.

        Returns:
            Tuple of (success, message)
        """
        deployments = ["uat-backend", "pm-agent", "dev-agent"]
        failed_deployments = []

        for deployment in deployments:
            try:
                command = [
                    "kubectl",
                    "get",
                    "deployment",
                    deployment,
                    "-n",
                    self.namespace,
                    "-o",
                    "jsonpath={.status.readyReplicas}/{.status.replicas}",
                ]

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                ready_total = result.stdout.strip()
                if "/" in ready_total:
                    ready, total = ready_total.split("/")
                    if ready != total:
                        failed_deployments.append(f"{deployment} ({ready}/{total})")
                else:
                    failed_deployments.append(f"{deployment} (no replicas)")

            except subprocess.CalledProcessError:
                failed_deployments.append(f"{deployment} (not found)")

        if failed_deployments:
            return False, f"Deployments not ready: {', '.join(failed_deployments)}"

        return True, f"All {len(deployments)} deployments are healthy"

    def verify_pod_logs(self) -> Tuple[bool, str]:
        """
        Check pod logs for authentication errors.

        Returns:
            Tuple of (success, message)
        """
        deployments = ["uat-backend", "pm-agent", "dev-agent"]
        errors_found = []

        error_keywords = [
            "401 Unauthorized",
            "403 Forbidden",
            "authentication failed",
            "invalid token",
            "invalid credentials",
        ]

        for deployment in deployments:
            try:
                command = [
                    "kubectl",
                    "logs",
                    f"deployment/{deployment}",
                    "-n",
                    self.namespace,
                    "--tail=100",
                    "--since=10m",
                ]

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    logs = result.stdout.lower()
                    for keyword in error_keywords:
                        if keyword.lower() in logs:
                            errors_found.append(f"{deployment}: {keyword}")

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                # Non-critical if we can't get logs
                pass

        if errors_found:
            return False, f"Auth errors found: {', '.join(errors_found)}"

        return True, "No authentication errors in recent logs"

    def verify_service_endpoints(self) -> Tuple[bool, str]:
        """
        Verify service endpoints are responding.

        Returns:
            Tuple of (success, message)
        """
        # This is environment-specific, adjust URLs as needed
        endpoints = {
            "production": "https://api.sdt1.com",
            "staging": "https://staging-api.sdt1.com",
            "development": "http://localhost:8000",
        }

        base_url = endpoints.get(self.environment)
        if not base_url:
            return True, "No endpoint configured for verification"

        try:
            # Test health endpoint
            response = requests.get(f"{base_url}/health", timeout=10)

            if response.status_code == 200:
                return True, f"Service endpoint responding (status {response.status_code})"
            else:
                return False, f"Service endpoint returned status {response.status_code}"

        except requests.RequestException as e:
            return False, f"Service endpoint unreachable: {e}"

    def verify_all(self) -> bool:
        """
        Run all verification checks.

        Returns:
            True if all critical checks passed, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"Token Rotation Verification - {self.environment.upper()}")
        print(f"{'='*60}\n")

        # Determine which services to check
        if self.service:
            services = [self.service]
        else:
            services = ["jira", "openai", "github", "jwt", "database"]

        # Run service-specific checks
        for svc in services:
            if svc == "jira":
                self._run_check("Jira API Token", self.verify_jira_token, critical=True)
            elif svc == "openai":
                self._run_check("OpenAI API Key", self.verify_openai_key, critical=True)
            elif svc == "github":
                self._run_check("GitHub API Token", self.verify_github_token, critical=True)
            elif svc == "jwt":
                self._run_check("JWT Secret Configuration", self.verify_jwt_secret, critical=True)
            elif svc == "database":
                self._run_check(
                    "Database Connection",
                    self.verify_database_connection,
                    critical=True,
                )

        # Run general checks
        self._run_check(
            "Kubernetes Deployments",
            self.verify_kubernetes_deployments,
            critical=True,
        )

        self._run_check(
            "Pod Logs (Auth Errors)",
            self.verify_pod_logs,
            critical=False,
        )

        self._run_check(
            "Service Endpoints",
            self.verify_service_endpoints,
            critical=False,
        )

        # Determine overall status
        critical_failures = [
            check for check in self.results["checks"]
            if check["critical"] and check["status"] != "passed"
        ]

        if critical_failures:
            self.results["overall_status"] = "failed"
        else:
            self.results["overall_status"] = "passed"

        # Print summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")

        total_checks = len(self.results["checks"])
        passed_checks = len([c for c in self.results["checks"] if c["status"] == "passed"])
        failed_checks = len([c for c in self.results["checks"] if c["status"] in ["failed", "error"]])

        print(f"Total checks: {total_checks}")
        print(f"Passed: {passed_checks} ✓")
        print(f"Failed: {failed_checks} ✗")
        print(f"\nOverall status: {self.results['overall_status'].upper()}")

        if critical_failures:
            print("\nCritical failures:")
            for check in critical_failures:
                print(f"  - {check['name']}: {check['message']}")

        return self.results["overall_status"] == "passed"

    def save_results(self, output_file: str = "verification_results.json") -> None:
        """
        Save verification results to file.

        Args:
            output_file: Output file path
        """
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n[INFO] Results saved to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify token rotation for SDT1 platform services",
    )

    parser.add_argument(
        "--environment",
        required=True,
        choices=["development", "staging", "production"],
        help="Target environment",
    )

    parser.add_argument(
        "--service",
        choices=["jira", "openai", "github", "jwt", "database"],
        help="Specific service to verify (if not specified, verify all)",
    )

    parser.add_argument(
        "--output",
        default="verification_results.json",
        help="Output file for results (default: verification_results.json)",
    )

    args = parser.parse_args()

    try:
        verifier = TokenVerifier(
            environment=args.environment,
            service=args.service,
        )

        success = verifier.verify_all()
        verifier.save_results(args.output)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n[INFO] Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
