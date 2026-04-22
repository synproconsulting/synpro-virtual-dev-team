# User Registration with Email and Password Validation

This module implements a secure user registration system with comprehensive email and password validation.

## Features

- **Email Validation**: RFC-compliant email validation with format, length, and structure checks
- **Password Validation**: Strong password requirements enforcing complexity rules
- **Secure Password Hashing**: Industry-standard bcrypt hashing via passlib
- **Extensible Storage**: Interface-based storage design supporting multiple backends
- **Comprehensive Testing**: Full pytest test coverage

## Password Requirements

Passwords must meet the following criteria:
- Minimum 8 characters, maximum 128 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\/;'`~)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Registration

```python
from src.auth.registration import UserRegistration

# Create registration service
registration = UserRegistration()

# Register a new user
try:
    user_data = registration.register_user(
        email="user@example.com",
        password="SecurePass123!"
    )
    print(f"User registered successfully: {user_data['user_id']}")
except RegistrationError as e:
    print(f"Registration failed: {e}")
```

### Validate Before Registration

```python
from src.auth.registration import UserRegistration

registration = UserRegistration()

# Validate registration data
validation = registration.validate_registration_data(
    email="user@example.com",
    password="SecurePass123!"
)

if validation["overall_valid"]:
    print("Data is valid, proceed with registration")
else:
    if not validation["email"]["valid"]:
        print(f"Email error: {validation['email']['error']}")
    if not validation["password"]["valid"]:
        print(f"Password error: {validation['password']['error']}")
```

### Custom Storage Implementation

```python
from src.auth.registration import UserRegistration
from src.auth.storage import UserStorageInterface

# Implement your own storage (e.g., database-backed)
class DatabaseUserStorage(UserStorageInterface):
    def save_user(self, user):
        # Your database logic here
        pass
    
    def get_user_by_email(self, email):
        # Your database logic here
        pass
    
    # ... implement other methods

# Use custom storage
storage = DatabaseUserStorage()
registration = UserRegistration(storage=storage)
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_registration.py
```

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py           # Module exports
│       ├── models.py             # User data models
│       ├── validators.py         # Email and password validation
│       ├── password_hasher.py    # Password hashing utilities
│       ├── storage.py            # Storage interface and implementations
│       └── registration.py       # User registration service
├── tests/
│   ├── __init__.py
│   ├── test_validators.py        # Validator tests
│   ├── test_password_hasher.py   # Password hashing tests
│   ├── test_storage.py           # Storage tests
│   └── test_registration.py      # Registration service tests
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Security Considerations

- **No Hardcoded Secrets**: All sensitive configuration should use environment variables
- **Password Hashing**: Uses bcrypt with automatic salt generation
- **In-Memory Storage**: The included `InMemoryUserStorage` is for development/testing only
- **Production Storage**: Implement a proper database-backed storage for production use
- **HTTPS Only**: Always use HTTPS in production to protect credentials in transit
- **Rate Limiting**: Consider implementing rate limiting for registration endpoints

## API Reference

### UserRegistration

#### `register_user(email: str, password: str) -> Dict[str, Any]`

Registers a new user with validation.

**Parameters:**
- `email`: User's email address
- `password`: User's password

**Returns:**
- Dictionary containing user data (without password hash)

**Raises:**
- `RegistrationError`: If validation fails or email already exists

#### `validate_registration_data(email: str, password: str) -> Dict[str, Any]`

Validates registration data without actually registering.

**Parameters:**
- `email`: Email to validate
- `password`: Password to validate

**Returns:**
- Dictionary with validation results for email, password, and overall validity

## Development

### Code Quality Standards

- Python 3.11+
- Type hints on all functions
- Docstrings on all classes and public functions
- Functions under 30 lines where possible
- No hardcoded secrets

### Contributing

1. Create a feature branch
2. Implement changes with tests
3. Ensure all tests pass
4. Submit a pull request

## License

Internal use only.
