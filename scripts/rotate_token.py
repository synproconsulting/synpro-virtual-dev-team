#!/usr/bin/env python3
"""
scripts/rotate_token.py
=======================
Automated token rotation script with safety checks and rollback support.

Usage:
    ./scripts/rotate_token.py --env production --token-type jwt --dry-run
    ./scripts/rotate_token.py --env production --token-type jwt --execute
    ./scripts/rotate_token.py --env production --token-type jwt --rollback
    ./scripts/rotate_token.py --env production --token-type database --emergency

Author: DevOps Team
Created: 2024-01-XX
Ticket: SDT1-70
"""

import argparse
import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from uat.backend.config import generate_jwt_secret
except ImportError:
    # Fallback if backend not available
    import secrets
    def generate_jwt_secret(length: int = 64) -> str:
        import base64
        return base64.b64encode(secrets.token_bytes(length)).decode('utf-8')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/rotation-{datetime.now().strftime("%Y%m%d-%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class TokenRotationError(Exception):
    """Raised when token rotation fails."""
    pass


class TokenRotator:
    """Handles token rotation for various credential types."""
    
    SUPPORTED_TYPES = ['jwt', 'database', 'railway', 'smtp', 'jira']
    
    def __init__(self, env: str, token_type: str, dry_run: bool = False):
        """
        Initialize token rotator.
        
        Args:
            env: Environment (development, staging, production)
            token_type: Type of token to rotate
            dry_run: If True, simulate rotation without making changes
        """
        self.env = env
        self.token_type = token_type
        self.dry_run = dry_run
        self.backup: Dict[str, str] = {}
        
        if token_type not in self.SUPPORTED_TYPES:
            raise TokenRotationError(
                f"Unsupported token type: {token_type}. "
                f"Supported types: {', '.join(self.SUPPORTED_TYPES)}"
            )
        
        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
        
        logger.info(f"Initialized TokenRotator for {token_type} in {env} environment")
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
    
    def check_prerequisites(self) -> Tuple[bool, List[str]]:
        """
        Check if all prerequisites for rotation are met.
        
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        # Check environment
        if self.env not in ['development', 'staging', 'production']:
            errors.append(f"Invalid environment: {self.env}")
        
        # Check railway CLI is installed
        try:
            result = subprocess.run(
                ['railway', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                errors.append("Railway CLI not installed or not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append("Railway CLI not found. Install with: npm install -g @railway/cli")
        
        # Check token-specific prerequisites
        if self.token_type == 'database':
            # Check psql is available
            try:
                result = subprocess.run(
                    ['psql', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    errors.append("psql client not installed")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                errors.append("psql client not found. Install PostgreSQL client tools.")
        
        # Check backup directory exists
        backup_dir = Path('backups/secrets')
        if not backup_dir.exists():
            try:
                backup_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created backup directory: {backup_dir}")
            except Exception as e:
                errors.append(f"Cannot create backup directory: {e}")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False, errors
        
        logger.info("✓ All prerequisites met")
        return True, []
    
    def backup_current_token(self) -> None:
        """Backup current token value before rotation."""
        logger.info("Backing up current token...")
        
        try:
            # Get current value from Railway
            result = subprocess.run(
                ['railway', 'variables', '--env', self.env, '--json'],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            variables = json.loads(result.stdout)
            token_var = self._get_token_variable_name()
            
            if token_var in variables:
                self.backup[token_var] = variables[token_var]
                
                # Save to file
                backup_file = Path('backups/secrets') / f'{self.token_type}_{self.env}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(backup_file, 'w') as f:
                    json.dump({
                        'token_type': self.token_type,
                        'env': self.env,
                        'timestamp': datetime.now().isoformat(),
                        'variables': {token_var: variables[token_var]}
                    }, f, indent=2)
                
                logger.info(f"✓ Backup saved to {backup_file}")
            else:
                logger.warning(f"Token variable {token_var} not found in environment")
        
        except subprocess.CalledProcessError as e:
            raise TokenRotationError(f"Failed to backup current token: {e.stderr}")
        except Exception as e:
            raise TokenRotationError(f"Failed to backup current token: {e}")
    
    def generate_new_token(self) -> str:
        """
        Generate a new token based on type.
        
        Returns:
            New token value
        """
        logger.info(f"Generating new {self.token_type} token...")
        
        if self.token_type == 'jwt':
            token = generate_jwt_secret()
            logger.info(f"✓ Generated JWT secret ({len(token)} characters)")
            return token
        
        elif self.token_type == 'database':
            # Generate secure database password
            import secrets
            import string
            chars = string.ascii_letters + string.digits + '!@#$%^&*()-_=+[]{}|;:,.<>?'
            password = ''.join(secrets.choice(chars) for _ in range(32))
            logger.info("✓ Generated database password (32 characters)")
            return password
        
        elif self.token_type in ['railway', 'smtp', 'jira']:
            logger.warning(
                f"⚠️  {self.token_type.upper()} tokens must be generated manually through the provider's web interface."
            )
            token = input(f"Enter the new {self.token_type.upper()} token: ").strip()
            if not token:
                raise TokenRotationError("No token provided")
            return token
        
        else:
            raise TokenRotationError(f"Unsupported token type: {self.token_type}")
    
    def update_environment_variable(self, new_token: str) -> None:
        """
        Update environment variable with new token.
        
        Args:
            new_token: New token value
        """
        token_var = self._get_token_variable_name()
        logger.info(f"Updating environment variable {token_var}...")
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update {token_var} in {self.env} environment")
            return
        
        try:
            # Update Railway environment variable
            subprocess.run(
                ['railway', 'variables', 'set', f'{token_var}={new_token}', '--env', self.env],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            logger.info(f"✓ Updated {token_var} in {self.env} environment")
        
        except subprocess.CalledProcessError as e:
            raise TokenRotationError(f"Failed to update environment variable: {e.stderr}")
    
    def restart_services(self, zero_downtime: bool = False) -> None:
        """
        Restart services to pick up new token.
        
        Args:
            zero_downtime: If True, perform rolling restart
        """
        logger.info("Restarting services...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would restart services")
            return
        
        try:
            if zero_downtime:
                logger.info("Performing rolling restart for zero-downtime deployment...")
                # Railway handles rolling restarts automatically
                subprocess.run(
                    ['railway', 'up', '--env', self.env, '--detach'],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=True
                )
            else:
                # Simple restart
                subprocess.run(
                    ['railway', 'up', '--env', self.env, '--restart'],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=True
                )
            
            logger.info("✓ Services restarted successfully")
            
            # Wait for services to be healthy
            logger.info("Waiting for services to become healthy...")
            time.sleep(10)
        
        except subprocess.CalledProcessError as e:
            raise TokenRotationError(f"Failed to restart services: {e.stderr}")
    
    def validate_rotation(self) -> bool:
        """
        Validate that rotation was successful.
        
        Returns:
            True if validation passed
        """
        logger.info("Validating rotation...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would validate rotation")
            return True
        
        try:
            # Check health endpoint
            import requests
            
            health_url = self._get_health_url()
            if health_url:
                response = requests.get(health_url, timeout=10)
                if response.status_code == 200:
                    logger.info("✓ Health check passed")
                else:
                    logger.error(f"✗ Health check failed: {response.status_code}")
                    return False
            
            # Token-specific validation
            if self.token_type == 'jwt':
                # Try to generate a test token
                logger.info("Testing JWT token generation...")
                # This would require importing and testing the actual auth system
                logger.info("✓ JWT validation skipped (requires manual testing)")
            
            elif self.token_type == 'database':
                # Try to connect to database
                logger.info("Testing database connection...")
                result = subprocess.run(
                    ['railway', 'run', '--env', self.env, 'psql', '$DATABASE_URL', '-c', 'SELECT 1;'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    logger.info("✓ Database connection successful")
                else:
                    logger.error(f"✗ Database connection failed: {result.stderr}")
                    return False
            
            logger.info("✓ Rotation validation passed")
            return True
        
        except Exception as e:
            logger.error(f"✗ Validation failed: {e}")
            return False
    
    def rollback(self) -> None:
        """Rollback to previous token value."""
        logger.info("Rolling back to previous token...")
        
        if not self.backup:
            logger.error("No backup available for rollback")
            
            # Try to load from most recent backup file
            backup_dir = Path('backups/secrets')
            backup_files = sorted(
                backup_dir.glob(f'{self.token_type}_{self.env}_*.json'),
                reverse=True
            )
            
            if backup_files:
                logger.info(f"Loading backup from {backup_files[0]}")
                with open(backup_files[0], 'r') as f:
                    backup_data = json.load(f)
                    self.backup = backup_data['variables']
            else:
                raise TokenRotationError("No backup available for rollback")
        
        token_var = self._get_token_variable_name()
        old_token = self.backup.get(token_var)
        
        if not old_token:
            raise TokenRotationError(f"No backup found for {token_var}")
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would rollback {token_var}")
            return
        
        try:
            # Restore old token
            subprocess.run(
                ['railway', 'variables', 'set', f'{token_var}={old_token}', '--env', self.env],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            logger.info(f"✓ Rolled back {token_var}")
            
            # Restart services
            self.restart_services()
            
            logger.info("✓ Rollback completed successfully")
        
        except subprocess.CalledProcessError as e:
            raise TokenRotationError(f"Failed to rollback: {e.stderr}")
    
    def _get_token_variable_name(self) -> str:
        """Get environment variable name for token type."""
        mapping = {
            'jwt': 'JWT_SECRET',
            'database': 'DATABASE_URL',
            'railway': 'RAILWAY_API_TOKEN',
            'smtp': 'SMTP_PASSWORD',
            'jira': 'JIRA_API_TOKEN'
        }
        return mapping.get(self.token_type, self.token_type.upper() + '_TOKEN')
    
    def _get_health_url(self) -> Optional[str]:
        """Get health check URL for environment."""
        urls = {
            'production': 'https://api.yourapp.com/health',
            'staging': 'https://staging-api.yourapp.com/health',
            'development': 'http://localhost:8000/health'
        }
        return urls.get(self.env)


def main():
    """Main entry point for token rotation script."""
    parser = argparse.ArgumentParser(
        description='Rotate tokens and secrets with safety checks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (recommended first)
  %(prog)s --env production --token-type jwt --dry-run
  
  # Execute rotation
  %(prog)s --env production --token-type jwt --execute
  
  # Execute with zero-downtime
  %(prog)s --env production --token-type jwt --execute --zero-downtime
  
  # Emergency rotation (skips some safety checks)
  %(prog)s --env production --token-type jwt --emergency
  
  # Rollback to previous token
  %(prog)s --env production --token-type jwt --rollback
  
  # Check prerequisites only
  %(prog)s --env production --token-type jwt --check-prerequisites
        """
    )
    
    parser.add_argument(
        '--env',
        required=True,
        choices=['development', 'staging', 'production'],
        help='Target environment'
    )
    
    parser.add_argument(
        '--token-type',
        required=True,
        choices=TokenRotator.SUPPORTED_TYPES,
        help='Type of token to rotate'
    )
    
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate rotation without making changes'
    )
    action_group.add_argument(
        '--execute',
        action='store_true',
        help='Execute the rotation'
    )
    action_group.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback to previous token'
    )
    action_group.add_argument(
        '--emergency',
        action='store_true',
        help='Emergency rotation (bypasses some checks)'
    )
    action_group.add_argument(
        '--check-prerequisites',
        action='store_true',
        help='Check prerequisites only'
    )
    
    parser.add_argument(
        '--zero-downtime',
        action='store_true',
        help='Perform zero-downtime rolling restart'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation after rotation'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize rotator
        rotator = TokenRotator(
            env=args.env,
            token_type=args.token_type,
            dry_run=args.dry_run
        )
        
        # Check prerequisites
        logger.info("=" * 60)
        logger.info(f"Token Rotation: {args.token_type.upper()} in {args.env.upper()}")
        logger.info("=" * 60)
        
        success, errors = rotator.check_prerequisites()
        if not success:
            logger.error("Prerequisites check failed!")
            sys.exit(1)
        
        if args.check_prerequisites:
            logger.info("✓ Prerequisites check completed successfully")
            sys.exit(0)
        
        # Handle rollback
        if args.rollback:
            if args.env == 'production':
                confirm = input("⚠️  Rollback in PRODUCTION environment. Are you sure? (yes/no): ")
                if confirm.lower() != 'yes':
                    logger.info("Rollback cancelled")
                    sys.exit(0)
            
            rotator.rollback()
            sys.exit(0)
        
        # Confirm production rotation
        if args.env == 'production' and (args.execute or args.emergency) and not args.dry_run:
            logger.warning("⚠️  WARNING: You are about to rotate tokens in PRODUCTION!")
            logger.warning(f"Token type: {args.token_type}")
            logger.warning(f"Environment: {args.env}")
            logger.warning("")
            confirm = input("Type 'ROTATE' to confirm: ")
            if confirm != 'ROTATE':
                logger.info("Rotation cancelled")
                sys.exit(0)
        
        # Execute rotation
        logger.info("\nStarting rotation process...")
        
        # Step 1: Backup
        rotator.backup_current_token()
        
        # Step 2: Generate new token
        new_token = rotator.generate_new_token()
        
        # Step 3: Update environment variable
        rotator.update_environment_variable(new_token)
        
        # Step 4: Restart services
        rotator.restart_services(zero_downtime=args.zero_downtime)
        
        # Step 5: Validate (if requested or in emergency mode)
        if args.validate or args.emergency:
            if not rotator.validate_rotation():
                logger.error("✗ Validation failed!")
                logger.error("Consider running rollback: --rollback")
                sys.exit(1)
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Token rotation completed successfully!")
        logger.info("=" * 60)
        logger.info(f"\nNext steps:")
        logger.info(f"1. Monitor application logs for errors")
        logger.info(f"2. Test critical functionality")
        logger.info(f"3. Update rotation schedule in runbook")
        logger.info(f"4. Archive old token securely")
        
        if not args.validate:
            logger.info("\nNote: Validation was not run. Use --validate flag to run validation checks.")
    
    except TokenRotationError as e:
        logger.error(f"✗ Token rotation failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Rotation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
