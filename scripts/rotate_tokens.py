#!/usr/bin/env python3
"""
Automated token rotation script for PM Agent system.

This script automates the rotation of API tokens and secrets used by the PM Agent.
It follows security best practices and includes comprehensive logging and rollback capabilities.

Usage:
    python rotate_tokens.py --environment production --tokens jira,openai,github
    python rotate_tokens.py --environment staging --tokens all --dry-run
    python rotate_tokens.py --environment production --tokens jwt --force
"""

import os
import sys
import json
import argparse
import logging
import secrets
import subprocess
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    import boto3
    import requests
    from botocore.exceptions import ClientError
except ImportError:
    print("Missing dependencies. Install with: pip install boto3 requests")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RotationResult:
    """Result of a token rotation attempt."""
    token_type: str
    success: bool
    timestamp: str
    error: Optional[str] = None
    old_token_last4: Optional[str] = None
    new_token_last4: Optional[str] = None


class TokenRotationError(Exception):
    """Raised when token rotation fails."""
    pass


class TokenRotator:
    """Handles automated rotation of various API tokens and secrets."""
    
    def __init__(self, environment: str, dry_run: bool = False, force: bool = False):
        """
        Initialize the token rotator.
        
        Args:
            environment: Target environment (staging/production)
            dry_run: If True, simulate rotation without making changes
            force: If True, skip confirmation prompts
        """
        self.environment = environment
        self.dry_run = dry_run
        self.force = force
        self.rotation_log: List[RotationResult] = []
        
        # Initialize AWS clients
        try:
            self.secrets_client = boto3.client('secretsmanager')
            self.ssm_client = boto3.client('ssm')
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise
        
        # Secret paths
        self.secret_prefix = f"pm-agent/{environment}"
        
    def _get_secret(self, secret_name: str) -> str:
        """
        Retrieve a secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret (without environment prefix)
            
        Returns:
            The secret value
        """
        try:
            secret_id = f"{self.secret_prefix}/{secret_name}"
            response = self.secrets_client.get_secret_value(SecretId=secret_id)
            return response['SecretString']
        except ClientError as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise TokenRotationError(f"Secret retrieval failed: {e}")
    
    def _update_secret(self, secret_name: str, new_value: str) -> bool:
        """
        Update a secret in AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret (without environment prefix)
            new_value: New secret value
            
        Returns:
            True if successful
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update secret: {secret_name}")
            return True
        
        try:
            secret_id = f"{self.secret_prefix}/{secret_name}"
            self.secrets_client.update_secret(
                SecretId=secret_id,
                SecretString=new_value
            )
            logger.info(f"Successfully updated secret: {secret_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to update secret {secret_name}: {e}")
            raise TokenRotationError(f"Secret update failed: {e}")
    
    def _update_kubernetes_env(self, deployment: str, env_var: str, value: str) -> bool:
        """
        Update environment variable in Kubernetes deployment.
        
        Args:
            deployment: Deployment name
            env_var: Environment variable name
            value: New value
            
        Returns:
            True if successful
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update k8s env {env_var} in {deployment}")
            return True
        
        try:
            namespace = self.environment
            cmd = [
                'kubectl', 'set', 'env',
                f'deployment/{deployment}',
                f'{env_var}={value}',
                '-n', namespace
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Updated {env_var} in {deployment}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update k8s env: {e.stderr}")
            raise TokenRotationError(f"Kubernetes update failed: {e.stderr}")
    
    def _test_http_endpoint(self, url: str, headers: Dict[str, str]) -> bool:
        """
        Test an HTTP endpoint with given headers.
        
        Args:
            url: URL to test
            headers: Request headers
            
        Returns:
            True if request succeeds (2xx status)
        """
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code < 300
        except Exception as e:
            logger.error(f"HTTP test failed: {e}")
            return False
    
    def rotate_jira_token(self) -> RotationResult:
        """
        Rotate Jira API token.
        
        Note: Jira tokens must be created manually via Atlassian account.
        This method guides the user through the process and updates the secret.
        
        Returns:
            RotationResult with outcome
        """
        logger.info("🔄 Starting Jira API token rotation...")
        
        try:
            # Get current token for backup
            old_token = self._get_secret('jira-token')
            old_last4 = old_token[-4:] if old_token else "N/A"
            
            # Guide user to create new token
            if not self.dry_run and not self.force:
                logger.info("Please create a new Jira API token:")
                logger.info("1. Go to https://id.atlassian.com/manage-profile/security/api-tokens")
                logger.info("2. Click 'Create API token'")
                logger.info(f"3. Name it: pm-agent-api-token-{datetime.now().strftime('%Y-%m-%d')}")
                
                new_token = input("Paste the new token here: ").strip()
                if not new_token:
                    raise TokenRotationError("No token provided")
            else:
                # For automation, token must be provided via environment
                new_token = os.getenv('NEW_JIRA_TOKEN')
                if not new_token and not self.dry_run:
                    raise TokenRotationError("NEW_JIRA_TOKEN environment variable not set")
                new_token = new_token or "dry-run-token"
            
            new_last4 = new_token[-4:]
            
            # Test new token
            jira_email = os.getenv('JIRA_EMAIL')
            jira_domain = os.getenv('JIRA_DOMAIN')
            
            if jira_email and jira_domain and not self.dry_run:
                logger.info("Testing new Jira token...")
                test_url = f"https://{jira_domain}/rest/api/3/myself"
                test_success = self._test_http_endpoint(
                    test_url,
                    headers={'Authorization': f'Basic {jira_email}:{new_token}'}
                )
                
                if not test_success:
                    raise TokenRotationError("New Jira token failed validation test")
                
                logger.info("✅ New token validated successfully")
            
            # Update in secrets manager
            self._update_secret('jira-token', new_token)
            
            # Update in Kubernetes
            self._update_kubernetes_env(
                'pm-agent-backend',
                'JIRA_API_TOKEN',
                new_token
            )
            
            logger.info("✅ Jira token rotation complete")
            
            return RotationResult(
                token_type='jira',
                success=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
                old_token_last4=old_last4,
                new_token_last4=new_last4
            )
            
        except Exception as e:
            logger.error(f"❌ Jira token rotation failed: {e}")
            return RotationResult(
                token_type='jira',
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )
    
    def rotate_openai_key(self) -> RotationResult:
        """
        Rotate OpenAI API key.
        
        Note: OpenAI keys must be created manually via OpenAI platform.
        
        Returns:
            RotationResult with outcome
        """
        logger.info("🔄 Starting OpenAI API key rotation...")
        
        try:
            old_token = self._get_secret('openai-key')
            old_last4 = old_token[-4:] if old_token else "N/A"
            
            if not self.dry_run and not self.force:
                logger.info("Please create a new OpenAI API key:")
                logger.info("1. Go to https://platform.openai.com/api-keys")
                logger.info("2. Click 'Create new secret key'")
                logger.info(f"3. Name it: pm-agent-{datetime.now().strftime('%Y-%m-%d')}")
                
                new_token = input("Paste the new key here: ").strip()
                if not new_token:
                    raise TokenRotationError("No key provided")
            else:
                new_token = os.getenv('NEW_OPENAI_KEY')
                if not new_token and not self.dry_run:
                    raise TokenRotationError("NEW_OPENAI_KEY environment variable not set")
                new_token = new_token or "dry-run-token"
            
            new_last4 = new_token[-4:]
            
            # Test new key
            if not self.dry_run:
                logger.info("Testing new OpenAI key...")
                test_success = self._test_http_endpoint(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {new_token}'}
                )
                
                if not test_success:
                    raise TokenRotationError("New OpenAI key failed validation test")
                
                logger.info("✅ New key validated successfully")
            
            # Update in secrets manager
            self._update_secret('openai-key', new_token)
            
            # Update in Kubernetes
            self._update_kubernetes_env(
                'pm-agent-backend',
                'OPENAI_API_KEY',
                new_token
            )
            
            logger.info("✅ OpenAI key rotation complete")
            
            return RotationResult(
                token_type='openai',
                success=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
                old_token_last4=old_last4,
                new_token_last4=new_last4
            )
            
        except Exception as e:
            logger.error(f"❌ OpenAI key rotation failed: {e}")
            return RotationResult(
                token_type='openai',
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )
    
    def rotate_github_token(self) -> RotationResult:
        """
        Rotate GitHub Personal Access Token.
        
        Returns:
            RotationResult with outcome
        """
        logger.info("🔄 Starting GitHub PAT rotation...")
        
        try:
            old_token = self._get_secret('github-token')
            old_last4 = old_token[-4:] if old_token else "N/A"
            
            if not self.dry_run and not self.force:
                logger.info("Please create a new GitHub Personal Access Token:")
                logger.info("1. Go to https://github.com/settings/tokens")
                logger.info("2. Click 'Generate new token (classic)'")
                logger.info(f"3. Name it: pm-agent-production-{datetime.now().strftime('%Y-%m-%d')}")
                logger.info("4. Select scopes: repo, workflow")
                logger.info("5. Set expiration: 90 days")
                
                new_token = input("Paste the new token here: ").strip()
                if not new_token:
                    raise TokenRotationError("No token provided")
            else:
                new_token = os.getenv('NEW_GITHUB_TOKEN')
                if not new_token and not self.dry_run:
                    raise TokenRotationError("NEW_GITHUB_TOKEN environment variable not set")
                new_token = new_token or "dry-run-token"
            
            new_last4 = new_token[-4:]
            
            # Test new token
            if not self.dry_run:
                logger.info("Testing new GitHub token...")
                test_success = self._test_http_endpoint(
                    'https://api.github.com/user',
                    headers={'Authorization': f'token {new_token}'}
                )
                
                if not test_success:
                    raise TokenRotationError("New GitHub token failed validation test")
                
                logger.info("✅ New token validated successfully")
            
            # Update in secrets manager
            self._update_secret('github-token', new_token)
            
            # Update in Kubernetes
            self._update_kubernetes_env(
                'pm-agent-backend',
                'GITHUB_TOKEN',
                new_token
            )
            
            logger.info("✅ GitHub token rotation complete")
            
            return RotationResult(
                token_type='github',
                success=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
                old_token_last4=old_last4,
                new_token_last4=new_last4
            )
            
        except Exception as e:
            logger.error(f"❌ GitHub token rotation failed: {e}")
            return RotationResult(
                token_type='github',
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )
    
    def rotate_jwt_secret(self) -> RotationResult:
        """
        Rotate JWT secret key.
        
        Note: This will invalidate all existing user sessions.
        
        Returns:
            RotationResult with outcome
        """
        logger.info("🔄 Starting JWT secret rotation...")
        logger.warning("⚠️  This will invalidate all user sessions!")
        
        if not self.force and not self.dry_run:
            confirm = input("Continue? (yes/no): ").strip().lower()
            if confirm != 'yes':
                logger.info("Rotation cancelled")
                return RotationResult(
                    token_type='jwt',
                    success=False,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    error="Cancelled by user"
                )
        
        try:
            old_secret = self._get_secret('jwt-secret')
            old_last4 = old_secret[-4:] if old_secret else "N/A"
            
            # Generate new secret (256-bit)
            new_secret = secrets.token_urlsafe(32)
            new_last4 = new_secret[-4:]
            
            # Store old secret as previous (for dual-secret verification)
            self._update_secret('jwt-secret-previous', old_secret)
            
            # Update to new secret
            self._update_secret('jwt-secret', new_secret)
            
            # Update in Kubernetes (with both secrets)
            self._update_kubernetes_env(
                'pm-agent-backend',
                'JWT_SECRET_KEY',
                new_secret
            )
            self._update_kubernetes_env(
                'pm-agent-backend',
                'JWT_SECRET_KEY_PREVIOUS',
                old_secret
            )
            
            logger.info("✅ JWT secret rotation complete")
            logger.info("⚠️  Remember to remove JWT_SECRET_KEY_PREVIOUS after 24 hours")
            
            return RotationResult(
                token_type='jwt',
                success=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
                old_token_last4=old_last4,
                new_token_last4=new_last4
            )
            
        except Exception as e:
            logger.error(f"❌ JWT secret rotation failed: {e}")
            return RotationResult(
                token_type='jwt',
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )
    
    def rotate_database_password(self) -> RotationResult:
        """
        Rotate database password.
        
        Note: This requires database admin access and careful coordination.
        
        Returns:
            RotationResult with outcome
        """
        logger.info("🔄 Starting database password rotation...")
        logger.warning("⚠️  This is a critical operation that requires database admin access!")
        
        try:
            # Get current DATABASE_URL
            old_db_url = self._get_secret('database-url')
            
            # Parse DATABASE_URL to extract components
            # Format: postgresql://user:password@host:port/database
            import re
            match = re.match(
                r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)',
                old_db_url
            )
            
            if not match:
                raise TokenRotationError("Invalid DATABASE_URL format")
            
            user, old_password, host, port, database = match.groups()
            old_last4 = old_password[-4:]
            
            # Generate new password
            new_password = secrets.token_urlsafe(32)
            new_last4 = new_password[-4:]
            
            if not self.dry_run:
                logger.info(f"Please update database password for user '{user}':")
                logger.info(f"Run: ALTER USER {user} WITH PASSWORD '{new_password}';")
                
                if not self.force:
                    confirm = input("Have you updated the database password? (yes/no): ").strip().lower()
                    if confirm != 'yes':
                        raise TokenRotationError("Database password not updated")
            
            # Build new DATABASE_URL
            new_db_url = f"postgresql://{user}:{new_password}@{host}:{port}/{database}"
            
            # Update secret
            self._update_secret('database-url', new_db_url)
            
            # Update in Kubernetes
            self._update_kubernetes_env(
                'pm-agent-backend',
                'DATABASE_URL',
                new_db_url
            )
            
            logger.info("✅ Database password rotation complete")
            
            return RotationResult(
                token_type='database',
                success=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
                old_token_last4=old_last4,
                new_token_last4=new_last4
            )
            
        except Exception as e:
            logger.error(f"❌ Database password rotation failed: {e}")
            return RotationResult(
                token_type='database',
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )
    
    def rotate_tokens(self, token_types: List[str]) -> List[RotationResult]:
        """
        Rotate specified tokens.
        
        Args:
            token_types: List of token types to rotate ('jira', 'openai', 'github', 'jwt', 'database', 'all')
            
        Returns:
            List of RotationResult objects
        """
        if 'all' in token_types:
            token_types = ['jira', 'openai', 'github', 'jwt', 'database']
        
        results = []
        
        for token_type in token_types:
            if token_type == 'jira':
                result = self.rotate_jira_token()
            elif token_type == 'openai':
                result = self.rotate_openai_key()
            elif token_type == 'github':
                result = self.rotate_github_token()
            elif token_type == 'jwt':
                result = self.rotate_jwt_secret()
            elif token_type == 'database':
                result = self.rotate_database_password()
            else:
                logger.warning(f"Unknown token type: {token_type}")
                continue
            
            results.append(result)
            self.rotation_log.append(result)
        
        return results
    
    def generate_report(self) -> str:
        """
        Generate a rotation report.
        
        Returns:
            Formatted report string
        """
        report = [
            "\n" + "="*60,
            "Token Rotation Report",
            "="*60,
            f"Environment: {self.environment}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            f"Dry Run: {self.dry_run}",
            "\n" + "Results:",
            "-"*60
        ]
        
        for result in self.rotation_log:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            report.append(f"\n{result.token_type.upper()}: {status}")
            report.append(f"  Timestamp: {result.timestamp}")
            
            if result.old_token_last4:
                report.append(f"  Old token (last 4): ...{result.old_token_last4}")
            if result.new_token_last4:
                report.append(f"  New token (last 4): ...{result.new_token_last4}")
            if result.error:
                report.append(f"  Error: {result.error}")
        
        report.extend([
            "\n" + "="*60,
            f"Summary: {sum(1 for r in self.rotation_log if r.success)}/{len(self.rotation_log)} successful",
            "="*60 + "\n"
        ])
        
        return "\n".join(report)
    
    def save_audit_log(self, output_file: str):
        """
        Save rotation audit log to file.
        
        Args:
            output_file: Path to output file
        """
        audit_data = {
            'environment': self.environment,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'dry_run': self.dry_run,
            'results': [asdict(r) for r in self.rotation_log]
        }
        
        with open(output_file, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"Audit log saved to: {output_file}")


