# JWT Token Refresh Mechanism

A secure and production-ready JWT token refresh implementation for Python applications.

## Features

- **Access Token Management**: Short-lived access tokens (default: 15 minutes)
- **Refresh Token Management**: Long-lived refresh tokens (default: 7 days)
- **Token Validation**: Comprehensive token verification and expiration checking
- **Token Refresh**: Seamless token renewal without re-authentication
- **Additional Claims Support**: Include custom claims in tokens (roles, permissions, etc.)
- **Security Best Practices**: Uses industry-standard libraries (python-jose, passlib)
- **Environment Variable Configuration**: Secret keys managed via environment variables

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

Set the following environment variable for production use:

```bash
export JWT_SECRET_KEY="your-secret-key-here"
```

**Important**: Never commit secret keys to version control. Use environment variables or a secure secrets management system.

## Usage

### Basic Setup

```python
from src.auth import JWTTokenManager

# Initialize with environment variable
manager = JWTTokenManager()

# Or initialize with explicit secret (for testing only)
manager = JWTTokenManager(
    secret_key="test-secret",
    access_token_expire_minutes=15,
    refresh_token_expire_days=7
)
```

### Creating Tokens

```python
# Create a token pair (access + refresh)
access_token, refresh_token = manager.create_token_pair("user123")

# Create tokens with additional claims
access_token, refresh_token = manager.create_token_pair(
    "user123",
    additional_claims={"role": "admin", "email": "user@example.com"}
)

# Create individual tokens
access_token = manager.create_access_token("user123")
refresh_token = manager.create_refresh_token("user123")
```

### Validating Tokens

```python
try:
    # Decode and validate token
    payload = manager.decode_token(access_token)
    user_id = payload["sub"]
    
    # Check if token is expired
    if manager.is_token_expired(access_token):
        print("Token has expired")
    
    # Get token expiration time
    expiry = manager.get_token_expiry(access_token)
    
except TokenRefreshError as e:
    print(f"Token validation failed: {e}")
```

### Refreshing Tokens

```python
try:
    # Refresh access token only
    new_access_token = manager.refresh_access_token(refresh_token)
    
    # Refresh both tokens
    new_access_token, new_refresh_token = manager.refresh_token_pair(
        refresh_token
    )
    
    # Refresh with new claims
    new_access_token = manager.refresh_access_token(
        refresh_token,
        additional_claims={"role": "editor"}
    )
    
except TokenRefreshError as e:
    print(f"Token refresh failed: {e}")
```

## API Reference

### JWTTokenManager

Main class for managing JWT tokens.

#### Methods

- `create_access_token(subject, additional_claims=None)` - Create a new access token
- `create_refresh_token(subject, additional_claims=None)` - Create a new refresh token
- `create_token_pair(subject, additional_claims=None)` - Create both access and refresh tokens
- `decode_token(token)` - Decode and validate a token
- `verify_refresh_token(refresh_token)` - Verify a refresh token and extract subject
- `refresh_access_token(refresh_token, additional_claims=None)` - Generate new access token
- `refresh_token_pair(refresh_token, additional_claims=None)` - Generate new token pair
- `get_token_expiry(token)` - Get token expiration datetime
- `is_token_expired(token)` - Check if token is expired

### TokenRefreshError

Exception raised when token operations fail (invalid token, expired, wrong type, etc.).

## Testing

Run the test suite:

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/auth --cov-report=term-missing

# Run specific test file
pytest tests/test_jwt_refresh.py -v
```

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py
│       └── jwt_refresh.py       # Main JWT token manager implementation
├── tests/
│   ├── __init__.py
│   └── test_jwt_refresh.py      # Comprehensive unit tests
├── requirements.txt              # Project dependencies
└── README.md                     # This file
```

## Security Considerations

1. **Secret Key Management**: Always use strong, randomly generated secret keys
2. **HTTPS Only**: Only transmit tokens over HTTPS in production
3. **Token Storage**: Store tokens securely (httpOnly cookies for web, secure storage for mobile)
4. **Token Expiration**: Use short expiration times for access tokens
5. **Refresh Token Rotation**: Consider implementing refresh token rotation for enhanced security
6. **Revocation**: Implement token revocation for logout and security events

## Dependencies

- `python-jose[cryptography]` - JWT encoding/decoding
- `passlib[bcrypt]` - Password hashing utilities
- `pytest` - Testing framework
- `pytest-cov` - Test coverage reporting

## Contributing

When contributing to this project:

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for all classes and public methods
4. Include unit tests for new functionality
5. Keep functions under 30 lines where possible
6. Never commit secrets or API keys

## License

This implementation is part of the Synpro Virtual Dev Team project.
