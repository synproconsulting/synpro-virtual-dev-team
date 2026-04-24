# User Authentication Module

This is a complete implementation of a user authentication system with secure registration, password hashing, and validation.

## Features

- **User Registration**: Create new user accounts with validation
- **Email Validation**: Ensure email addresses are in valid format
- **Password Strength**: Enforce strong password requirements
- **Secure Hashing**: Use bcrypt for password hashing
- **User Verification**: Check credentials and user existence

## Requirements

- Python 3.11+
- See `requirements.txt` for dependencies

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Registration

```python
from src.auth.register import UserRegistration

# Create registration service
registration = UserRegistration()

# Register a new user
try:
    user = registration.register_user(
        username="johndoe",
        email="john@example.com",
        password="SecurePass123"
    )
    print(f"User {user['username']} registered successfully!")
except RegistrationError as e:
    print(f"Registration failed: {e}")
```

### Password Verification

```python
# Verify user credentials
is_valid = registration.verify_password("johndoe", "SecurePass123")
if is_valid:
    print("Login successful!")
else:
    print("Invalid credentials")
```

### Check User Existence

```python
# Check if a user exists
exists = registration.user_exists("johndoe")
print(f"User exists: {exists}")
```

## Password Requirements

- Minimum 8 characters (configurable via `MIN_PASSWORD_LENGTH` environment variable)
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## Email Validation

Email addresses must follow standard format: `username@domain.extension`

## Environment Variables

- `MIN_PASSWORD_LENGTH`: Minimum password length (default: 8)

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_register.py
```

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py
│       └── register.py          # User registration implementation
├── tests/
│   ├── __init__.py
│   └── test_register.py         # Unit tests for registration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Security Notes

- Passwords are never stored in plain text
- Bcrypt hashing is used for secure password storage
- No hardcoded secrets - use environment variables
- Input validation prevents common security issues

## Error Handling

The module raises `RegistrationError` for validation failures:
- Username too short (< 3 characters)
- Username already exists
- Invalid email format
- Weak password

## License

MIT License
