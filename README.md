# Authentication Module

This module provides secure user registration functionality with password hashing and validation for Python applications.

## Features

- **User Registration**: Register new users with username, email, and password
- **Email Validation**: Validates email format using regex patterns
- **Password Strength Validation**: Enforces strong password requirements
- **Secure Password Hashing**: Uses bcrypt for secure password storage
- **Password Verification**: Verify passwords against stored hashes

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Register a New User

```python
from src.auth import register_user, RegistrationError

try:
    user = register_user(
        username="johndoe",
        email="john@example.com",
        password="SecurePass123"
    )
    print(f"User registered: {user}")
except RegistrationError as e:
    print(f"Registration failed: {e}")
```

### Validate Email

```python
from src.auth import validate_email

is_valid = validate_email("user@example.com")
print(f"Email valid: {is_valid}")
```

### Validate Password Strength

```python
from src.auth import validate_password

is_strong = validate_password("MyPassword123")
print(f"Password meets requirements: {is_strong}")
```

### Hash and Verify Passwords

```python
from src.auth import hash_password, verify_password

# Hash a password
hashed = hash_password("MyPassword123")

# Verify a password
is_correct = verify_password("MyPassword123", hashed)
print(f"Password verified: {is_correct}")
```

## Password Requirements

Passwords must meet the following criteria:
- Minimum 8 characters long
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)

## Username Requirements

- Minimum 3 characters
- Maximum 50 characters

## Email Requirements

- Valid email format (e.g., user@example.com)

## Running Tests

Execute the test suite using pytest:

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

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py
│       └── user_registration.py
├── tests/
│   ├── __init__.py
│   └── test_user_registration.py
├── requirements.txt
└── README.md
```

## Dependencies

- **passlib**: Password hashing library with bcrypt support
- **pytest**: Testing framework
- **pytest-cov**: Code coverage plugin for pytest

## API Reference

### `register_user(username: str, email: str, password: str) -> User`

Register a new user with validation.

**Parameters:**
- `username`: Desired username (3-50 characters)
- `email`: User's email address
- `password`: Plain text password

**Returns:** User object with hashed password

**Raises:** `RegistrationError` if validation fails

### `validate_email(email: str) -> bool`

Validate email format.

**Parameters:**
- `email`: Email address to validate

**Returns:** True if email format is valid, False otherwise

### `validate_password(password: str) -> bool`

Validate password strength.

**Parameters:**
- `password`: Password to validate

**Returns:** True if password meets requirements, False otherwise

### `hash_password(password: str) -> str`

Hash a password using bcrypt.

**Parameters:**
- `password`: Plain text password

**Returns:** Hashed password string

### `verify_password(plain_password: str, hashed_password: str) -> bool`

Verify a password against its hash.

**Parameters:**
- `plain_password`: Plain text password
- `hashed_password`: Hashed password to verify against

**Returns:** True if password matches, False otherwise

## Security Notes

- Passwords are hashed using bcrypt with automatic salt generation
- Never store plain text passwords
- Each password hash is unique due to automatic salting
- The bcrypt algorithm is intentionally slow to prevent brute-force attacks

## License

This module is part of the SynPro Virtual Dev Team project.
