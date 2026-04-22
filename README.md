# User Registration Module

A production-ready Python module for user registration with comprehensive email and password validation.

## Features

- **Email Validation**: RFC 5322 compliant email validation
- **Password Strength Validation**: Configurable password requirements including:
  - Minimum length
  - Uppercase letters
  - Lowercase letters
  - Digits
  - Special characters
- **Secure Password Hashing**: Uses bcrypt for industry-standard password hashing
- **Password Verification**: Built-in password verification against hashed passwords
- **Flexible Configuration**: Customizable validation rules to match your security requirements

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Registration

```python
from src.auth.registration import UserRegistration, RegistrationError

# Initialize registration handler
registration = UserRegistration()

# Register a new user
try:
    user_data = registration.register_user(
        email="user@example.com",
        password="SecureP@ss1",
        confirm_password="SecureP@ss1"
    )
    print(f"User registered: {user_data['email']}")
except RegistrationError as e:
    print(f"Registration failed: {e}")
```

### Custom Password Requirements

```python
# Create registration handler with custom requirements
registration = UserRegistration(
    min_password_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digits=True,
    require_special=True
)

user_data = registration.register_user(
    email="user@example.com",
    password="MyV3ryS3cur3P@ssword!"
)
```

### Registration with Additional Data

```python
# Register user with additional profile data
user_data = registration.register_user(
    email="user@example.com",
    password="SecureP@ss1",
    additional_data={
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890"
    }
)
```

### Email Validation Only

```python
# Validate email format
try:
    registration.validate_email("user@example.com")
    print("Email is valid")
except RegistrationError as e:
    print(f"Invalid email: {e}")
```

### Password Validation Only

```python
# Validate password strength
try:
    registration.validate_password("SecureP@ss1")
    print("Password meets requirements")
except RegistrationError as e:
    print(f"Weak password: {e}")
```

### Password Hashing and Verification

```python
# Hash a password
hashed_password = registration.hash_password("SecureP@ss1")

# Verify a password
is_valid = registration.verify_password("SecureP@ss1", hashed_password)
print(f"Password valid: {is_valid}")
```

## Configuration Options

The `UserRegistration` class accepts the following configuration parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_password_length` | int | 8 | Minimum required password length |
| `require_uppercase` | bool | True | Require at least one uppercase letter |
| `require_lowercase` | bool | True | Require at least one lowercase letter |
| `require_digits` | bool | True | Require at least one digit |
| `require_special` | bool | True | Require at least one special character |

## User Data Structure

The `register_user` method returns a dictionary with the following structure:

```python
{
    "email": "user@example.com",           # Normalized email (lowercase, trimmed)
    "password_hash": "$2b$12$...",         # Bcrypt hashed password
    "created_at": "2024-01-15T10:30:00",   # ISO format timestamp
    "is_active": True,                      # Account activation status
    # ... any additional data provided
}
```

## Error Handling

All validation errors raise `RegistrationError` with descriptive messages:

- `"Email is required"` - Empty email provided
- `"Invalid email format"` - Email doesn't match RFC 5322 format
- `"Email address is too long"` - Email exceeds 254 characters
- `"Password is required"` - Empty password provided
- `"Password must be at least X characters long"` - Password too short
- `"Password must contain at least one uppercase letter"` - Missing uppercase
- `"Password must contain at least one lowercase letter"` - Missing lowercase
- `"Password must contain at least one digit"` - Missing digit
- `"Password must contain at least one special character"` - Missing special character
- `"Passwords do not match"` - Password confirmation mismatch

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src/auth --cov-report=html

# Run specific test class
pytest tests/test_registration.py::TestEmailValidation

# Run specific test
pytest tests/test_registration.py::TestEmailValidation::test_valid_email
```

## Security Considerations

- **Password Storage**: Passwords are hashed using bcrypt with automatic salt generation
- **Email Normalization**: Emails are automatically converted to lowercase and trimmed
- **No Plain Text Storage**: Plain text passwords are never stored or logged
- **Configurable Strength**: Password requirements can be adjusted based on security needs
- **RFC Compliance**: Email validation follows RFC 5322 and RFC 5321 standards

## Module Structure

```
src/auth/
├── __init__.py           # Package initialization
└── registration.py       # Main registration logic

tests/
├── __init__.py          # Test package initialization
└── test_registration.py # Comprehensive test suite
```

## Dependencies

- **passlib[bcrypt]**: Password hashing library with bcrypt support
- **bcrypt**: Bcrypt hashing algorithm implementation
- **pytest**: Testing framework
- **pytest-cov**: Code coverage plugin for pytest

## License

This module is part of the SDT1-7 project.

## Development

### Adding New Validation Rules

Extend the `UserRegistration` class to add custom validation:

```python
class CustomRegistration(UserRegistration):
    def validate_password(self, password: str) -> bool:
        # Call parent validation
        super().validate_password(password)
        
        # Add custom rules
        if "password" in password.lower():
            raise RegistrationError("Password cannot contain the word 'password'")
        
        return True
```

### Integration with Database

The returned user data dictionary can be easily integrated with any database:

```python
# Example with SQLAlchemy
from sqlalchemy.orm import Session
from models import User

user_data = registration.register_user(email="user@example.com", password="SecureP@ss1")

# Create database record
db_user = User(**user_data)
db.add(db_user)
db.commit()
```

## Support

For issues, questions, or contributions, please contact the development team.
