# User Registration Module

A production-ready Python user registration system with comprehensive email and password validation.

## Features

- **Email Validation**
  - RFC 5322 compliant email format validation
  - Duplicate email detection
  - Case-insensitive email storage
  - Maximum length enforcement (254 characters)

- **Password Validation**
  - Configurable minimum length (default: 8 characters)
  - Maximum length enforcement (default: 128 characters)
  - Requires uppercase letter
  - Requires lowercase letter
  - Requires digit
  - Requires special character
  - Comprehensive validation error messages

- **Security**
  - Bcrypt password hashing with automatic salt generation
  - Environment variable configuration for password requirements
  - No hardcoded secrets or credentials
  - Password hashes never returned in API responses

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

You can customize password requirements using environment variables:

- `MIN_PASSWORD_LENGTH` - Minimum password length (default: 8)
- `MAX_PASSWORD_LENGTH` - Maximum password length (default: 128)

## Usage

### Basic Registration

```python
from src.auth.registration import register_user, ValidationError

try:
    user = register_user(
        email="user@example.com",
        password="SecurePass123!"
    )
    print(f"User registered: {user['email']}")
except ValidationError as e:
    print(f"Registration failed: {e}")
```

### Using the UserRegistration Class

```python
from src.auth.registration import UserRegistration, ValidationError

registration = UserRegistration()

# Register a user
try:
    user = registration.register(
        email="user@example.com",
        password="SecurePass123!",
        additional_data={"first_name": "John", "last_name": "Doe"}
    )
    print(f"User created at: {user['created_at']}")
except ValidationError as e:
    print(f"Error: {e}")

# Retrieve a user
user_data = registration.get_user("user@example.com")
if user_data:
    print(f"Found user: {user_data['email']}")
```

### Password Verification

```python
from src.auth.registration import UserRegistration

registration = UserRegistration()

# Register user
registration.register("user@example.com", "SecurePass123!")

# Get user and verify password
user = registration.get_user("user@example.com")
is_valid = registration.verify_password("SecurePass123!", user['password_hash'])
print(f"Password valid: {is_valid}")
```

## Running Tests

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/auth --cov-report=html

# Run specific test file
pytest tests/test_registration.py

# Run with verbose output
pytest -v
```

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py
│       └── registration.py
├── tests/
│   ├── __init__.py
│   └── test_registration.py
├── requirements.txt
└── README.md
```

## API Reference

### `UserRegistration`

Main class for handling user registration.

#### Methods

- **`validate_email(email: str) -> Tuple[bool, Optional[str]]`**
  - Validates email format and checks for duplicates
  - Returns: (is_valid, error_message)

- **`validate_password(password: str) -> Tuple[bool, Optional[str]]`**
  - Validates password strength requirements
  - Returns: (is_valid, error_message)

- **`hash_password(password: str) -> str`**
  - Hashes a password using bcrypt
  - Returns: Hashed password string

- **`verify_password(plain_password: str, hashed_password: str) -> bool`**
  - Verifies a password against its hash
  - Returns: True if password matches, False otherwise

- **`register(email: str, password: str, additional_data: Optional[Dict] = None) -> Dict`**
  - Registers a new user
  - Returns: User data dictionary (without password hash)
  - Raises: ValidationError if validation fails

- **`get_user(email: str) -> Optional[Dict]`**
  - Retrieves user by email
  - Returns: User data or None if not found

### `register_user()`

Convenience function for quick user registration.

```python
def register_user(
    email: str, 
    password: str,
    additional_data: Optional[Dict] = None
) -> Dict
```

## Password Requirements

Passwords must meet the following criteria:

1. Minimum 8 characters (configurable)
2. Maximum 128 characters (configurable)
3. At least one uppercase letter (A-Z)
4. At least one lowercase letter (a-z)
5. At least one digit (0-9)
6. At least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\/`~;)

## Email Requirements

Emails must:

1. Follow RFC 5322 format (simplified)
2. Be no longer than 254 characters
3. Be unique (case-insensitive)
4. Contain @ symbol with valid domain

## Error Handling

The module raises `ValidationError` for any validation failures:

```python
from src.auth.registration import ValidationError

try:
    register_user("invalid-email", "weak")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## Security Considerations

- Passwords are hashed using bcrypt with automatic salt generation
- Password hashes are never exposed in API responses
- Email addresses are stored in lowercase for consistency
- No sensitive data is logged or exposed
- Environment variables are used for configuration
- Input validation prevents common attack vectors

## License

This module is part of the Synpro Virtual Dev Team project.

## Contributing

1. Write clean, type-hinted Python code
2. Add comprehensive tests for new features
3. Update documentation as needed
4. Follow PEP 8 style guidelines
