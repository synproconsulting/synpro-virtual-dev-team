# User Registration Module

A robust Python module for user registration with comprehensive email and password validation.

## Features

- ✅ **Email Validation**: Uses Pydantic's `EmailStr` for RFC-compliant email validation
- ✅ **Password Strength Validation**: Configurable requirements for password complexity
- ✅ **Secure Password Hashing**: Uses bcrypt via passlib for industry-standard password security
- ✅ **Password Confirmation**: Ensures passwords match before registration
- ✅ **Duplicate Prevention**: Checks for existing users with case-insensitive email comparison
- ✅ **Type Safety**: Full type hints for better IDE support and type checking
- ✅ **Comprehensive Testing**: 100% test coverage with pytest

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from src.auth import UserRegistrationService, RegistrationError

# Create a registration service instance
service = UserRegistrationService()

# Register a new user
try:
    user = service.register_user(
        email="john.doe@example.com",
        password="SecurePass123!",
        confirm_password="SecurePass123!",
        full_name="John Doe"
    )
    print(f"User registered successfully: {user.email}")
except RegistrationError as e:
    print(f"Registration failed: {e}")
```

## Password Requirements

By default, passwords must meet the following criteria:

- Minimum 8 characters long
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*(),.?":{}|<>)

### Custom Password Requirements

You can customize password requirements:

```python
from src.auth import UserRegistrationService, PasswordRequirements

# Define custom requirements
custom_reqs = PasswordRequirements(
    min_length=10,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_special=False  # Don't require special characters
)

# Create service with custom requirements
service = UserRegistrationService(password_requirements=custom_reqs)
```

## API Reference

### `UserRegistrationService`

Main service class for handling user registration.

#### Methods

**`register_user(email: str, password: str, confirm_password: str, full_name: Optional[str] = None) -> User`**

Register a new user with validation.

- **Parameters:**
  - `email`: User's email address
  - `password`: User's password
  - `confirm_password`: Password confirmation (must match password)
  - `full_name`: Optional full name of the user

- **Returns:** `User` object with hashed password

- **Raises:** `RegistrationError` if validation fails or user already exists

**`validate_password_strength(password: str) -> Tuple[bool, str]`**

Validate password against strength requirements.

- **Returns:** Tuple of (is_valid, error_message)

**`hash_password(password: str) -> str`**

Hash a password using bcrypt.

**`verify_password(plain_password: str, hashed_password: str) -> bool`**

Verify a password against its hash.

**`user_exists(email: str) -> bool`**

Check if a user with the given email already exists.

**`get_user_by_email(email: str) -> Optional[User]`**

Retrieve a user by email address.

### Models

**`User`**
- `email`: EmailStr - User's email address
- `hashed_password`: str - Bcrypt hashed password
- `full_name`: Optional[str] - User's full name
- `is_active`: bool - Account active status (default: True)

**`UserRegistrationInput`**
- `email`: EmailStr - User's email address
- `password`: str - User's password
- `confirm_password`: str - Password confirmation
- `full_name`: Optional[str] - User's full name

**`PasswordRequirements`**
- `min_length`: int - Minimum password length (default: 8)
- `require_uppercase`: bool - Require uppercase letters (default: True)
- `require_lowercase`: bool - Require lowercase letters (default: True)
- `require_digit`: bool - Require digits (default: True)
- `require_special`: bool - Require special characters (default: True)

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_user_registration.py

# Run with verbose output
pytest -v
```

## Test Coverage

The module includes comprehensive tests covering:

- ✅ Email validation (valid/invalid formats)
- ✅ Password strength validation (all requirements)
- ✅ Password matching validation
- ✅ Password hashing and verification
- ✅ User registration flow
- ✅ Duplicate user prevention
- ✅ Case-insensitive email handling
- ✅ Custom password requirements
- ✅ User retrieval functionality

## Security Considerations

1. **Password Hashing**: Uses bcrypt with automatic salt generation
2. **No Plain Text Storage**: Passwords are never stored in plain text
3. **Environment Variables**: Configure any external services via environment variables
4. **Case-Insensitive Emails**: Prevents duplicate registrations with different cases
5. **Validation Before Processing**: All input is validated before any processing occurs

## Architecture

```
src/auth/
├── __init__.py                 # Package exports
└── user_registration.py        # Main registration logic

tests/
├── __init__.py
└── test_user_registration.py   # Comprehensive test suite
```

## Dependencies

- **passlib[bcrypt]**: Password hashing with bcrypt
- **pydantic[email]**: Data validation and email validation
- **pytest**: Testing framework
- **pytest-cov**: Test coverage reporting

## Future Enhancements

Potential improvements for production use:

- Database integration (PostgreSQL, MongoDB, etc.)
- Email verification flow
- Rate limiting for registration attempts
- CAPTCHA integration
- OAuth/Social login integration
- Account recovery mechanisms
- Audit logging
- Multi-factor authentication (MFA)

## License

This module is part of the SDT1-7 project.

## Support

For issues or questions, please contact the development team.
