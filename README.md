# Password Reset Completion Module

A secure, production-ready Python implementation for completing password reset flows with JWT token validation and bcrypt password hashing.

## Features

- ✅ Secure JWT token-based password reset validation
- ✅ Industry-standard bcrypt password hashing
- ✅ Strong password validation requirements
- ✅ Token expiration handling
- ✅ Comprehensive error handling
- ✅ Type hints throughout
- ✅ Fully tested with pytest

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

Set the following environment variable:

```bash
export JWT_SECRET_KEY="your-secure-secret-key-here"
```

**⚠️ Important:** Never commit your actual secret key to version control. Use a secure key management system in production.

## Usage

### Basic Usage

```python
from src.auth import PasswordResetCompletionService, PasswordResetRequest

# Initialize the service
service = PasswordResetCompletionService()

# Define a callback to update the user's password in your database
def update_user_password(user_id: str, hashed_password: str) -> bool:
    # Your database update logic here
    # Example: db.users.update_one({'id': user_id}, {'$set': {'password': hashed_password}})
    return True

# Complete the password reset
request = PasswordResetRequest(
    token="user-reset-token-from-email",
    new_password="NewSecurePassword123"
)

response = service.complete_password_reset(request, update_user_password)

if response.success:
    print(f"Password reset successful for {response.email}")
else:
    print(f"Password reset failed: {response.message}")
```

### Generating Reset Tokens

```python
# Generate a password reset token (typically done when user requests reset)
token = service.generate_reset_token(
    user_id="user123",
    email="user@example.com"
)

# Send this token to the user via email
# The token expires after 24 hours by default
```

### Custom Token Expiry

```python
# Set custom expiry (in hours)
service = PasswordResetCompletionService(
    secret_key="your-secret-key",
    token_expiry_hours=2  # Token expires in 2 hours
)
```

## Password Requirements

The module enforces the following password requirements:

- Minimum 8 characters long
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## API Reference

### `PasswordResetCompletionService`

Main service class for handling password reset completion.

**Methods:**

- `generate_reset_token(user_id: str, email: str) -> str`
  - Generates a JWT reset token for a user
  
- `verify_reset_token(token: str) -> Dict[str, Any]`
  - Verifies and decodes a reset token
  
- `hash_password(password: str) -> str`
  - Hashes a password using bcrypt
  
- `complete_password_reset(request: PasswordResetRequest, update_callback: callable) -> PasswordResetResponse`
  - Completes the password reset process

### `PasswordResetRequest`

Pydantic model for password reset requests.

**Fields:**
- `token: str` - The JWT reset token
- `new_password: str` - The new password (validated)

### `PasswordResetResponse`

Pydantic model for password reset responses.

**Fields:**
- `success: bool` - Whether the operation succeeded
- `message: str` - Human-readable result message
- `email: Optional[EmailStr]` - User's email (on success)

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/auth --cov-report=html

# Run specific test file
pytest tests/test_password_reset_completion.py

# Run with verbose output
pytest -v
```

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py
│       └── password_reset_completion.py
├── tests/
│   ├── __init__.py
│   └── test_password_reset_completion.py
├── requirements.txt
└── README.md
```

## Security Considerations

1. **Secret Key Management**: Never hardcode the JWT secret key. Use environment variables or a secure key management service.

2. **HTTPS Only**: Always transmit reset tokens over HTTPS in production.

3. **Token Expiry**: Reset tokens expire after 24 hours by default. Adjust based on your security requirements.

4. **Password Hashing**: Uses bcrypt with automatic salt generation for secure password storage.

5. **Password Validation**: Enforces strong password requirements to prevent weak passwords.

6. **Single Use Tokens**: Implement token invalidation after use in your database layer.

## Error Handling

The service handles various error scenarios gracefully:

- Expired tokens
- Invalid tokens
- Malformed tokens
- Weak passwords
- Database update failures

All errors return a `PasswordResetResponse` with `success=False` and a descriptive message.

## Example Integration

### With FastAPI

```python
from fastapi import FastAPI, HTTPException
from src.auth import PasswordResetCompletionService, PasswordResetRequest

app = FastAPI()
service = PasswordResetCompletionService()

@app.post("/auth/reset-password/complete")
async def complete_reset(request: PasswordResetRequest):
    def update_password(user_id: str, hashed_password: str) -> bool:
        # Your database logic
        return True
    
    response = service.complete_password_reset(request, update_password)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    
    return {"message": response.message, "email": response.email}
```

### With Flask

```python
from flask import Flask, request, jsonify
from src.auth import PasswordResetCompletionService, PasswordResetRequest

app = Flask(__name__)
service = PasswordResetCompletionService()

@app.route('/auth/reset-password/complete', methods=['POST'])
def complete_reset():
    data = request.get_json()
    
    reset_request = PasswordResetRequest(**data)
    
    def update_password(user_id: str, hashed_password: str) -> bool:
        # Your database logic
        return True
    
    response = service.complete_password_reset(reset_request, update_password)
    
    if not response.success:
        return jsonify({"error": response.message}), 400
    
    return jsonify({
        "message": response.message,
        "email": response.email
    })
```

## License

Copyright © 2024 SynPro Consulting. All rights reserved.

## Support

For issues or questions, please contact the development team or create an issue in the repository.
