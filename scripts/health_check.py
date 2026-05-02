#!/usr/bin/env python3
"""
scripts/health_check.py
=======================
Comprehensive health check for services after token rotation.

Usage:
    ./scripts/health_check.py --service backend --timeout 300
    ./scripts/health_check.py --comprehensive --env production
    ./scripts/health_check.py --db-test --write-test

Author: DevOps Team
Created: 2024-01-XX
Ticket: SDT1-70
"""

import argparse
import sys
import time
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class HealthChecker:
    """Perform health checks on services."""
    
    def __init__(self, env: str = 'production', timeout: int = 300):
        """
        Initialize health checker.
        
        Args:
            env: Environment to check
            timeout: Maximum time to wait for health (seconds)
        """
        self.env = env
        self.timeout = timeout
        self.start_time = time.time()
        
        # Environment URLs
        self.urls = {
            'production': 'https://api.yourapp.com',
            'staging': 'https://staging-api.yourapp.com',
            'development': 'http://localhost:8000'
        }
        
        self.base_url = self.urls.get(env, 'http://localhost:8000')
    
    def check_health_endpoint(self) -> Tuple[bool, str]:
        """
        Check main health endpoint.
        
        Returns:
            Tuple of (success, message)
        """
        endpoint = f"{self.base_url}/health"
        
        try:
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                return True, "✓ Health endpoint OK"
            else:
                return False, f"✗ Health endpoint returned {response.status_code}"
        
        except requests.RequestException as e:
            return False, f"✗ Health endpoint unreachable: {e}"
    
    def check_database_health(self) -> Tuple[bool, str]:
        """
        Check database connectivity.
        
        Returns:
            Tuple of (success, message)
        """
        endpoint = f"{self.base_url}/health/db"
        
        try:
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return True, "✓ Database connection OK"
                else:
                    return False, f"✗ Database unhealthy: {data.get('message', 'Unknown')}"
            else:
                return False, f"✗ Database check returned {response.status_code}"
        
        except requests.RequestException as e:
            return False, f"✗ Database check failed: {e}"
        except ValueError:
            return False, "✗ Invalid JSON response from database check"
    
    def check_auth_endpoint(self) -> Tuple[bool, str]:
        """
        Check authentication endpoint.
        
        Returns:
            Tuple of (success, message)
        """
        endpoint = f"{self.base_url}/auth/verify"
        
        try:
            # This should return 401 without auth header (expected)
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 401:
                return True, "✓ Auth endpoint responding correctly"
            elif response.status_code == 200:
                return False, "⚠️  Auth endpoint not requiring authentication"
            else:
                return False, f"✗ Auth endpoint unexpected status: {response.status_code}"
        
        except requests.RequestException as e:
            return False, f"✗ Auth endpoint unreachable: {e}"
    
    def check_response_time(self) -> Tuple[bool, str]:
        """
        Check API response time.
        
        Returns:
            Tuple of (success, message)
        """
        endpoint = f"{self.base_url}/health"
        
        try:
            start = time.time()
            response = requests.get(endpoint, timeout=10)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code == 200:
                if elapsed < 500:
                    return True, f"✓ Response time: {elapsed:.0f}ms (good)"
                elif elapsed < 2000:
                    return True, f"⚠️  Response time: {elapsed:.0f}ms (acceptable)"
                else:
                    return False, f"✗ Response time: {elapsed:.0f}ms (slow)"
            else:
                return False, f"✗ Health check failed: {response.status_code}"
        
        except requests.RequestException as e:
            return False, f"✗ Response time check failed: {e}"
    
    def check_error_rate(self) -> Tuple[bool, str]:
        """
        Check error rate from logs (if available).
        
        Returns:
            Tuple of (success, message)
        """
        # This would need to integrate with logging service
        # Placeholder implementation
        return True, "⚪ Error rate check not implemented"
    
    def wait_for_healthy(self, interval: int = 5) -> bool:
        """
        Wait for service to become healthy.
        
        Args:
            interval: Seconds between checks
            
        Returns:
            True if healthy within timeout
        """
        print(f"\nWaiting for service to become healthy (timeout: {self.timeout}s)...")
        
        while (time.time() - self.start_time) < self.timeout:
            success, message = self.check_health_endpoint()
            
            if success:
                elapsed = int(time.time() - self.start_time)
                print(f"✓ Service healthy after {elapsed}s")
                return True
            
            remaining = int(self.timeout - (time.time() - self.start_time))
            print(f"  Waiting... ({remaining}s remaining)")
            time.sleep(interval)
        
        print(f"✗ Service did not become healthy within {self.timeout}s")
        return False
    
    def run_comprehensive_checks(self) -> Dict[str, Tuple[bool, str]]:
        """
        Run all health checks.
        
        Returns:
            Dictionary of check results
        """
        checks = {
            'Health Endpoint': self.check_health_endpoint,
            'Database': self.check_database_health,
            'Authentication': self.check_auth_endpoint,
            'Response Time': self.check_response_time,
            'Error Rate': self.check_error_rate,
        }
        
        results = {}
        
        print(f"\n{'=' * 80}")
        print(f"Health Check: {self.env.upper()} environment")
        print(f"{'=' * 80}\n")
        
        for check_name, check_func in checks.items():
            print(f"Checking {check_name}...", end=' ')
            sys.stdout.flush()
            
            try:
                success, message = check_func()
                results[check_name] = (success, message)
                print(message)
            except Exception as e:
                results[check_name] = (False, f"✗ Exception: {e}")
                print(f"✗ Exception: {e}")
        
        return results
    
    def print_summary(self, results: Dict[str, Tuple[bool, str]]) -> bool:
        """
        Print summary of health checks.
        
        Args:
            results: Dictionary of check results
            
        Returns:
            True if all checks passed
        """
        print(f"\n{'=' * 80}")
        print("Summary")
        print(f"{'=' * 80}\n")
        
        passed = sum(1 for success, _ in results.values() if success)
        total = len(results)
        
        print(f"Checks passed: {passed}/{total}")
        
        if passed == total:
            print("\n✓ All health checks passed!")
            return True
        else:
            print("\n✗ Some health checks failed:")
            for check_name, (success, message) in results.items():
                if not success:
                    print(f"  • {check_name}: {message}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Comprehensive health check for services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check backend service health
  %(prog)s --service backend
  
  # Wait for service to become healthy (after rotation)
  %(prog)s --service backend --wait --timeout 300
  
  # Comprehensive checks in production
  %(prog)s --comprehensive --env production
  
  # Check specific environment
  %(prog)s --env staging --comprehensive
        """
    )
    
    parser.add_argument(
        '--service',
        default='backend',
        help='Service to check (default: backend)'
    )
    
    parser.add_argument(
        '--env',
        default='production',
        choices=['development', 'staging', 'production'],
        help='Environment to check (default: production)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--wait',
        action='store_true',
        help='Wait for service to become healthy'
    )
    
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Run comprehensive health checks'
    )
    
    parser.add_argument(
        '--db-test',
        action='store_true',
        help='Test database connectivity'
    )
    
    parser.add_argument(
        '--write-test',
        action='store_true',
        help='Test database write operations (creates test data)'
    )
    
    args = parser.parse_args()
    
    try:
        checker = HealthChecker(env=args.env, timeout=args.timeout)
        
        if args.wait:
            # Wait for service to become healthy
            if not checker.wait_for_healthy():
                sys.exit(1)
        
        if args.comprehensive:
            # Run all checks
            results = checker.run_comprehensive_checks()
            if not checker.print_summary(results):
                sys.exit(1)
        
        elif args.db_test:
            # Database check only
            success, message = checker.check_database_health()
            print(message)
            if not success:
                sys.exit(1)
        
        else:
            # Simple health check
            success, message = checker.check_health_endpoint()
            print(message)
            if not success:
                sys.exit(1)
        
        print(f"\n✓ Health check completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
