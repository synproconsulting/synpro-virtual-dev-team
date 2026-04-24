# Change Password Functionality - SDT1-14

This module implements secure password change functionality for user authentication systems.

## Features

- **Secure Password Hashing**: Uses bcrypt for password hashing
- **Password Strength Validation**: Enforces strong password requirements
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
- **Password History**: Prevents reuse of recently used passwords
- **Current Password Verification**: Requires current password for changes
- **Password Expiry Detection**: Identifies when passwords need to be changed
- **Thread-Safe Repository**: In-memory implementation with thread safety

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py              # Module exports
│       ├── change_password.py       # Core password change logic
│       └── user_repository.py       # User data persistence interface
├── tests/
│   ├── __init__.py
│   └── test_change_password.py      # Comprehensive unit tests
├── requirements.txt                  # Project dependencies
└── README.md                         # This file
```

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Password Change

```python
from src.auth.change_password import PasswordChangeService, PasswordChangeRequest
from src.auth.user_repository import InMemoryUserRepository

# Initialize repository and service
repository = InMemoryUserRepository()
service = PasswordChangeService(user_repository=repository)

# Create a user (for testing)
user_id = "user123"
initial_password_hash = service.hash_password("OldPassword123!")
repository.create_user(
    user_id=user_id,
    password_hash=initial_password_hash,
    email="user@example.com"
)

# Change password
request = PasswordChangeRequest(
    user_id=user_id,
    current_password="OldPassword123!",
    new_password="NewSecurePass456@",
    confirm_password="NewSecurePass456@"
)

response = service.change_password(request)

if response.success:
    print(f"Password changed successfully at {response.changed_at}")
else:
    print(f"Password change failed: {response.message}")
```

### Check if Password Change is Required

```python
should_force = service.should_force_password_change(user_id)

if should_force:
    print("User must change password (expired or never changed)")
```

## Configuration

The service supports configuration via environment variables:

- `MAX_PASSWORD_AGE_DAYS` (default: 90): Maximum days before password expires
- `PASSWORD_HISTORY_COUNT` (default: 5): Number of historical passwords to check

```bash
export MAX_PASSWORD_AGE_DAYS=60
export PASSWORD_HISTORY_COUNT=10
```

## Testing

Run the test suite with pytest:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/auth --cov-report=html

# Run specific test file
pytest tests/test_change_password.py

# Run with verbose output
pytest tests/ -v
```

### Test Coverage

The test suite includes:
- Password validation tests (strength requirements)
- Password matching validation
- Successful password change scenarios
- Error handling (wrong password, user not found)
- Password history checks
- Password expiry detection
- Repository operations
- Thread safety (via in-memory implementation)

## API Reference

### PasswordChangeRequest

Request model for password change operations.

**Fields:**
- `user_id` (str): Unique user identifier
- `current_password` (str): User's current password
- `new_password` (str): New password (min 8 chars, must meet strength requirements)
- `confirm_password` (str): Confirmation of new password

### PasswordChangeResponse

Response model for password change operations.

**Fields:**
- `success` (bool): Whether the operation succeeded
- `message` (str): Human-readable message
- `changed_at` (datetime, optional): Timestamp of password change

### PasswordChangeService

Service class for password change operations.

**Methods:**
- `hash_password(password: str) -> str`: Hash a plaintext password
- `verify_password(plain_password: str, hashed_password: str) -> bool`: Verify password
- `change_password(request: PasswordChangeRequest) -> PasswordChangeResponse`: Change user password
- `check_password_in_history(user_id: str, new_password: str) -> bool`: Check if password was recently used
- `should_force_password_change(user_id: str) -> bool`: Check if password change should be forced

## Security Considerations

1. **Password Storage**: Passwords are hashed using bcrypt with automatic salt generation
2. **No Plain Text**: Plain text passwords are never stored
3. **History Protection**: Prevents reuse of recent passwords
4. **Strength Requirements**: Enforces strong password policies
5. **Current Password Verification**: Requires knowledge of current password
6. **No Secrets in Code**: Configuration via environment variables

## Integration with Databases

The `InMemoryUserRepository` is provided for development and testing. For production use, implement the `UserRepositoryInterface` with your database backend:

```python
from src.auth.user_repository import UserRepositoryInterface

class PostgresUserRepository(UserRepositoryInterface):
    def __init__(self, connection_string):
        # Initialize database connection
        pass
    
    def get_user_by_id(self, user_id: str):
        # Query database
        pass
    
    # Implement other methods...
```

## License

Internal project - All rights reserved

## Contributing

This is part of SDT1-14 Jira ticket implementation. For questions or issues, contact the development team.
