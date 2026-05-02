#!/usr/bin/env python3
"""
JWT CLI Tool - Helper for JWT secret management (SDT1-63).

Usage:
    python cli_jwt.py generate              # Generate a new secure secret
    python cli_jwt.py validate <secret>     # Validate a secret
    python cli_jwt.py info                  # Show current JWT configuration
    python cli_jwt.py create <user_id> <email>  # Create a test token
    python cli_jwt.py decode <token>        # Decode a token (for debugging)

Examples:
    # Generate a new secret
    python cli_jwt.py generate
    
    # Validate your secret
    python cli_jwt.py validate "your-secret-here"
    
    # Check current configuration
    python cli_jwt.py info
    
    # Create a test token
    python cli_jwt.py create user123 test@example.com
    
    # Decode a token (without verification)
    python cli_jwt.py decode eyJhbGc...
"""

import sys
import os
import argparse
import json
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jwt_config import (
    generate_secure_secret,
    _validate_jwt_secret,
    _calculate_entropy,
    get_jwt_config,
    JWTConfigError,
    JWTKeyValidationError,
)
import jwt as pyjwt


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(msg: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}✗ {msg}{Colors.END}", file=sys.stderr)


def print_warning(msg: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_info(msg: str) -> None:
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


def print_header(msg: str) -> None:
    """Print header message in bold."""
    print(f"\n{Colors.BOLD}{msg}{Colors.END}")


def cmd_generate(args) -> int:
    """Generate a new secure JWT secret."""
    print_header("Generating Secure JWT Secret")
    
    length = args.length if hasattr(args, 'length') else 32
    secret = generate_secure_secret(length)
    
    # Validate it
    try:
        _validate_jwt_secret(secret)
        print_success(f"Generated secure secret (length: {len(secret)} chars)")
    except Exception as e:
        print_error(f"Generated secret failed validation: {e}")
        return 1
    
    # Show entropy
    entropy = _calculate_entropy(secret)
    print_info(f"Entropy: {entropy:.2f} bits/char")
    
    # Print the secret
    print(f"\n{Colors.CYAN}JWT_SECRET={secret}{Colors.END}")
    
    # Instructions
    print_header("Next Steps")
    print("1. Copy the secret above to your .env file")
    print("2. Never commit the secret to version control")
    print("3. Restart your application to use the new secret")
    
    if os.environ.get("JWT_SECRET"):
        print_warning("\nNote: JWT_SECRET is already set in your environment")
        print("      For key rotation, use JWT_SECRET_OLD (see docs/JWT_SECURITY.md)")
    
    return 0


def cmd_validate(args) -> int:
    """Validate a JWT secret."""
    secret = args.secret
    
    print_header(f"Validating JWT Secret")
    print_info(f"Length: {len(secret)} characters")
    
    # Calculate entropy
    entropy = _calculate_entropy(secret)
    print_info(f"Entropy: {entropy:.2f} bits/char")
    
    # Unique characters
    unique = len(set(secret))
    diversity = (unique / len(secret)) * 100 if secret else 0
    print_info(f"Character diversity: {unique} unique chars ({diversity:.1f}%)")
    
    # Validate
    try:
        _validate_jwt_secret(secret)
        print_success("Secret passed validation ✓")
        print("This secret meets security requirements")
        return 0
    except JWTKeyValidationError as e:
        print_error(f"Validation failed: {e}")
        print_header("Recommendations")
        print("• Use at least 32 characters")
        print("• Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        print("• Avoid common patterns like 'secret', 'test', 'dev'")
        print("• Use high entropy (random) characters")
        return 1


def cmd_info(args) -> int:
    """Show current JWT configuration."""
    print_header("JWT Configuration")
    
    # Check if JWT_SECRET is set
    jwt_secret = os.environ.get("JWT_SECRET", "")
    if not jwt_secret:
        print_error("JWT_SECRET is not set in environment")
        print_info("Generate a secret with: python cli_jwt.py generate")
        return 1
    
    # Validate and show config
    try:
        config = get_jwt_config()
        
        # Primary secret info (don't show the actual secret!)
        secret_preview = jwt_secret[:8] + "..." + jwt_secret[-8:] if len(jwt_secret) > 16 else "***"
        print_success(f"JWT_SECRET is configured")
        print(f"  Preview: {secret_preview}")
        print(f"  Length: {len(jwt_secret)} characters")
        
        entropy = _calculate_entropy(jwt_secret)
        print(f"  Entropy: {entropy:.2f} bits/char")
        
        # Expiry
        expiry = os.environ.get("JWT_EXPIRY_HOURS", "24")
        print(f"\n{Colors.BOLD}Token Expiry:{Colors.END} {expiry} hours")
        
        # Old secrets
        old_secrets = os.environ.get("JWT_SECRET_OLD", "")
        if old_secrets:
            count = len([s for s in old_secrets.split(",") if s.strip()])
            print_info(f"Key rotation enabled: {count} old secret(s) configured")
        else:
            print_info("Key rotation not configured (no old secrets)")
        
        # Algorithm
        print(f"\n{Colors.BOLD}Algorithm:{Colors.END} {config.algorithm}")
        
        print_success("\nConfiguration is valid")
        return 0
        
    except JWTConfigError as e:
        print_error(f"Configuration error: {e}")
        return 1


def cmd_create(args) -> int:
    """Create a test JWT token."""
    user_id = args.user_id
    email = args.email
    
    print_header(f"Creating JWT Token")
    print_info(f"User ID: {user_id}")
    print_info(f"Email: {email}")
    
    try:
        config = get_jwt_config()
        token = config.create_token(user_id, email)
        
        print_success("Token created successfully")
        print(f"\n{Colors.CYAN}{token}{Colors.END}\n")
        
        # Decode to show payload
        payload = pyjwt.decode(token, options={"verify_signature": False})
        print_header("Token Payload")
        print(json.dumps(payload, indent=2, default=str))
        
        return 0
        
    except JWTConfigError as e:
        print_error(f"Failed to create token: {e}")
        return 1


def cmd_decode(args) -> int:
    """Decode a JWT token (without verification)."""
    token = args.token
    
    print_header("Decoding JWT Token")
    
    try:
        # Decode without verification (for inspection)
        payload = pyjwt.decode(token, options={"verify_signature": False})
        
        print_success("Token decoded successfully")
        print("\n" + json.dumps(payload, indent=2, default=str))
        
        # Try to validate signature if config is available
        try:
            config = get_jwt_config()
            config.decode_token(token)
            print_success("\n✓ Token signature is valid")
        except pyjwt.ExpiredSignatureError:
            print_warning("\n⚠ Token signature is valid but token has expired")
        except pyjwt.InvalidTokenError:
            print_error("\n✗ Token signature is invalid (wrong secret or corrupted)")
        except JWTConfigError:
            print_info("\n(Signature verification skipped - JWT_SECRET not configured)")
        
        return 0
        
    except pyjwt.InvalidTokenError as e:
        print_error(f"Failed to decode token: {e}")
        print_info("Token appears to be malformed or corrupted")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="JWT Secret Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a new secure secret")
    gen_parser.add_argument(
        "--length",
        type=int,
        default=32,
        help="Secret length in bytes (default: 32)"
    )
    
    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate a JWT secret")
    val_parser.add_argument("secret", help="Secret to validate")
    
    # Info command
    subparsers.add_parser("info", help="Show current JWT configuration")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a test JWT token")
    create_parser.add_argument("user_id", help="User ID for token")
    create_parser.add_argument("email", help="Email for token")
    
    # Decode command
    decode_parser = subparsers.add_parser("decode", help="Decode a JWT token")
    decode_parser.add_argument("token", help="JWT token to decode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command handler
    commands = {
        "generate": cmd_generate,
        "validate": cmd_validate,
        "info": cmd_info,
        "create": cmd_create,
        "decode": cmd_decode,
    }
    
    handler = commands.get(args.command)
    if handler:
        try:
            return handler(args)
        except KeyboardInterrupt:
            print_error("\nInterrupted")
            return 130
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print_error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
