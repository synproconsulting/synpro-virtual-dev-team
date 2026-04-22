# Password Reset Request Module

## Overview

This module provides a complete password reset request functionality for Python applications. It includes secure token generation, email delivery, and token validation with expiration handling.

## Features

- **Secure Token Generation**: Uses cryptographically secure random tokens (32-byte URL-safe tokens)
- **Email Notifications**: Sends HTML and plain text password reset emails via SMTP
- **Token Expiration**: Configurable token expiration time (default: 1 hour)
- **Token Validation**: Validates tokens and prevents reuse
- **In-Memory Storage**: Token storage (easily replaceable with database/Redis in production)

## Architecture

### Components

1. **PasswordResetToken**: Data class representing a reset token with metadata
2. **TokenStorage**: In-memory storage for managing tokens
3. **EmailService**: SMTP-based email delivery service
4. **PasswordResetService**: Main service orchestrating the reset flow

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The module uses environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP authentication username | `""` |
| `SMTP_PASSWORD` | SMTP authentication password | `""` |
| `FROM_EMAIL` | Email address to send from | Same as `SMTP_USER` |
| `TOKEN_EXPIRY_HOURS` | Token expiration time in hours | `1` |

### Example .env file

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourdomain.com
TOKEN_EXPIRY_HOURS=1
```

## Usage

### Basic Usage

```python
from src.auth.password_reset import create_password_reset_service

# Create service instance
service = create_password_reset_service()

# Request password reset
result = service.request_password_reset(
    user_email="user@example.com",
    reset_url_base="https://yourapp.com/reset-password"
)

if result["success"]:
    print("Reset email sent successfully")
else:
    print(f"Error: {result['message']}")
```

### Validating a Reset Token

```python
# Validate token when user clicks the reset link
validation_result = service.validate_reset_token(token)

if validation_result["valid"]:
    user_email = validation_result["user_email"]
    # Proceed with password reset
    # ...
    # Mark token as used
    service.mark_token_used(token)
else:
    print(f"Invalid token: {validation_result['message']}")
```

### Advanced Usage with Custom Configuration

```python
from src.auth.password_reset import (
    TokenStorage,
    EmailService,
    PasswordResetService
)

# Create custom instances
token_storage = TokenStorage()
email_service = EmailService(
    smtp_host="smtp.example.com",
    smtp_port=587,
    smtp_user="user@example.com",
    smtp_password="password",
    from_email="noreply@example.com"
)

service = PasswordResetService(
    token_storage=token_storage,
    email_service=email_service,
    token_expiry_hours=2  # 2-hour expiration
)
```

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/auth --cov-report=html

# Run specific test file
pytest tests/test_password_reset.py

# Run with verbose output
pytest tests/ -v
```

### Test Coverage

The module includes comprehensive unit tests covering:
- Token generation and validation
- Token storage operations
- Email sending (mocked)
- Service integration
- Error handling
- Edge cases (expired tokens, invalid emails, etc.)

## Security Considerations

### Production Deployment

1. **Replace In-Memory Storage**: Use a database (PostgreSQL, MySQL) or Redis for token storage
2. **Environment Variables**: Never commit SMTP credentials to version control
3. **HTTPS Only**: Ensure reset URLs use HTTPS in production
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **User Verification**: Verify that the email address exists before sending reset emails
6. **Logging**: Add secure logging (don't log tokens or passwords)

### Token Security

- Tokens are 32-byte URL-safe strings (43 characters)
- Tokens are cryptographically secure (using `secrets` module)
- Tokens expire after configurable time (default: 1 hour)
- Tokens are single-use (marked as used after password reset)

## Email Templates

The module sends both HTML and plain text versions of the reset email. The templates include:
- Clear reset instructions
- Clickable reset link
- Expiration notice
- Security warning for unsolicited emails

## API Reference

### PasswordResetService

#### `request_password_reset(user_email: str, reset_url_base: str) -> Dict[str, Any]`

Request a password reset for the given email address.

**Parameters:**
- `user_email`: Email address of the user
- `reset_url_base`: Base URL for the reset page (token will be appended)

**Returns:**
```python
{
    "success": bool,
    "message": str,
    "token": str  # Only in development, remove in production
}
```

#### `validate_reset_token(token: str) -> Dict[str, Any]`

Validate a password reset token.

**Returns:**
```python
{
    "valid": bool,
    "user_email": str,  # If valid
    "message": str
}
```

#### `mark_token_used(token: str) -> bool`

Mark a token as used after successful password reset.

## Error Handling

The module handles various error scenarios:
- Invalid email addresses
- SMTP connection failures
- Expired tokens
- Already-used tokens
- Non-existent tokens

All errors are returned as structured responses with clear messages.

## Integration Example

```python
from flask import Flask, request, jsonify
from src.auth.password_reset import create_password_reset_service

app = Flask(__name__)
service = create_password_reset_service()

@app.route('/api/auth/request-reset', methods=['POST'])
def request_reset():
    data = request.get_json()
    email = data.get('email')
    
    result = service.request_password_reset(
        user_email=email,
        reset_url_base="https://yourapp.com/reset-password"
    )
    
    return jsonify(result)

@app.route('/api/auth/validate-token', methods=['POST'])
def validate_token():
    data = request.get_json()
    token = data.get('token')
    
    result = service.validate_reset_token(token)
    return jsonify(result)
```

## License

This module is part of the SDT1 project.

## Support

For issues or questions, please contact the development team.
