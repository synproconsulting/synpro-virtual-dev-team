#!/usr/bin/env python3
"""
Token Rotation Verification Script

This script helps verify that tokens have been properly rotated and are working
across all services. It performs health checks and basic API tests.

Usage:
    python scripts/verify-token-rotation.py --service all
    python scripts/verify-token-rotation.py --service jira
    python scripts/verify-token-rotation.py --service openai
    python scripts/verify-token-rotation.py --service github
"""

import argparse
import base64
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import requests


class TokenVerifier:
    """Verifies token rotation across different services."""

    def __init__(self, verbose: bool = False):
        """
        Initialize the token verifier.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.results: Dict[str, Dict[str, any]] = {}

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message with timestamp.

        Args:
            message: Message to log
            level: Log level (INFO, SUCCESS, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
        }.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")

    def verify_jira_token(self) -> Tuple[bool, str]:
        """
        Verify Jira API token is working.

        Returns:
            Tuple of (success: bool, message: str)
        """
        self.log("Verifying Jira API token...")

        # Get credentials from environment
        jira_email = os.getenv("JIRA_EMAIL")
        jira_token = os.getenv("JIRA_API_TOKEN")
        jira_domain = os.getenv("JIRA_DOMAIN")

        if not all([jira_email, jira_token, jira_domain]):
            return False, "Missing Jira credentials in environment variables"

        # Create auth header
        auth_string = f"{jira_email}:{jira_token}"
        auth_bytes = auth_string.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
        }

        # Test 1: Get current user
        try:
            url = f"https://{jira_domain}/rest/api/3/myself"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                user_data = response.json()
                if self.verbose:
                    self.log(
                        f"  Authenticated as: {user_data.get('emailAddress', 'Unknown')}",
                        "INFO",
                    )
            elif response.status_code == 401:
                return False, "Authentication failed - token may be invalid"
            elif response.status_code == 403:
                return False, "Authentication succeeded but access forbidden - check permissions"
            else:
                return False, f"Unexpected status code: {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

        # Test 2: Search for projects (permission check)
        try:
            url = f"https://{jira_domain}/rest/api/3/project/search?maxResults=1"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return (
                    False,
                    f"Can authenticate but cannot list projects: {response.status_code}",
                )

            if self.verbose:
                projects = response.json()
                self.log(
                    f"  Can access {len(projects.get('values', []))} project(s)", "INFO"
                )

        except requests.exceptions.RequestException as e:
            return False, f"Project search failed: {str(e)}"

        return True, "Jira API token verified successfully"

    def verify_openai_token(self) -> Tuple[bool, str]:
        """
        Verify OpenAI API key is working.

        Returns:
            Tuple of (success: bool, message: str)
        """
        self.log("Verifying OpenAI API key...")

        # Get API key from environment
        openai_key = os.getenv("OPENAI_API_KEY")

        if not openai_key:
            return False, "Missing OPENAI_API_KEY in environment variables"

        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json",
        }

        # Test 1: List models
        try:
            url = "https://api.openai.com/v1/models"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                models_data = response.json()
                model_count = len(models_data.get("data", []))
                if self.verbose:
                    self.log(f"  Can access {model_count} models", "INFO")
            elif response.status_code == 401:
                return False, "Authentication failed - API key may be invalid"
            elif response.status_code == 403:
                return False, "Authentication succeeded but access forbidden"
            else:
                return False, f"Unexpected status code: {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

        # Test 2: Verify GPT-4 access (optional)
        try:
            url = "https://api.openai.com/v1/models/gpt-4"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                if self.verbose:
                    self.log("  GPT-4 access confirmed", "INFO")
            elif response.status_code == 404:
                if self.verbose:
                    self.log("  GPT-4 not available (using GPT-3.5?)", "WARNING")
            # Don't fail if GPT-4 not available, just note it

        except requests.exceptions.RequestException:
            # Non-critical test
            pass

        return True, "OpenAI API key verified successfully"

    def verify_github_token(self) -> Tuple[bool, str]:
        """
        Verify GitHub token is working.

        Returns:
            Tuple of (success: bool, message: str)
        """
        self.log("Verifying GitHub token...")

        # Get token from environment
        github_token = os.getenv("GITHUB_TOKEN")

        if not github_token:
            return False, "Missing GITHUB_TOKEN in environment variables"

        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Test 1: Get authenticated user
        try:
            url = "https://api.github.com/user"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                user_data = response.json()
                if self.verbose:
                    self.log(
                        f"  Authenticated as: {user_data.get('login', 'Unknown')}",
                        "INFO",
                    )
            elif response.status_code == 401:
                return False, "Authentication failed - token may be invalid"
            elif response.status_code == 403:
                return False, "Authentication succeeded but access forbidden"
            else:
                return False, f"Unexpected status code: {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

        # Test 2: Check token scopes
        scopes = response.headers.get("X-OAuth-Scopes", "")
        if self.verbose:
            self.log(f"  Token scopes: {scopes}", "INFO")

        required_scopes = ["repo"]
        has_required = any(scope in scopes for scope in required_scopes)

        if not has_required:
            return (
                False,
                f"Token missing required scopes. Has: {scopes}, Needs: {required_scopes}",
            )

        # Test 3: Check rate limit
        try:
            url = "https://api.github.com/rate_limit"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                rate_data = response.json()
                core_remaining = rate_data.get("resources", {}).get("core", {}).get(
                    "remaining", 0
                )
                if self.verbose:
                    self.log(f"  Rate limit remaining: {core_remaining}", "INFO")

                if core_remaining < 100:
                    self.log("  Low rate limit remaining!", "WARNING")

        except requests.exceptions.RequestException:
            # Non-critical test
            pass

        return True, "GitHub token verified successfully"

    def verify_database_connection(self) -> Tuple[bool, str]:
        """
        Verify database connection with current credentials.

        Returns:
            Tuple of (success: bool, message: str)
        """
        self.log("Verifying database connection...")

        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            return False, "Missing DATABASE_URL in environment variables"

        try:
            # Try to import psycopg2
            try:
                import psycopg2
            except ImportError:
                return False, "psycopg2 not installed (pip install psycopg2-binary)"

            # Connect to database
            conn = psycopg2.connect(database_url, connect_timeout=10)
            cursor = conn.cursor()

            # Test query
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

            if result[0] != 1:
                return False, "Unexpected query result"

            # Check current user
            cursor.execute("SELECT current_user;")
            current_user = cursor.fetchone()[0]
            if self.verbose:
                self.log(f"  Connected as: {current_user}", "INFO")

            # Close connection
            cursor.close()
            conn.close()

            return True, "Database connection verified successfully"

        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    def verify_service_health(self, service_url: str, service_name: str) -> Tuple[
        bool, str
    ]:
        """
        Verify service health endpoint.

        Args:
            service_url: Base URL of the service
            service_name: Name of the service for logging

        Returns:
            Tuple of (success: bool, message: str)
        """
        self.log(f"Checking {service_name} health...")

        try:
            # Try /health endpoint
            url = f"{service_url}/health"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                try:
                    health_data = response.json()
                    status = health_data.get("status", "unknown")
                    if self.verbose:
                        self.log(f"  Status: {status}", "INFO")
                except json.JSONDecodeError:
                    # Health endpoint might return plain text
                    pass

                return True, f"{service_name} health check passed"
            else:
                return False, f"{service_name} returned status {response.status_code}"

        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to {service_name} at {service_url}"
        except requests.exceptions.Timeout:
            return False, f"{service_name} health check timed out"
        except requests.exceptions.RequestException as e:
            return False, f"{service_name} health check failed: {str(e)}"

    def run_verification(self, services: List[str]) -> bool:
        """
        Run verification for specified services.

        Args:
            services: List of service names to verify

        Returns:
            True if all verifications passed, False otherwise
        """
        all_passed = True
        service_map = {
            "jira": self.verify_jira_token,
            "openai": self.verify_openai_token,
            "github": self.verify_github_token,
            "database": self.verify_database_connection,
        }

        # Service health checks
        health_checks = {
            "pm-agent": os.getenv("PM_AGENT_URL", "http://localhost:8000"),
            "orchestrator": os.getenv("ORCHESTRATOR_URL", "http://localhost:8001"),
            "uat-backend": os.getenv("UAT_BACKEND_URL", "http://localhost:8002"),
        }

        print("\n" + "=" * 70)
        print("TOKEN ROTATION VERIFICATION")
        print("=" * 70 + "\n")

        # Run token verifications
        for service in services:
            if service in service_map:
                verify_func = service_map[service]
                success, message = verify_func()

                self.results[service] = {
                    "success": success,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                }

                if success:
                    self.log(message, "SUCCESS")
                else:
                    self.log(message, "ERROR")
                    all_passed = False

                print()  # Blank line between services

            elif service == "health":
                # Check service health endpoints
                for service_name, service_url in health_checks.items():
                    success, message = self.verify_service_health(
                        service_url, service_name
                    )

                    self.results[f"health_{service_name}"] = {
                        "success": success,
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                    }

                    if success:
                        self.log(message, "SUCCESS")
                    else:
                        self.log(message, "WARNING")
                        # Don't fail overall if health check fails (might be expected)

                    print()

        # Print summary
        print("=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70 + "\n")

        passed = sum(1 for r in self.results.values() if r["success"])
        total = len(self.results)

        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")

        if all_passed:
            print("\n✅ All verifications passed!")
        else:
            print("\n❌ Some verifications failed. Check logs above for details.")

        return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify token rotation across services"
    )
    parser.add_argument(
        "--service",
        choices=["all", "jira", "openai", "github", "database", "health"],
        default="all",
        help="Service to verify (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output results to JSON file",
    )

    args = parser.parse_args()

    # Determine which services to check
    if args.service == "all":
        services = ["jira", "openai", "github", "database", "health"]
    else:
        services = [args.service]

    # Run verification
    verifier = TokenVerifier(verbose=args.verbose)
    success = verifier.run_verification(services)

    # Save results if output file specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(verifier.results, f, indent=2)
        print(f"\n📄 Results saved to {args.output}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
