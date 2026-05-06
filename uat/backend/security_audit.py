#!/usr/bin/env python3
"""
security_audit.py
═════════════════
Security audit script for SynPro Virtual Dev Team backend configuration.
Validates CORS, JWT, and other security settings.

Usage:
    python security_audit.py
    
Exit codes:
    0 - All checks passed
    1 - Security issues found

Related tickets: SDT1-56 (CORS), SDT1-63 (JWT)
"""

import os
import sys
import logging
from typing import List, Tuple
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


class SecurityAudit:
    """Security audit checker for backend configuration."""
    
    def __init__(self):
        self.issues: List[Tuple[str, str]] = []  # (severity, message)
        self.warnings: List[str] = []
        self.passed: List[str] = []
    
    def check_cors_config(self) -> None:
        """Check CORS configuration security."""
        logger.info("\n" + "="*80)
        logger.info("CORS Configuration Audit (SDT1-56)")
        logger.info("="*80)
        
        environment = os.environ.get("ENVIRONMENT", "production").lower()
        frontend_url = os.environ.get("FRONTEND_URL", "").strip()
        allow_wildcard = os.environ.get("ALLOW_CORS_WILDCARD", "false").lower() == "true"
        
        # Check environment
        if environment not in ["development", "production", "staging"]:
            self.warnings.append(
                f"ENVIRONMENT is set to '{environment}' - should be 'development' or 'production'"
            )
        
        # Check FRONTEND_URL is set
        if not frontend_url:
            if environment == "production":
                self.issues.append((
                    "CRITICAL",
                    "FRONTEND_URL is not set in production environment"
                ))
            else:
                self.warnings.append(
                    "FRONTEND_URL is not set - will default to http://localhost:3000"
                )
        else:
            # Parse origins
            origins = [o.strip() for o in frontend_url.split(",") if o.strip()]
            
            # Check wildcard
            if "*" in origins:
                if environment == "production" and not allow_wildcard:
                    self.issues.append((
                        "CRITICAL",
                        "CORS wildcard '*' used in production without ALLOW_CORS_WILDCARD=true"
                    ))
                elif environment == "production":
                    self.issues.append((
                        "HIGH",
                        "CORS wildcard '*' is enabled in production - allows requests from ANY origin"
                    ))
                else:
                    self.warnings.append(
                        "CORS wildcard '*' is enabled - should only be used in development"
                    )
                
                if len(origins) > 1:
                    self.issues.append((
                        "HIGH",
                        f"CORS wildcard mixed with specific origins: {origins}"
                    ))
            else:
                # Validate each origin
                for origin in origins:
                    self._validate_origin(origin, environment)
                
                self.passed.append(
                    f"CORS configured with {len(origins)} specific origin(s)"
                )
        
        # Check credentials with wildcard
        if "*" in frontend_url and allow_wildcard:
            self.warnings.append(
                "CORS credentials are enabled with wildcard origin - "
                "this may not work in all browsers"
            )
    
    def _validate_origin(self, origin: str, environment: str) -> None:
        """Validate a single origin URL."""
        try:
            parsed = urlparse(origin)
            
            # Check scheme
            if not parsed.scheme:
                self.issues.append((
                    "HIGH",
                    f"Origin missing protocol: {origin}"
                ))
                return
            
            if parsed.scheme not in ["http", "https"]:
                self.issues.append((
                    "HIGH",
                    f"Origin has invalid protocol '{parsed.scheme}': {origin}"
                ))
                return
            
            # Check HTTP vs HTTPS
            if parsed.scheme == "http":
                if environment == "production":
                    # Allow localhost/127.0.0.1 for testing
                    if parsed.hostname not in ["localhost", "127.0.0.1", "::1"]:
                        self.issues.append((
                            "MEDIUM",
                            f"Production origin uses HTTP (not HTTPS): {origin}"
                        ))
                else:
                    self.warnings.append(
                        f"Origin uses HTTP: {origin} (OK for development)"
                    )
            
            # Check for suspicious patterns
            if parsed.fragment or parsed.query:
                self.warnings.append(
                    f"Origin contains fragment or query string: {origin}"
                )
            
            if parsed.path and parsed.path != "/":
                self.warnings.append(
                    f"Origin contains path: {origin} (unusual but valid)"
                )
            
        except Exception as e:
            self.issues.append((
                "HIGH",
                f"Failed to parse origin '{origin}': {e}"
            ))
    
    def check_jwt_config(self) -> None:
        """Check JWT configuration security."""
        logger.info("\n" + "="*80)
        logger.info("JWT Configuration Audit (SDT1-63)")
        logger.info("="*80)
        
        environment = os.environ.get("ENVIRONMENT", "production").lower()
        jwt_secret = os.environ.get("JWT_SECRET", "").strip()
        allow_weak = os.environ.get("ALLOW_WEAK_JWT_SECRET", "false").lower() == "true"
        expiry_str = os.environ.get("JWT_EXPIRY_HOURS", "24").strip()
        
        # Check JWT_SECRET is set
        if not jwt_secret:
            if environment == "production":
                self.issues.append((
                    "CRITICAL",
                    "JWT_SECRET is not set in production environment"
                ))
            else:
                self.warnings.append(
                    "JWT_SECRET is not set - will use auto-generated temporary secret"
                )
        else:
            # Check secret strength
            weak_secrets = {
                "secret", "dev-secret", "dev-secret-change-in-production",
                "change-me", "changeme", "test", "testing", "development",
                "dev", "password", "123456", "admin", "default", "example",
                "sample", "your-secret-key", "your-jwt-secret", "jwt-secret-key",
            }
            
            if jwt_secret.lower() in weak_secrets:
                if environment == "production":
                    self.issues.append((
                        "CRITICAL",
                        f"JWT_SECRET is a known weak secret: '{jwt_secret}'"
                    ))
                elif not allow_weak:
                    self.issues.append((
                        "HIGH",
                        f"JWT_SECRET is a known weak secret: '{jwt_secret}'"
                    ))
                else:
                    self.warnings.append(
                        f"JWT_SECRET is weak but allowed in development: '{jwt_secret}'"
                    )
            
            # Check length
            if len(jwt_secret) < 32:
                if environment == "production":
                    self.issues.append((
                        "CRITICAL",
                        f"JWT_SECRET is too short ({len(jwt_secret)} chars, minimum 32 recommended)"
                    ))
                elif not allow_weak:
                    self.issues.append((
                        "HIGH",
                        f"JWT_SECRET is too short ({len(jwt_secret)} chars, minimum 32 recommended)"
                    ))
                else:
                    self.warnings.append(
                        f"JWT_SECRET is short ({len(jwt_secret)} chars) but allowed in development"
                    )
            else:
                self.passed.append(
                    f"JWT_SECRET length is adequate ({len(jwt_secret)} characters)"
                )
            
            # Check for default/placeholder patterns
            if any(word in jwt_secret.lower() for word in ["change", "default", "example", "replace"]):
                self.warnings.append(
                    f"JWT_SECRET appears to be a placeholder: '{jwt_secret}'"
                )
            
            # Check entropy (basic)
            unique_chars = len(set(jwt_secret))
            if unique_chars < len(jwt_secret) / 4:
                self.warnings.append(
                    f"JWT_SECRET has low character diversity (only {unique_chars} unique chars)"
                )
        
        # Check expiry
        try:
            expiry_hours = int(expiry_str)
            if expiry_hours <= 0:
                self.issues.append((
                    "MEDIUM",
                    f"JWT_EXPIRY_HOURS must be positive, got: {expiry_hours}"
                ))
            elif expiry_hours > 720:  # 30 days
                self.warnings.append(
                    f"JWT_EXPIRY_HOURS is very long ({expiry_hours} hours = {expiry_hours/24:.1f} days)"
                )
            else:
                self.passed.append(
                    f"JWT expiry is set to {expiry_hours} hours"
                )
        except ValueError:
            self.issues.append((
                "MEDIUM",
                f"JWT_EXPIRY_HOURS is not a valid integer: '{expiry_str}'"
            ))
    
    def check_database_config(self) -> None:
        """Check database configuration."""
        logger.info("\n" + "="*80)
        logger.info("Database Configuration Audit")
        logger.info("="*80)
        
        database_url = os.environ.get("DATABASE_URL", "").strip()
        environment = os.environ.get("ENVIRONMENT", "production").lower()
        
        if not database_url:
            self.warnings.append("DATABASE_URL is not set")
        else:
            # Check for SSL in production
            if environment == "production":
                if "sslmode=require" not in database_url.lower():
                    self.warnings.append(
                        "DATABASE_URL doesn't include sslmode=require for production"
                    )
                else:
                    self.passed.append("Database SSL is configured")
            
            # Check for weak passwords (basic check)
            if "password=password" in database_url.lower() or \
               "password=admin" in database_url.lower() or \
               "password=123" in database_url.lower():
                self.issues.append((
                    "HIGH",
                    "Database URL appears to contain a weak password"
                ))
            
            self.passed.append("DATABASE_URL is configured")
    
    def check_external_services(self) -> None:
        """Check external service configuration."""
        logger.info("\n" + "="*80)
        logger.info("External Services Configuration")
        logger.info("="*80)
        
        services = {
            "Jira": ["JIRA_API_TOKEN", "JIRA_EMAIL", "JIRA_SERVER", "JIRA_PROJECT_KEY"],
            "GitHub": ["GITHUB_TOKEN", "GITHUB_REPO"],
            "Railway": ["RAILWAY_TOKEN"],
            "SonarCloud": ["SONARCLOUD_TOKEN", "SONARCLOUD_ORGANIZATION"],
        }
        
        for service_name, env_vars in services.items():
            configured = all(os.environ.get(var) for var in env_vars)
            if configured:
                self.passed.append(f"{service_name} integration is configured")
            else:
                missing = [var for var in env_vars if not os.environ.get(var)]
                if service_name in ["Jira", "GitHub"]:
                    # These are typically required
                    self.warnings.append(
                        f"{service_name} integration incomplete (missing: {', '.join(missing)})"
                    )
    
    def print_report(self) -> int:
        """Print audit report and return exit code."""
        logger.info("\n" + "="*80)
        logger.info("Security Audit Report")
        logger.info("="*80)
        
        # Count issues by severity
        critical = [i for s, i in self.issues if s == "CRITICAL"]
        high = [i for s, i in self.issues if s == "HIGH"]
        medium = [i for s, i in self.issues if s == "MEDIUM"]
        
        # Print passed checks
        if self.passed:
            logger.info("\n✅ Passed Checks:")
            for check in self.passed:
                logger.info(f"   • {check}")
        
        # Print warnings
        if self.warnings:
            logger.info("\n⚠️  Warnings:")
            for warning in self.warnings:
                logger.info(f"   • {warning}")
        
        # Print issues
        if critical:
            logger.info("\n🔴 CRITICAL Issues:")
            for issue in critical:
                logger.info(f"   • {issue}")
        
        if high:
            logger.info("\n🟠 HIGH Priority Issues:")
            for issue in high:
                logger.info(f"   • {issue}")
        
        if medium:
            logger.info("\n🟡 MEDIUM Priority Issues:")
            for issue in medium:
                logger.info(f"   • {issue}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("Summary")
        logger.info("="*80)
        logger.info(f"Passed:   {len(self.passed)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        logger.info(f"Critical: {len(critical)}")
        logger.info(f"High:     {len(high)}")
        logger.info(f"Medium:   {len(medium)}")
        
        # Determine exit code
        if critical:
            logger.info("\n❌ AUDIT FAILED - Critical issues must be resolved")
            return 1
        elif high:
            logger.info("\n⚠️  AUDIT WARNING - High priority issues should be resolved")
            return 1
        elif medium:
            logger.info("\n⚠️  AUDIT PASSED with medium priority issues")
            return 0
        else:
            logger.info("\n✅ AUDIT PASSED - No security issues found")
            return 0
    
    def run(self) -> int:
        """Run complete security audit."""
        logger.info("="*80)
        logger.info("SynPro Virtual Dev Team - Security Configuration Audit")
        logger.info("="*80)
        logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'production')}")
        
        try:
            self.check_cors_config()
            self.check_jwt_config()
            self.check_database_config()
            self.check_external_services()
            
            return self.print_report()
            
        except Exception as e:
            logger.error(f"\n❌ Audit failed with error: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main() -> int:
    """Main entry point."""
    audit = SecurityAudit()
    return audit.run()


if __name__ == "__main__":
    sys.exit(main())
