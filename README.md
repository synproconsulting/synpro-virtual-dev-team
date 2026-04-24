# Test Feedback Loop - SDT1-18

This repository demonstrates a test feedback loop implementation for the authentication module.

## Overview

This project replaces the existing README with new content as per ticket SDT1-18 requirements. All previous requirements have been removed and replaced with a fresh authentication module implementation.

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py
│       ├── user.py
│       └── authentication.py
├── tests/
│   ├── __init__.py
│   └── test_authentication.py
├── requirements.txt
└── README.md
```

## Features

- User registration and authentication
- Password hashing with bcrypt
- JWT token generation and validation
- Type-safe Python 3.11+ implementation
- Comprehensive unit tests

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```python
from src.auth.authentication import AuthService
from src.auth.user import User

# Initialize auth service
auth_service = AuthService()

# Register a new user
user = auth_service.register_user("john@example.com", "secure_password123")

# Authenticate user
is_authenticated = auth_service.authenticate_user("john@example.com", "secure_password123")

# Generate JWT token
token = auth_service.generate_token(user.user_id)

# Validate token
payload = auth_service.validate_token(token)
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## Environment Variables

Set the following environment variables:

- `JWT_SECRET_KEY`: Secret key for JWT token signing (required)
- `JWT_ALGORITHM`: Algorithm for JWT (default: HS256)
- `JWT_EXPIRATION_MINUTES`: Token expiration time in minutes (default: 30)

## License

MIT License
