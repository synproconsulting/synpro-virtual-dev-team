#!/usr/bin/env python3
"""
scripts/generate_secrets.py
===========================
Generate cryptographically secure secrets for various purposes.

Usage:
    ./scripts/generate_secrets.py --type jwt
    ./scripts/generate_secrets.py --type database
    ./scripts/generate_secrets.py --type api --length 48
    ./scripts/generate_secrets.py --all

Author: DevOps Team
Created: 2024-01-XX
Ticket: SDT1-70
"""

import argparse
import secrets
import string
import base64
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from uat.backend.config import generate_jwt_secret, _calculate_entropy_bits
except ImportError:
    # Fallback implementations
    def generate_jwt_secret(length: int = 64) -> str:
        """Generate JWT secret."""
        secret_bytes = secrets.token_bytes(length)
        return base64.b64encode(secret_bytes).decode('utf-8')
    
    def _calculate_entropy_bits(secret: str) -> float:
        """Calculate entropy bits."""
        import math
        unique_chars = len(set(secret))
        if unique_chars <= 10:
            bits_per_char = math.log2(10)
        elif unique_chars <= 26:
            bits_per_char = math.log2(26)
        elif unique_chars <= 36:
            bits_per_char = math.log2(36)
        elif unique_chars <= 62:
            bits_per_char = math.log2(62)
        else:
            bits_per_char = math.log2(95)
        return len(secret) * bits_per_char


class SecretGenerator:
    """Generate various types of secure secrets."""
    
    @staticmethod
    def generate_jwt_secret(length: int = 64) -> str:
        """
        Generate a JWT secret key.
        
        Args:
            length: Number of bytes (default: 64 = 512 bits)
            
        Returns:
            Base64-encoded secret
        """
        if length < 32:
            raise ValueError("JWT secret must be at least 32 bytes")
        
        secret_bytes = secrets.token_bytes(length)
        return base64.b64encode(secret_bytes).decode('utf-8')
    
    @staticmethod
    def generate_database_password(length: int = 32) -> str:
        """
        Generate a database password.
        
        Args:
            length: Password length (default: 32)
            
        Returns:
            Secure random password
        """
        if length < 16:
            raise ValueError("Database password must be at least 16 characters")
        
        # Use alphanumeric + safe special characters
        chars = string.ascii_letters + string.digits + '!@#$%^&*()-_=+[]{}|;:,.<>?'
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        # Ensure password contains at least one of each type
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?' for c in password)
        
        # Regenerate if requirements not met
        if not (has_upper and has_lower and has_digit and has_special):
            return SecretGenerator.generate_database_password(length)
        
        return password
    
    @staticmethod
    def generate_api_token(length: int = 48) -> str:
        """
        Generate an API token.
        
        Args:
            length: Token length in bytes (default: 48)
            
        Returns:
            URL-safe base64 token
        """
        if length < 32:
            raise ValueError("API token must be at least 32 bytes")
        
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_symmetric_key(length: int = 32) -> str:
        """
        Generate a symmetric encryption key.
        
        Args:
            length: Key length in bytes (default: 32 = 256 bits for AES-256)
            
        Returns:
            Hex-encoded key
        """
        if length not in [16, 24, 32]:  # AES-128, AES-192, AES-256
            raise ValueError("Symmetric key must be 16, 24, or 32 bytes")
        
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_random_string(length: int = 32, charset: str = None) -> str:
        """
        Generate a random string with custom charset.
        
        Args:
            length: String length
            charset: Character set to use (default: alphanumeric)
            
        Returns:
            Random string
        """
        if charset is None:
            charset = string.ascii_letters + string.digits
        
        return ''.join(secrets.choice(charset) for _ in range(length))
    
    @staticmethod
    def generate_otp_secret(length: int = 32) -> str:
        """
        Generate a TOTP/HOTP secret.
        
        Args:
            length: Secret length in bytes (default: 32)
            
        Returns:
            Base32-encoded secret (for TOTP apps)
        """
        secret_bytes = secrets.token_bytes(length)
        return base64.b32encode(secret_bytes).decode('utf-8').rstrip('=')
    
    @staticmethod
    def generate_csrf_token(length: int = 32) -> str:
        """
        Generate a CSRF token.
        
        Args:
            length: Token length in bytes (default: 32)
            
        Returns:
            URL-safe token
        """
        return secrets.token_urlsafe(length)


