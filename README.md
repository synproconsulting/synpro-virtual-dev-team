# User Registration Module

## Overview

This module provides a comprehensive user registration system with email and password validation. It includes secure password hashing using bcrypt and robust validation for both email addresses and passwords.

## Features

- **Email Validation**: Validates email format and normalizes addresses
- **Password Strength Validation**: Enforces strong password requirements
- **Secure Password Hashing**: Uses bcrypt for secure password storage
- **User Storage**: In-memory user storage with support for custom stores
- **Duplicate Prevention**: Prevents registration of duplicate email addresses
- **Type Safety**: Full type hints for all functions

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Password Requirements

Passwords must meet the following criteria:

- Minimum length: 8 characters (configurable via `MIN_PASSWORD_LENGTH` environment variable)
- Maximum length: 128 characters (configurable via `MAX_PASSWORD_LENGTH` environment variable)
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\/`~;)

## Email Requirements

- Must be a valid email format
- Email addresses are normalized (lowercase domain)
- Case-insensitive lookup

## Usage

### Basic Registration

```python
from src.auth import UserRegistration

# Create registration service
registration = UserRegistration()

# Register a new user
try:
    user = registration.register_user(
        email="user@example.com",
        password="SecurePass123!",
        username="johndoe"  # optional
    )
    print(f"User registered: {user['email']}")
except Exception as e:
    print(f"Registration failed: {e}")
```

### Custom User Store

```python
# Use a custom dictionary for user storage
user_store = {}
registration = UserRegistration(user_store=user_store)

user = registration.register_user(
    email="user@example.com",
    password="SecurePass123!"
)
```

### Retrieve User

```python
user = registration.get_user("user@example.com")
if user:
    print(f"Found user: {user['username']}")
else:
    print("User not found")
```

### Password Verification

```python
# Verify a password against stored hash
stored_user = registration.user_store["user@example.com"]
is_valid = registration.verify_password(
    "SecurePass123!",
    stored_user['password_hash']
)
```

## API Reference

### UserRegistration Class

#### `__init__(user_store: Optional[Dict] = None)`
Initialize the registration service with an optional custom user store.

#### `validate_email(email: str) -> str`
Validate and normalize an email address.

**Raises:**
- `EmailValidationError`: If email is invalid

#### `validate_password(password: str) -> None`
Validate password against strength requirements.

**Raises:**
- `PasswordValidationError`: If password doesn't meet requirements

#### `register_user(email: str, password: str, username: Optional[str] = None) -> Dict`
Register a new user.

**Returns:** Dictionary with user information (excluding password hash)

**Raises:**
- `EmailValidationError`: If email is invalid
- `PasswordValidationError`: If password is weak
- `UserAlreadyExistsError`: If user already exists

#### `get_user(email: str) -> Optional[Dict]`
Retrieve user by email address.

**Returns:** User dictionary or None if not found

#### `verify_password(plain_password: str, hashed_password: str) -> bool`
Verify a password against its hash.

## Exception Classes

- `EmailValidationError`: Raised when email validation fails
- `PasswordValidationError`: Raised when password validation fails
- `UserAlreadyExistsError`: Raised when attempting to register duplicate user

## Environment Variables

- `MIN_PASSWORD_LENGTH`: Minimum password length (default: 8)
- `MAX_PASSWORD_LENGTH`: Maximum password length (default: 128)

## Testing

Run tests using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/auth --cov-report=html

# Run specific test file
pytest tests/test_user_registration.py

# Run with verbose output
pytest -v
```

## Test Coverage

The module includes comprehensive unit tests covering:

- Email validation (valid/invalid formats, normalization)
- Password validation (all requirements)
- Password hashing and verification
- User registration (successful, duplicates, edge cases)
- User retrieval
- Custom user stores
- Case-insensitive email handling

## Security Considerations

1. **Password Hashing**: Passwords are hashed using bcrypt with automatic salt generation
2. **No Plain Text Storage**: Passwords are never stored in plain text
3. **Password Hash Exclusion**: User retrieval methods never return password hashes
4. **Environment Variables**: Sensitive configuration via environment variables
5. **Input Validation**: All inputs are validated before processing

## Example Application

```python
from src.auth import UserRegistration, UserAlreadyExistsError

def main():
    registration = UserRegistration()
    
    # Register users
    users_to_register = [
        ("alice@example.com", "AlicePass123!", "alice"),
        ("bob@example.com", "BobSecure456#", "bob"),
    ]
    
    for email, password, username in users_to_register:
        try:
            user = registration.register_user(email, password, username)
            print(f"✓ Registered: {user['username']} ({user['email']})")
        except UserAlreadyExistsError:
            print(f"✗ User {email} already exists")
        except Exception as e:
            print(f"✗ Registration failed: {e}")
    
    # Retrieve and display users
    print("\nRegistered Users:")
    for email, _, _ in users_to_register:
        user = registration.get_user(email)
        if user:
            print(f"  - {user['username']}: {user['email']}")

if __name__ == "__main__":
    main()
```

## License

This module is part of the SDT1-7 project.

## Contributing

Please ensure all tests pass before submitting changes:

```bash
pytest tests/
```

Follow PEP 8 style guidelines and include type hints for all functions.
