# JWT CLI Tool

Command-line utility for managing JWT secrets and tokens in the SynPro Virtual Dev Team platform.

## Installation

The CLI tool is located at `uat/backend/cli_jwt.py` and requires no additional installation beyond the project's Python dependencies.

## Usage

### Generate a New Secret

Generate a cryptographically secure JWT secret:

```bash
python uat/backend/cli_jwt.py generate
```

Output:
```
Generating Secure JWT Secret
✓ Generated secure secret (length: 43 chars)
ℹ Entropy: 5.23 bits/char

JWT_SECRET=vK8Qx3ZtN9mP2wR5yJ7sL1nF4hD6gA8cE0bT3xW5yR9qM2pL4k

Next Steps
1. Copy the secret above to your .env file
2. Never commit the secret to version control
3. Restart your application to use the new secret
```

### Validate a Secret

Check if a secret meets security requirements:

```bash
python uat/backend/cli_jwt.py validate "your-secret-here"
```

Output for valid secret:
```
Validating JWT Secret
ℹ Length: 43 characters
ℹ Entropy: 5.23 bits/char
ℹ Character diversity: 38 unique chars (88.4%)
✓ Secret passed validation ✓
This secret meets security requirements
```

Output for weak secret:
```
Validating JWT Secret
ℹ Length: 10 characters
ℹ Entropy: 2.85 bits/char
ℹ Character diversity: 8 unique chars (80.0%)
✗ Validation failed: JWT secret must be at least 32 characters long...

Recommendations
• Use at least 32 characters
• Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
• Avoid common patterns like 'secret', 'test', 'dev'
• Use high entropy (random) characters
```

### Show Current Configuration

Display current JWT configuration from environment:

```bash
python uat/backend/cli_jwt.py info
```

Output:
```
JWT Configuration
✓ JWT_SECRET is configured
  Preview: vK8Qx3Zt...yR9qM2pL4k
  Length: 43 characters
  Entropy: 5.23 bits/char

Token Expiry: 24 hours
ℹ Key rotation not configured (no old secrets)

Algorithm: HS256

✓ Configuration is valid
```

### Create a Test Token

Generate a JWT token for testing:

```bash
python uat/backend/cli_jwt.py create user123 test@example.com
```

Output:
```
Creating JWT Token
ℹ User ID: user123
ℹ Email: test@example.com
✓ Token created successfully

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaWF0IjoxNzA5NTU2MjM0LCJleHAiOjE3MDk2NDI2MzR9.abc123...

Token Payload
{
  "sub": "user123",
  "email": "test@example.com",
  "iat": 1709556234,
  "exp": 1709642634
}
```

### Decode a Token

Inspect a JWT token's contents:

```bash
python uat/backend/cli_jwt.py decode "eyJhbGc..."
```

Output:
```
Decoding JWT Token
✓ Token decoded successfully

{
  "sub": "user123",
  "email": "test@example.com",
  "iat": 1709556234,
  "exp": 1709642634
}

✓ Token signature is valid
```

For expired tokens:
```
⚠ Token signature is valid but token has expired
```

For invalid signatures:
```
✗ Token signature is invalid (wrong secret or corrupted)
```

## Common Workflows

### Initial Setup

```bash
# 1. Generate a secret
python uat/backend/cli_jwt.py generate

# 2. Add to .env file
echo "JWT_SECRET=<generated-secret>" >> .env

# 3. Verify configuration
python uat/backend/cli_jwt.py info
```

### Key Rotation

```bash
# 1. Generate new secret
python uat/backend/cli_jwt.py generate
# Copy the new secret

# 2. Update .env file
# Keep old secret in JWT_SECRET_OLD
JWT_SECRET=<new-secret>
JWT_SECRET_OLD=<old-secret>

# 3. Verify both secrets work
python uat/backend/cli_jwt.py info

# 4. After token expiry period, remove old secret
```

### Testing Tokens

```bash
# Create a test token
TOKEN=$(python uat/backend/cli_jwt.py create user123 test@example.com | grep "eyJ" | head -1)

# Test API with token
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Decode to inspect
python uat/backend/cli_jwt.py decode "$TOKEN"
```

### Security Audit

```bash
# Check current secret strength
python uat/backend/cli_jwt.py info

# If weak, generate new secret
python uat/backend/cli_jwt.py generate

# Validate before using
python uat/backend/cli_jwt.py validate "<new-secret>"
```

## Environment Variables

The CLI tool reads these environment variables:

- `JWT_SECRET` - Primary JWT secret (required for most commands)
- `JWT_SECRET_OLD` - Old secrets for key rotation (optional)
- `JWT_EXPIRY_HOURS` - Token expiry in hours (default: 24)

## Exit Codes

- `0` - Success
- `1` - Error (validation failed, configuration error, etc.)
- `130` - Interrupted (Ctrl+C)

## Examples

### Quick Secret Generation

```bash
# Just the secret, no formatting
python uat/backend/cli_jwt.py generate | grep JWT_SECRET= | cut -d= -f2
```

### Validate Multiple Secrets

```bash
# Check if all secrets are strong
for secret in secret1 secret2 secret3; do
  echo "Testing: $secret"
  python uat/backend/cli_jwt.py validate "$secret"
  echo "---"
done
```

### Automated Testing

```bash
#!/bin/bash
# Generate secret, set in env, create token, test API

SECRET=$(python uat/backend/cli_jwt.py generate | grep "JWT_SECRET=" | cut -d= -f2)
export JWT_SECRET="$SECRET"

TOKEN=$(python uat/backend/cli_jwt.py create testuser test@example.com | grep "eyJ" | head -1)

curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### "JWT_SECRET is not set in environment"

Set the JWT_SECRET environment variable:

```bash
export JWT_SECRET=$(python uat/backend/cli_jwt.py generate | grep "JWT_SECRET=" | cut -d= -f2)
```

### "Validation failed: JWT secret must be at least 32 characters"

Your secret is too short. Generate a new one:

```bash
python uat/backend/cli_jwt.py generate
```

### "Token signature is invalid"

The token was created with a different secret. Possible causes:
- JWT_SECRET changed since token was created
- Token was modified/corrupted
- Token is from different environment

For key rotation, use `JWT_SECRET_OLD` to keep old tokens valid.

## Security Notes

- ⚠️ Never share secrets in logs, error messages, or public channels
- ⚠️ Never commit secrets to version control
- ⚠️ Use different secrets for different environments
- ✓ Rotate secrets periodically (recommended: annually)
- ✓ Use `generate` command for cryptographically secure secrets
- ✓ Validate secrets with `validate` command before using

## See Also

- [JWT Security Guide](../../docs/JWT_SECURITY.md) - Comprehensive JWT security documentation
- [.env.example](../../.env.example) - Environment variable configuration
- [jwt_config.py](jwt_config.py) - JWT configuration module source code