def print_secret(name: str, secret: str, copy_hint: bool = True) -> None:
    """
    Print a secret with formatting.
    
    Args:
        name: Secret name/type
        secret: Secret value
        copy_hint: Whether to show copy hint
    """
    entropy = _calculate_entropy_bits(secret)
    
    print(f"\n{'=' * 80}")
    print(f"{name}")
    print(f"{'=' * 80}")
    print(f"\nSecret:")
    print(f"  {secret}")
    print(f"\nProperties:")
    print(f"  Length: {len(secret)} characters")
    print(f"  Entropy: ~{entropy:.0f} bits")
    
    if copy_hint:
        print(f"\nTo copy to clipboard (macOS):")
        print(f"  echo '{secret}' | pbcopy")
        print(f"\nTo copy to clipboard (Linux):")
        print(f"  echo '{secret}' | xclip -selection clipboard")
    
    print(f"\nEnvironment variable:")
    env_var = {
        'JWT Secret': 'JWT_SECRET',
        'Database Password': 'DATABASE_URL',
        'API Token': 'API_TOKEN',
        'Symmetric Key': 'ENCRYPTION_KEY',
        'CSRF Token': 'CSRF_SECRET',
        'OTP Secret': 'OTP_SECRET'
    }.get(name, 'SECRET')
    
    print(f"  export {env_var}='{secret}'")
    print(f"{'=' * 80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate cryptographically secure secrets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate JWT secret
  %(prog)s --type jwt
  
  # Generate database password
  %(prog)s --type database
  
  # Generate API token with custom length
  %(prog)s --type api --length 64
  
  # Generate all types
  %(prog)s --all
  
  # Generate symmetric encryption key (AES-256)
  %(prog)s --type symmetric
        """
    )
    
    parser.add_argument(
        '--type',
        choices=['jwt', 'database', 'api', 'symmetric', 'otp', 'csrf', 'random'],
        help='Type of secret to generate'
    )
    
    parser.add_argument(
        '--length',
        type=int,
        help='Length of secret (in bytes for most types, in characters for passwords)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate all common secret types'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of secrets to generate (default: 1)'
    )
    
    parser.add_argument(
        '--no-hints',
        action='store_true',
        help='Skip usage hints'
    )
    
    args = parser.parse_args()
    
    if not args.type and not args.all:
        parser.error("Must specify --type or --all")
    
    generator = SecretGenerator()
    
    try:
        if args.all:
            # Generate all common types
            print("\n🔐 Generating secure secrets for all common types...\n")
            
            secrets_to_generate = [
                ('JWT Secret', lambda: generator.generate_jwt_secret()),
                ('Database Password', lambda: generator.generate_database_password()),
                ('API Token', lambda: generator.generate_api_token()),
                ('Symmetric Key', lambda: generator.generate_symmetric_key()),
                ('CSRF Token', lambda: generator.generate_csrf_token()),
            ]
            
            for name, gen_func in secrets_to_generate:
                secret = gen_func()
                print_secret(name, secret, copy_hint=not args.no_hints)
        
        else:
            # Generate specific type
            type_mapping = {
                'jwt': ('JWT Secret', lambda: generator.generate_jwt_secret(args.length or 64)),
                'database': ('Database Password', lambda: generator.generate_database_password(args.length or 32)),
                'api': ('API Token', lambda: generator.generate_api_token(args.length or 48)),
                'symmetric': ('Symmetric Key', lambda: generator.generate_symmetric_key(args.length or 32)),
                'otp': ('OTP Secret', lambda: generator.generate_otp_secret(args.length or 32)),
                'csrf': ('CSRF Token', lambda: generator.generate_csrf_token(args.length or 32)),
                'random': ('Random String', lambda: generator.generate_random_string(args.length or 32)),
            }
            
            name, gen_func = type_mapping[args.type]
            
            if args.count == 1:
                secret = gen_func()
                print_secret(name, secret, copy_hint=not args.no_hints)
            else:
                print(f"\n🔐 Generating {args.count} {name}s...\n")
                for i in range(args.count):
                    secret = gen_func()
                    print(f"{i + 1}. {secret}")
                print()
        
        # Security reminder
        if not args.no_hints:
            print("\n⚠️  SECURITY REMINDERS:")
            print("  • Never commit secrets to version control")
            print("  • Store in secure password manager or secret management system")
            print("  • Use unique secrets for each environment (dev/staging/prod)")
            print("  • Rotate secrets regularly (see docs/runbooks/TOKEN_ROTATION.md)")
            print("  • Clear terminal history after copying secrets")
            print()
    
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
