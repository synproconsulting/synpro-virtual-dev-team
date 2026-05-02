#!/usr/bin/env python3
"""
Generate a secure JWT secret key.

This script generates a cryptographically secure random secret suitable
for use as a JWT signing key.

Usage:
    python scripts/generate_jwt_secret.py

The script will:
1. Generate a secure random secret (256 bits)
2. Validate the secret meets security requirements
3. Display instructions for setting the environment variable
"""

import secrets
import sys
import os

# Add parent directory to path to import jwt_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'uat', 'backend'))

try:
    from jwt_utils import _validate_secret_strength, MIN_SECRET_LENGTH_BYTES
except ImportError:
    print("Error: Could not import jwt_utils. Make sure you're running from the project root.")
    sys.exit(1)


def generate_secret(length_bytes: int = 32) -> str:
    """
    Generate a cryptographically secure random secret.
    
    Args:
        length_bytes: Length in bytes (default: 32 = 256 bits)
        
    Returns:
        URL-safe base64-encoded random string
    """
    return secrets.token_urlsafe(length_bytes)


def main():
    """Generate and display a secure JWT secret."""
    print("=" * 70)
    print("JWT Secret Generator")
    print("=" * 70)
    print()
    
    # Generate secret
    print(f"Generating {MIN_SECRET_LENGTH_BYTES * 8}-bit secret...")
    secret = generate_secret(MIN_SECRET_LENGTH_BYTES)
    
    # Validate it meets requirements
    try:
        _validate_secret_strength(secret)
        print("✓ Secret validated successfully")
    except Exception as e:
        print(f"✗ Generated secret failed validation: {e}")
        print("This should not happen. Please report this issue.")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("Your new JWT secret:")
    print("=" * 70)
    print()
    print(secret)
    print()
    print("=" * 70)
    print("Setup Instructions:")
    print("=" * 70)
    print()
    print("1. Copy the secret above")
    print()
    print("2. Set the environment variable:")
    print()
    print(f"   export JWT_SECRET='{secret}'")
    print()
    print("3. Or add to your .env file:")
    print()
    print(f"   JWT_SECRET={secret}")
    print()
    print("4. IMPORTANT: Never commit this secret to version control!")
    print()
    print("=" * 70)
    print("Key Rotation (Optional):")
    print("=" * 70)
    print()
    print("If you're rotating an existing key:")
    print()
    print("1. Set your current JWT_SECRET as JWT_SECRET_OLD:")
    print("   export JWT_SECRET_OLD='your-current-secret'")
    print()
    print("2. Set the new secret as JWT_SECRET:")
    print(f"   export JWT_SECRET='{secret}'")
    print()
    print("3. Deploy the application")
    print()
    print("4. Wait for old tokens to expire (default: 24 hours)")
    print()
    print("5. Remove JWT_SECRET_OLD from environment")
    print()
    print("=" * 70)
    
    # Additional security notes
    print()
    print("Security Notes:")
    print("-" * 70)
    print("• Store this secret securely (password manager, secrets vault)")
    print("• Use different secrets for development/staging/production")
    print("• Rotate secrets regularly (e.g., every 90 days)")
    print("• Never share secrets via email, chat, or public channels")
    print("• Never commit secrets to git repositories")
    print("• Use secret management services in production:")
    print("  - AWS Secrets Manager")
    print("  - HashiCorp Vault")
    print("  - Azure Key Vault")
    print("  - Google Cloud Secret Manager")
    print()


if __name__ == "__main__":
    main()
