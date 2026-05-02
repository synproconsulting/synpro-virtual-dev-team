#!/usr/bin/env python3
"""
generate_jwt_secret.py
══════════════════════
CLI utility to generate secure JWT secrets.

Usage:
    python generate_jwt_secret.py
    python generate_jwt_secret.py --length 64
    python generate_jwt_secret.py --validate "your-existing-secret"

Examples:
    # Generate a new secret
    $ python generate_jwt_secret.py
    Generated secure JWT secret (64 bytes, ~512 bits entropy):
    h8Kx2Vp9... (copy this to your JWT_SECRET environment variable)
    
    # Generate with custom length
    $ python generate_jwt_secret.py --length 32
    
    # Validate an existing secret
    $ python generate_jwt_secret.py --validate "my-secret-key"
    ❌ Secret is weak: Secret is too short (minimum 32 characters recommended, got 13)
"""

import argparse
import sys
from config import generate_jwt_secret, _is_weak_jwt_secret, _calculate_entropy_bits


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate and validate secure JWT secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate a new secret:
    python generate_jwt_secret.py
  
  Generate with custom length (bytes):
    python generate_jwt_secret.py --length 32
  
  Validate an existing secret:
    python generate_jwt_secret.py --validate "your-secret-here"
  
  Show help for deployment:
    python generate_jwt_secret.py --help-deploy
        """
    )
    
    parser.add_argument(
        "--length",
        type=int,
        default=64,
        help="Number of bytes of entropy (default: 64 = 512 bits)",
    )
    
    parser.add_argument(
        "--validate",
        type=str,
        metavar="SECRET",
        help="Validate an existing secret instead of generating a new one",
    )
    
    parser.add_argument(
        "--help-deploy",
        action="store_true",
        help="Show deployment instructions",
    )
    
    args = parser.parse_args()
    
    if args.help_deploy:
        print_deployment_help()
        return 0
    
    if args.validate:
        return validate_secret(args.validate)
    else:
        return generate_and_display_secret(args.length)


def generate_and_display_secret(length: int) -> int:
    """
    Generate and display a new JWT secret.
    
    Args:
        length: Number of bytes of entropy
        
    Returns:
        Exit code (0 for success)
    """
    try:
        secret = generate_jwt_secret(length=length)
        entropy = _calculate_entropy_bits(secret)
        
        print(f"Generated secure JWT secret ({length} bytes, ~{entropy:.0f} bits entropy):")
        print()
        print(secret)
        print()
        print("To use this secret, add it to your environment variables:")
        print()
        print(f'export JWT_SECRET="{secret}"')
        print()
        print("For production deployment, see: python generate_jwt_secret.py --help-deploy")
        
        return 0
    except Exception as e:
        print(f"❌ Error generating secret: {e}", file=sys.stderr)
        return 1


def validate_secret(secret: str) -> int:
    """
    Validate an existing JWT secret.
    
    Args:
        secret: The secret to validate
        
    Returns:
        Exit code (0 for valid, 1 for invalid)
    """
    is_weak, reason = _is_weak_jwt_secret(secret)
    entropy = _calculate_entropy_bits(secret)
    
    print(f"Secret analysis:")
    print(f"  Length: {len(secret)} characters")
    print(f"  Entropy: ~{entropy:.0f} bits")
    print(f"  Unique characters: {len(set(secret))}")
    print()
    
    if is_weak:
        print(f"❌ Secret is weak: {reason}")
        print()
        print("Generate a secure secret using:")
        print("  python generate_jwt_secret.py")
        return 1
    else:
        print("✓ Secret appears to be strong")
        print()
        print("Recommendations:")
        print("  - Store securely (e.g., environment variables, secrets manager)")
        print("  - Never commit to version control")
        print("  - Rotate regularly (e.g., every 90 days)")
        print("  - Use different secrets for different environments")
        return 0


def print_deployment_help():
    """Print deployment instructions."""
    print("""
JWT Secret Deployment Guide
════════════════════════════

1. Generate a Secret
   ──────────────────
   Run this script to generate a cryptographically secure secret:
   
     python generate_jwt_secret.py
   
   This will output a base64-encoded secret with 512 bits of entropy.

2. Store Securely
   ──────────────
   NEVER commit the secret to version control. Instead:
   
   a) Local Development:
      Add to your .env file (make sure .env is in .gitignore):
      
        JWT_SECRET=<your-generated-secret>
      
   b) Docker:
      Pass as environment variable:
      
        docker run -e JWT_SECRET=<your-secret> ...
      
   c) Kubernetes:
      Create a secret:
      
        kubectl create secret generic jwt-secret \\
          --from-literal=JWT_SECRET=<your-secret>
        
      Then reference in deployment:
      
        env:
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: JWT_SECRET
   
   d) AWS/Cloud:
      Use a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)

3. Environment Configuration
   ──────────────────────────
   Set these environment variables:
   
     ENVIRONMENT=production          # Required: enables strict validation
     JWT_SECRET=<your-secret>        # Required: your secure secret
     JWT_EXPIRY_HOURS=24            # Optional: default is 24 hours

4. Validation
   ──────────
   On startup, the application will validate your JWT configuration.
   If the secret is weak or missing, it will fail to start (fail-fast).
   
   To manually validate a secret:
   
     python generate_jwt_secret.py --validate "<your-secret>"

5. Security Best Practices
   ────────────────────────
   ✓ Use different secrets for different environments
   ✓ Rotate secrets regularly (every 90 days recommended)
   ✓ Use at least 64 bytes (512 bits) of entropy
   ✓ Store in a secure secrets management system
   ✓ Never log or expose the secret in error messages
   ✓ Use HTTPS/TLS in production to protect tokens in transit
   
   ✗ Never commit secrets to git
   ✗ Never use default/example secrets in production
   ✗ Never reuse secrets across different applications
   ✗ Never share secrets via insecure channels (email, chat, etc.)

6. Troubleshooting
   ───────────────
   If you see: "JWT_SECRET must be set in production"
   → Set the JWT_SECRET environment variable
   
   If you see: "Insecure JWT secret detected"
   → Your secret is too weak. Generate a new one using this script
   
   If you see: "Secret is too short"
   → Use at least 32 characters (64 bytes recommended)
   
   If you see: "Secret has low entropy"
   → Don't use simple passwords. Use this script to generate secrets

For more information, see the documentation at:
https://github.com/your-org/your-repo/docs/security.md
""")


if __name__ == "__main__":
    sys.exit(main())
