# User Registration Module

A production-ready user registration system with email and password validation, built with Python 3.11+.

## Features

- ✅ **Email Validation**: RFC 5322 compliant email validation
- ✅ **Strong Password Requirements**: 
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
- ✅ **Secure Password Hashing**: Uses bcrypt via passlib
- ✅ **User Management**: In-memory storage (easily replaceable with database)
- ✅ **Credential Verification**: Built-in login verification
- ✅ **Comprehensive Tests**: Full pytest test suite

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Registration

```python
from src.auth.registration import UserRegistration

# Initialize the registration service
registration = UserRegistration()

# Register a new user
success, message, user = registration.register_user(
    email="user@example.com",
    password="SecurePass123!"
)

if success:
    print(f"User registered: {user.email}")
    print(f"User ID: {user.id}")
else:
    print(f"Registration failed: {message}")
```

### Strict Mode (Raises Exceptions)

```python
from src.auth.registration import UserRegistration, RegistrationError

registration = UserRegistration()

try:
    user = registration.register_user_strict(
        email="user@example.com",
        password="SecurePass123!"
    )
    print(f"User registered: {user.email}")
except RegistrationError as e:
    print(f"Registration failed: {e}")
```

### Verify Credentials

```python
from src.auth.registration import UserRegistration

registration = UserRegistration()

# Register a user first
registration.register_user("user@example.com", "SecurePass123!")

# Verify credentials for login
is_valid, user = registration.verify_credentials(
    email="user@example.com",
    password="SecurePass123!"
)

if is_valid:
    print(f"Login successful for {user.email}")
else:
    print("Invalid credentials")
```

### Standalone Validators

```python
from src.auth.validators import EmailValidator, PasswordValidator

# Validate email
is_valid, error = EmailValidator.validate("user@example.com")
if not is_valid:
    print(f"Email error: {error}")

# Validate password
is_valid, error = PasswordValidator.validate("SecurePass123!")
if not is_valid:
    print(f"Password error: {error}")
```

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py           # Module exports
│       ├── models.py             # User data model
│       ├── validators.py         # Email and password validators
│       ├── password_hasher.py    # Password hashing utilities
│       ├── storage.py            # User storage (in-memory)
│       └── registration.py       # Main registration service
├── tests/
│   ├── __init__.py
│   ├── test_models.py            # User model tests
│   ├── test_validators.py        # Validator tests
│   ├── test_password_hasher.py   # Password hasher tests
│   ├── test_storage.py           # Storage tests
│   └── test_registration.py      # Registration service tests
├── requirements.txt              # Project dependencies
└── README.md                     # This file
```

## Running Tests

Run the full test suite:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=src/auth --cov-report=html
```

Run specific test file:

```bash
pytest tests/test_registration.py
```

## Password Requirements

Passwords must meet the following criteria:

- **Length**: 8-128 characters
- **Uppercase**: At least one uppercase letter (A-Z)
- **Lowercase**: At least one lowercase letter (a-z)
- **Digit**: At least one number (0-9)
- **Special Character**: At least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\/;`~)

## Email Validation

Emails are validated against:

- Basic RFC 5322 format compliance
- Maximum length of 254 characters
- Valid domain structure
- Proper character usage

Emails are normalized to lowercase for storage and lookups.

## Security Features

1. **Bcrypt Password Hashing**: Uses industry-standard bcrypt algorithm with cost factor 12
2. **Salted Hashes**: Each password hash includes a unique salt
3. **No Plaintext Storage**: Passwords are never stored in plaintext
4. **Case-Insensitive Email Lookup**: Prevents duplicate accounts with different casing
5. **Input Validation**: All inputs are validated before processing

## Production Considerations

This implementation uses in-memory storage for simplicity. For production deployment:

1. **Replace UserStorage**: Implement database storage (PostgreSQL, MongoDB, etc.)
2. **Add Email Verification**: Send verification emails to confirm email ownership
3. **Rate Limiting**: Implement rate limiting to prevent brute force attacks
4. **Logging**: Add comprehensive logging for security auditing
5. **Environment Variables**: Configure bcrypt rounds and other settings via environment
6. **Session Management**: Implement JWT or session-based authentication
7. **Account Recovery**: Add password reset functionality

## API Reference

### UserRegistration

Main service class for user registration.

**Methods:**

- `register_user(email: str, password: str) -> Tuple[bool, str, Optional[User]]`
  - Register a new user
  - Returns: (success, message, user)

- `register_user_strict(email: str, password: str) -> User`
  - Register a new user (raises RegistrationError on failure)
  - Returns: User object

- `get_user_by_email(email: str) -> Optional[User]`
  - Retrieve user by email address
  - Returns: User object or None

- `verify_credentials(email: str, password: str) -> Tuple[bool, Optional[User]]`
  - Verify login credentials
  - Returns: (is_valid, user)

### EmailValidator

Static validator for email addresses.

**Methods:**

- `validate(email: str) -> Tuple[bool, str]`
  - Returns: (is_valid, error_message)

### PasswordValidator

Static validator for passwords.

**Methods:**

- `validate(password: str) -> Tuple[bool, str]`
  - Returns: (is_valid, error_message)

### PasswordHasher

Password hashing and verification.

**Methods:**

- `hash_password(password: str) -> str`
  - Returns: Hashed password string

- `verify_password(plaintext: str, hashed: str) -> bool`
  - Returns: True if password matches

## License

This module is part of the SDT1-7 project implementation.

## Author

Backend Developer - Virtual Development Team
