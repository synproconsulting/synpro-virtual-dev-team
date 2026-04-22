# JWT Token Generation and Validation Module

This module provides a complete implementation of JSON Web Token (JWT) generation and validation for authentication and authorization purposes.

## Features

- **Access Token Generation**: Create short-lived access tokens for API authentication
- **Refresh Token Generation**: Create long-lived refresh tokens for obtaining new access tokens
- **Token Validation**: Validate tokens with type checking and expiration handling
- **Token Decoding**: Extract and verify token payloads
- **Subject Extraction**: Retrieve user identifiers from tokens
- **Token Refresh**: Generate new access tokens from valid refresh tokens

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The JWT handler requires a secret key for signing tokens. You can provide it in two ways:

1. **Environment Variable** (recommended):
   ```bash
   export SECRET_KEY="your-secret-key-here"
   ```

2. **Direct instantiation**:
   ```python
   from src.auth import JWTHandler
   
   handler = JWTHandler(secret_key="your-secret-key-here")
   ```

### Configuration Parameters

- `secret_key`: Secret key for signing tokens (required)
- `algorithm`: Algorithm for encoding/decoding (default: "HS256")
- `access_token_expire_minutes`: Expiration time for access tokens in minutes (default: 30)
- `refresh_token_expire_days`: Expiration time for refresh tokens in days (default: 7)

## Usage

### Basic Usage

```python
from src.auth import JWTHandler

# Initialize the handler
handler = JWTHandler(
    secret_key="your-secret-key",
    access_token_expire_minutes=30,
    refresh_token_expire_days=7
)

# Create an access token
access_token = handler.create_access_token(subject="user123")

# Create a refresh token
refresh_token = handler.create_refresh_token(subject="user123")

# Validate a token
is_valid = handler.validate_token(access_token)

# Decode a token
payload = handler.decode_token(access_token)
print(payload["sub"])  # Output: user123

# Get subject from token
subject = handler.get_token_subject(access_token)
print(subject)  # Output: user123
```

### Advanced Usage

#### Tokens with Additional Claims

```python
# Create access token with custom claims
access_token = handler.create_access_token(
    subject="user123",
    additional_claims={
        "role": "admin",
        "permissions": ["read", "write", "delete"]
    }
)

# Decode and use custom claims
payload = handler.decode_token(access_token)
print(payload["role"])  # Output: admin
print(payload["permissions"])  # Output: ["read", "write", "delete"]
```

#### Custom Token Expiration

```python
from datetime import timedelta

# Create access token with custom expiration
access_token = handler.create_access_token(
    subject="user123",
    expires_delta=timedelta(hours=2)
)
```

#### Token Type Validation

```python
# Validate token and check its type
is_valid_access = handler.validate_token(access_token, token_type="access")
is_valid_refresh = handler.validate_token(refresh_token, token_type="refresh")
```

#### Refresh Access Tokens

```python
# Generate a new access token from a refresh token
new_access_token = handler.refresh_access_token(refresh_token)

if new_access_token:
    print("New access token generated successfully")
else:
    print("Invalid or expired refresh token")
```

### Error Handling

```python
from jose import JWTError
from jose.exceptions import ExpiredSignatureError

try:
    payload = handler.decode_token(token)
    print(f"Token is valid for user: {payload['sub']}")
except ExpiredSignatureError:
    print("Token has expired")
except JWTError as e:
    print(f"Invalid token: {e}")
```

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/auth --cov-report=html

# Run specific test file
pytest tests/test_jwt_handler.py

# Run with verbose output
pytest -v
```

### Test Coverage

The test suite includes comprehensive tests for:
- Handler initialization and configuration
- Access token generation and validation
- Refresh token generation and validation
- Token decoding with valid and invalid tokens
- Token expiration handling
- Subject extraction
- Token refresh functionality
- Error scenarios and edge cases

## Security Considerations

1. **Secret Key**: Always use a strong, randomly generated secret key. Never commit it to version control.
2. **HTTPS Only**: Always transmit tokens over HTTPS in production.
3. **Token Storage**: Store tokens securely on the client side (e.g., httpOnly cookies for web apps).
4. **Expiration**: Use appropriate expiration times. Access tokens should be short-lived (15-30 minutes), refresh tokens longer (7-30 days).
5. **Token Revocation**: Implement token blacklisting or rotation for enhanced security.
6. **Algorithm**: The default HS256 algorithm is suitable for most use cases. Use RS256 for distributed systems.

## Architecture

```
src/
└── auth/
    ├── __init__.py          # Package exports
    └── jwt_handler.py       # Main JWT handler implementation

tests/
├── __init__.py              # Test package
└── test_jwt_handler.py      # Comprehensive test suite

requirements.txt             # Project dependencies
README.md                    # This file
```

## API Reference

### JWTHandler Class

#### `__init__(secret_key, algorithm, access_token_expire_minutes, refresh_token_expire_days)`
Initialize the JWT handler with configuration.

#### `create_access_token(subject, additional_claims, expires_delta) -> str`
Create a JWT access token.

#### `create_refresh_token(subject, additional_claims, expires_delta) -> str`
Create a JWT refresh token.

#### `decode_token(token) -> Dict[str, Any]`
Decode and validate a JWT token. Raises `JWTError` or `ExpiredSignatureError` if invalid.

#### `validate_token(token, token_type) -> bool`
Validate a JWT token, optionally checking its type.

#### `get_token_subject(token) -> Optional[str]`
Extract the subject from a token. Returns `None` if invalid.

#### `refresh_access_token(refresh_token) -> Optional[str]`
Generate a new access token from a valid refresh token.

## Dependencies

- **python-jose[cryptography]**: JWT encoding/decoding with cryptographic support
- **pytest**: Testing framework
- **pytest-cov**: Code coverage reporting
- **mypy**: Static type checking (optional)

## License

This module is part of the SDT1 project.

## Contributing

When contributing to this module:
1. Ensure all tests pass
2. Add tests for new functionality
3. Follow the existing code style
4. Update documentation as needed
5. Use type hints for all functions
