#!/usr/bin/env python3
"""
CLI tool to generate secure JWT secrets.
Part of SDT1-63: Harden JWT secret key handling.

Usage:
    python generate_secret.py
    python generate_secret.py --length 64
"""

import argparse
import sys
from security_config import generate_secure_secret


def main():
    """Generate and print a secure JWT secret."""
    parser = argparse.ArgumentParser(
        description="Generate a cryptographically secure JWT secret",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a default 64-character secret
  python generate_secret.py

  # Generate a shorter 48-character secret
  python generate_secret.py --length 48

  # Generate and save directly to .env file
  python generate_secret.py >> .env

Usage in .env file:
  JWT_SECRET=<generated-secret>
  ENVIRONMENT=production
        """
    )
    
    parser.add_argument(
        "--length",
        type=int,
        default=48,
        help="Number of bytes for secret generation (default: 48, results in ~64 chars)"
    )
    
    parser.add_argument(
        "--format",
        choices=["env", "plain"],
        default="env",
        help="Output format: 'env' for .env file format, 'plain' for just the secret"
    )
    
    args = parser.parse_args()
    
    # Validate length
    if args.length < 32:
        print("Error: Length must be at least 32 bytes for security", file=sys.stderr)
        return 1
    
    # Generate secret (use different import if custom length needed)
    if args.length == 48:
        secret = generate_secure_secret()
    else:
        import secrets
        secret = secrets.token_urlsafe(args.length)
    
    # Output in requested format
    if args.format == "env":
        print(f"JWT_SECRET={secret}")
    else:
        print(secret)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
