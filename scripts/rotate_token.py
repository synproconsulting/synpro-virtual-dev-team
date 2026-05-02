#!/usr/bin/env python3
"""
Token rotation automation script.

This script automates the process of rotating authentication tokens across
different services and environments.

Usage:
    python3 rotate_token.py --service jira --token '<new-token>' --environment production
    python3 rotate_token.py --service jwt --token '<new-key>' --environment production --zero-downtime
    python3 rotate_token.py --service all --dry-run
"""

import argparse
import base64
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class TokenRotationError(Exception):
    """Base exception for token rotation errors."""
    pass


class TokenRotator:
    """Handles token rotation for various services."""

    SUPPORTED_SERVICES = ["jira", "openai", "github", "jwt", "database", "redis"]
    SUPPORTED_ENVIRONMENTS = ["development", "staging", "production"]

    def __init__(
        self,
        service: str,
        environment: str,
        new_token: Optional[str] = None,
        dry_run: bool = False,
        zero_downtime: bool = False,
    ):
        """
        Initialize token rotator.

        Args:
            service: Service name (jira, openai, github, jwt, database, redis)
            environment: Target environment (development, staging, production)
            new_token: New token/credential value
            dry_run: If True, only simulate rotation without applying changes
            zero_downtime: If True, use zero-downtime rotation strategy (JWT only)
        """
        if service not in self.SUPPORTED_SERVICES:
            raise ValueError(
                f"Unsupported service: {service}. "
                f"Supported: {', '.join(self.SUPPORTED_SERVICES)}"
            )

        if environment not in self.SUPPORTED_ENVIRONMENTS:
            raise ValueError(
                f"Unsupported environment: {environment}. "
                f"Supported: {', '.join(self.SUPPORTED_ENVIRONMENTS)}"
            )

        self.service = service
        self.environment = environment
        self.new_token = new_token
        self.dry_run = dry_run
        self.zero_downtime = zero_downtime

        # Service to secret key mapping
        self.service_secret_map = {
            "jira": "JIRA_API_TOKEN",
            "openai": "OPENAI_API_KEY",
            "github": "GITHUB_TOKEN",
            "jwt": "JWT_SECRET_KEY",
            "database": "DATABASE_PASSWORD",
            "redis": "REDIS_PASSWORD",
        }

        # Services that need to be restarted after rotation
        self.service_deployments = {
            "jira": ["uat-backend", "pm-agent", "dev-agent"],
            "openai": ["pm-agent", "dev-agent", "uat-backend"],
            "github": ["dev-agent", "uat-backend"],
            "jwt": ["uat-backend"],
            "database": ["uat-backend"],
            "redis": ["uat-backend"],
        }

        self.namespace = environment
        self.secret_name = "sdt1-secrets"
        self.backup_dir = Path("./backups")
        self.backup_dir.mkdir(exist_ok=True)

    def _run_command(
        self, command: List[str], capture_output: bool = True
    ) -> Tuple[int, str, str]:
        """
        Run a shell command.

        Args:
            command: Command and arguments as list
            capture_output: Whether to capture stdout/stderr

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        print(f"[CMD] {' '.join(command)}")

        if self.dry_run:
            print("[DRY-RUN] Command not executed")
            return (0, "", "")

        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                check=False,
            )
            return (result.returncode, result.stdout, result.stderr)
        except Exception as e:
            raise TokenRotationError(f"Command failed: {e}")

    def _backup_current_secret(self) -> Path:
        """
        Backup current Kubernetes secret.

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{self.secret_name}-{self.environment}-{timestamp}.yaml"

        print(f"[INFO] Backing up current secret to {backup_file}")

        command = [
            "kubectl",
            "get",
            "secret",
            self.secret_name,
            "-n",
            self.namespace,
            "-o",
            "yaml",
        ]

        returncode, stdout, stderr = self._run_command(command)

        if returncode != 0:
            raise TokenRotationError(f"Failed to backup secret: {stderr}")

        if not self.dry_run:
            backup_file.write_text(stdout)
            print(f"[SUCCESS] Secret backed up to {backup_file}")

        return backup_file

    def _get_current_secret(self) -> Dict[str, str]:
        """
        Get current secret values.

        Returns:
            Dictionary of secret key-value pairs
        """
        command = [
            "kubectl",
            "get",
            "secret",
            self.secret_name,
            "-n",
            self.namespace,
            "-o",
            "json",
        ]

        returncode, stdout, stderr = self._run_command(command)

        if returncode != 0:
            raise TokenRotationError(f"Failed to get secret: {stderr}")

        if self.dry_run:
            return {}

        secret_data = json.loads(stdout)
        decoded_data = {}

        for key, value in secret_data.get("data", {}).items():
            decoded_data[key] = base64.b64decode(value).decode("utf-8")

        return decoded_data

    def _update_secret(self, updates: Dict[str, str]) -> None:
        """
        Update Kubernetes secret with new values.

        Args:
            updates: Dictionary of key-value pairs to update
        """
        print(f"[INFO] Updating secret with new values")

        # Build kubectl command
        command = [
            "kubectl",
            "create",
            "secret",
            "generic",
            self.secret_name,
        ]

        for key, value in updates.items():
            command.extend(["--from-literal", f"{key}={value}"])

        command.extend([
            "--dry-run=client",
            "-o",
            "yaml",
            "-n",
            self.namespace,
        ])

        # First, create the secret YAML
        returncode, stdout, stderr = self._run_command(command)

        if returncode != 0:
            raise TokenRotationError(f"Failed to create secret YAML: {stderr}")

        if not self.dry_run:
            # Apply the secret
            apply_command = ["kubectl", "apply", "-f", "-", "-n", self.namespace]
            result = subprocess.run(
                apply_command,
                input=stdout,
                text=True,
                capture_output=True,
            )

            if result.returncode != 0:
                raise TokenRotationError(f"Failed to apply secret: {result.stderr}")

            print(f"[SUCCESS] Secret updated")

    def _restart_deployments(self, deployments: List[str]) -> None:
        """
        Restart Kubernetes deployments.

        Args:
            deployments: List of deployment names to restart
        """
        print(f"[INFO] Restarting deployments: {', '.join(deployments)}")

        for deployment in deployments:
            command = [
                "kubectl",
                "rollout",
                "restart",
                f"deployment/{deployment}",
                "-n",
                self.namespace,
            ]

            returncode, stdout, stderr = self._run_command(command)

            if returncode != 0:
                print(f"[WARNING] Failed to restart {deployment}: {stderr}")
            else:
                print(f"[SUCCESS] Restarted {deployment}")

            # Wait for rollout to complete
            if not self.dry_run:
                wait_command = [
                    "kubectl",
                    "rollout",
                    "status",
                    f"deployment/{deployment}",
                    "-n",
                    self.namespace,
                    "--timeout=5m",
                ]

                returncode, stdout, stderr = self._run_command(wait_command, capture_output=False)

                if returncode != 0:
                    print(f"[WARNING] Rollout status check failed for {deployment}")

    def _rotate_standard_token(self) -> None:
        """Rotate a standard token (Jira, OpenAI, GitHub, Database, Redis)."""
        if not self.new_token:
            raise TokenRotationError("New token value is required")

        # Backup current secret
        self._backup_current_secret()

        # Get current secrets
        current_secrets = self._get_current_secret()

        # Update with new token
        secret_key = self.service_secret_map[self.service]
        current_secrets[secret_key] = self.new_token

        # Update secret
        self._update_secret(current_secrets)

        # Restart affected deployments
        deployments = self.service_deployments.get(self.service, [])
        self._restart_deployments(deployments)

        print(f"[SUCCESS] {self.service.upper()} token rotation completed")

    def _rotate_jwt_zero_downtime(self) -> None:
        """
        Rotate JWT secret with zero-downtime strategy.

        This implements a three-phase rotation:
        1. Add new key as secondary (accept both old and new)
        2. Switch to new key as primary (issue with new, accept both)
        3. Remove old key (only new key remains)
        """
        if not self.new_token:
            raise TokenRotationError("New JWT secret is required")

        # Phase 1: Add new key as secondary
        print("[PHASE 1] Adding new JWT secret as secondary key")
        self._backup_current_secret()
        current_secrets = self._get_current_secret()

        current_secrets["JWT_SECRET_KEY_NEW"] = self.new_token
        self._update_secret(current_secrets)
        self._restart_deployments(["uat-backend"])

        print("[PHASE 1] Complete. Both old and new keys are now accepted.")
        print("[ACTION REQUIRED] Monitor logs for 5 minutes, then run Phase 2:")
        print(f"  python3 {sys.argv[0]} --service jwt --token '<same-new-key>' "
              f"--environment {self.environment} --phase 2")

        # For now, stop here and require manual progression
        # In production, you might add automated waiting and health checks

    def _rotate_jwt_standard(self) -> None:
        """Rotate JWT secret with standard strategy (causes session invalidation)."""
        if not self.new_token:
            raise TokenRotationError("New JWT secret is required")

        print("[WARNING] Standard JWT rotation will invalidate all active sessions")
        print("[WARNING] Users will need to re-login")

        if not self.dry_run:
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() != "yes":
                print("Rotation cancelled")
                return

        self._backup_current_secret()
        current_secrets = self._get_current_secret()

        current_secrets["JWT_SECRET_KEY"] = self.new_token
        # Remove any old transition keys
        current_secrets.pop("JWT_SECRET_KEY_NEW", None)
        current_secrets.pop("JWT_SECRET_KEY_OLD", None)

        self._update_secret(current_secrets)
        self._restart_deployments(["uat-backend"])

        print("[SUCCESS] JWT secret rotation completed")
        print("[INFO] All active user sessions have been invalidated")

    def rotate(self) -> None:
        """Execute token rotation for the configured service."""
        print(f"[START] Token rotation for {self.service} in {self.environment}")

        if self.dry_run:
            print("[DRY-RUN] No changes will be applied")

        try:
            if self.service == "jwt":
                if self.zero_downtime:
                    self._rotate_jwt_zero_downtime()
                else:
                    self._rotate_jwt_standard()
            else:
                self._rotate_standard_token()

            # Log rotation
            self._log_rotation()

        except Exception as e:
            print(f"[ERROR] Rotation failed: {e}")
            raise

    def _log_rotation(self) -> None:
        """Log rotation to file for audit trail."""
        log_file = Path("./token_rotation_log.json")

        # Load existing log
        if log_file.exists():
            with open(log_file) as f:
                log_data = json.load(f)
        else:
            log_data = {"rotations": []}

        # Add new entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "service": self.service,
            "environment": self.environment,
            "dry_run": self.dry_run,
            "zero_downtime": self.zero_downtime,
            "status": "completed",
        }

        log_data["rotations"].append(log_entry)

        # Save log
        if not self.dry_run:
            with open(log_file, "w") as f:
                json.dump(log_data, f, indent=2)

            print(f"[INFO] Rotation logged to {log_file}")

    def verify(self) -> bool:
        """
        Verify token rotation was successful.

        Returns:
            True if verification passed, False otherwise
        """
        print(f"[INFO] Verifying {self.service} token rotation")

        # Check all deployments are running
        deployments = self.service_deployments.get(self.service, [])

        for deployment in deployments:
            command = [
                "kubectl",
                "get",
                "deployment",
                deployment,
                "-n",
                self.namespace,
                "-o",
                "jsonpath={.status.readyReplicas}",
            ]

            returncode, stdout, stderr = self._run_command(command)

            if returncode != 0:
                print(f"[ERROR] Failed to check {deployment}: {stderr}")
                return False

            if not self.dry_run:
                ready_replicas = stdout.strip()
                if ready_replicas == "0" or not ready_replicas:
                    print(f"[ERROR] {deployment} has 0 ready replicas")
                    return False

            print(f"[SUCCESS] {deployment} is healthy")

        # Check for recent errors in logs
        print("[INFO] Checking logs for errors...")

        for deployment in deployments:
            command = [
                "kubectl",
                "logs",
                f"deployment/{deployment}",
                "-n",
                self.namespace,
                "--tail=50",
            ]

            returncode, stdout, stderr = self._run_command(command)

            if returncode != 0:
                print(f"[WARNING] Failed to get logs for {deployment}")
                continue

            if not self.dry_run:
                # Check for auth-related errors
                error_keywords = ["401", "403", "unauthorized", "forbidden", "authentication failed"]
                for line in stdout.lower().split("\n"):
                    if any(keyword in line for keyword in error_keywords):
                        print(f"[WARNING] Potential auth error in {deployment}: {line.strip()}")

        print(f"[SUCCESS] Verification completed for {self.service}")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automate token rotation for SDT1 platform services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rotate Jira token in production
  python3 rotate_token.py --service jira --token 'new-token-here' --environment production

  # Rotate JWT secret with zero-downtime
  python3 rotate_token.py --service jwt --token 'new-secret-here' --environment production --zero-downtime

  # Dry run to test rotation process
  python3 rotate_token.py --service openai --token 'new-key-here' --environment staging --dry-run

  # Verify rotation was successful
  python3 rotate_token.py --service github --environment production --verify
        """,
    )

    parser.add_argument(
        "--service",
        required=True,
        choices=TokenRotator.SUPPORTED_SERVICES,
        help="Service to rotate token for",
    )

    parser.add_argument(
        "--environment",
        required=True,
        choices=TokenRotator.SUPPORTED_ENVIRONMENTS,
        help="Target environment",
    )

    parser.add_argument(
        "--token",
        help="New token/credential value (not needed for --verify)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate rotation without applying changes",
    )

    parser.add_argument(
        "--zero-downtime",
        action="store_true",
        help="Use zero-downtime rotation strategy (JWT only)",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify rotation was successful",
    )

    args = parser.parse_args()

    try:
        rotator = TokenRotator(
            service=args.service,
            environment=args.environment,
            new_token=args.token,
            dry_run=args.dry_run,
            zero_downtime=args.zero_downtime,
        )

        if args.verify:
            success = rotator.verify()
            sys.exit(0 if success else 1)
        else:
            rotator.rotate()
            print("\n[INFO] Rotation complete. Run with --verify to check status:")
            print(f"  python3 {sys.argv[0]} --service {args.service} "
                  f"--environment {args.environment} --verify")

    except TokenRotationError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Rotation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