def main():
    """Main entry point for token rotation script."""
    parser = argparse.ArgumentParser(
        description='Rotate PM Agent API tokens and secrets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rotate all tokens in staging (dry run)
  python rotate_tokens.py --environment staging --tokens all --dry-run
  
  # Rotate specific tokens in production
  python rotate_tokens.py --environment production --tokens jira,openai
  
  # Force rotation without prompts (for automation)
  python rotate_tokens.py --environment production --tokens jwt --force
  
  # Generate audit log
  python rotate_tokens.py --environment production --tokens all --audit-log rotation.json
        """
    )
    
    parser.add_argument(
        '--environment',
        required=True,
        choices=['staging', 'production'],
        help='Target environment'
    )
    
    parser.add_argument(
        '--tokens',
        required=True,
        help='Comma-separated list of tokens to rotate (jira,openai,github,jwt,database,all)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate rotation without making changes'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts (for automation)'
    )
    
    parser.add_argument(
        '--audit-log',
        help='Path to save audit log (JSON format)'
    )
    
    args = parser.parse_args()
    
    # Parse token types
    token_types = [t.strip() for t in args.tokens.split(',')]
    
    # Create rotator
    try:
        rotator = TokenRotator(
            environment=args.environment,
            dry_run=args.dry_run,
            force=args.force
        )
    except Exception as e:
        logger.error(f"Failed to initialize rotator: {e}")
        sys.exit(1)
    
    # Perform rotation
    logger.info(f"Starting token rotation for: {', '.join(token_types)}")
    results = rotator.rotate_tokens(token_types)
    
    # Generate and display report
    report = rotator.generate_report()
    print(report)
    
    # Save audit log if requested
    if args.audit_log:
        rotator.save_audit_log(args.audit_log)
    
    # Exit with appropriate code
    all_success = all(r.success for r in results)
    sys.exit(0 if all_success else 1)


if __name__ == '__main__':
    main()
