# User Update Module - Username and Email

This module provides secure functionality for updating user profile information, specifically username and email addresses, with proper authentication and validation.

## Features

- **Username Update**: Update user's username with validation
- **Email Update**: Update user's email address with validation  
- **Profile Update**: Update both username and email in a single operation
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive validation for usernames and emails
- **Duplicate Detection**: Prevents duplicate usernames and emails
- **Authorization**: Users can only update their own profiles

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py           # Module exports
│       ├── update_user.py        # Core update functionality
│       └── user_repository.py    # Data persistence layer
├── tests/
│   ├── __init__.py
│   ├── test_update_user.py       # Update service tests
│   └── test_user_repository.py   # Repository tests
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set the following environment variables for production use:

- `JWT_SECRET_KEY`: Secret key for JWT token signing (required for production)

**Important**: Never use the default secret key in production!

```bash
export JWT_SECRET_KEY="your-secure-random-secret-key-here"
```

## Usage

### Basic Example

```python
from src.auth import UserUpdateService, InMemoryUserRepository

# Initialize repository and service
repository = InMemoryUserRepository()
service = UserUpdateService(repository)

# Create a test user
user = repository.create(
    username="johndoe",
    email="john@example.com",
    hashed_password="hashed_password_here"
)

# Generate a JWT token for the user (in production, this comes from login)
import jwt
from datetime import datetime, timedelta

token = jwt.encode(
    {
        "sub": str(user["id"]),
        "username": user["username"],
        "exp": datetime.utcnow() + timedelta(minutes=30)
    },
    "your-secret-key",
    algorithm="HS256"
)

# Update username
result = service.update_username(
    user_id=user["id"],
    new_username="john_doe_updated",
    token=token
)
print(f"Updated username: {result['username']}")

# Update email
result = service.update_email(
    user_id=user["id"],
    new_email="john.doe@example.com",
    token=token
)
print(f"Updated email: {result['email']}")

# Update both at once
result = service.update_user_profile(
    user_id=user["id"],
    username="johndoe2024",
    email="johndoe2024@example.com",
    token=token
)
print(f"Updated profile: {result}")
```

### Validation Rules

**Username:**
- 3-30 characters in length
- Only alphanumeric characters, underscores (_), and hyphens (-)
- Must be unique across all users

**Email:**
- Valid email format (e.g., user@example.com)
- Must be unique across all users

## API Reference

### UserUpdateService

#### `update_username(user_id: int, new_username: str, token: str) -> Dict[str, Any]`

Update a user's username.

**Parameters:**
- `user_id`: ID of the user to update
- `new_username`: New username to set
- `token`: Valid JWT authentication token

**Returns:** Dictionary with updated user information

**Raises:**
- `ValidationError`: If username format is invalid
- `AuthenticationError`: If token is invalid or unauthorized
- `UserNotFoundError`: If user doesn't exist
- `UserUpdateError`: If username is already taken

#### `update_email(user_id: int, new_email: str, token: str) -> Dict[str, Any]`

Update a user's email address.

**Parameters:**
- `user_id`: ID of the user to update
- `new_email`: New email address to set
- `token`: Valid JWT authentication token

**Returns:** Dictionary with updated user information

**Raises:**
- `ValidationError`: If email format is invalid
- `AuthenticationError`: If token is invalid or unauthorized
- `UserNotFoundError`: If user doesn't exist
- `UserUpdateError`: If email is already taken

#### `update_user_profile(user_id: int, username: Optional[str], email: Optional[str], token: str) -> Dict[str, Any]`

Update user profile (username and/or email).

**Parameters:**
- `user_id`: ID of the user to update
- `username`: New username (optional)
- `email`: New email address (optional)
- `token`: Valid JWT authentication token

**Returns:** Dictionary with updated user information

**Raises:**
- `ValidationError`: If any field format is invalid or both fields are None
- `AuthenticationError`: If token is invalid or unauthorized
- `UserNotFoundError`: If user doesn't exist
- `UserUpdateError`: If username or email is already taken

### Helper Functions

#### `validate_email(email: str) -> bool`

Validate email format.

#### `validate_username(username: str) -> bool`

Validate username format.

#### `verify_token(token: str) -> Dict[str, Any]`

Verify JWT token and extract user information.

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_update_user.py

# Run with verbose output
pytest -v
```

### Test Coverage

The test suite includes:
- Email validation tests
- Username validation tests
- JWT token verification tests
- Username update tests (success, validation, authorization)
- Email update tests (success, validation, authorization)
- Profile update tests (combined updates)
- Repository CRUD operations
- Error handling and edge cases

## Security Considerations

1. **JWT Secret Key**: Always use a strong, random secret key in production
2. **Token Expiration**: Tokens expire after 30 minutes by default
3. **Authorization**: Users can only update their own profiles
4. **Password Hashing**: Uses bcrypt for secure password hashing
5. **Input Validation**: All inputs are validated before processing
6. **No Sensitive Data in Responses**: Hashed passwords are never returned

## Error Handling

The module provides specific exception types:

- `UserUpdateError`: Base exception for update-related errors
- `ValidationError`: Invalid input format
- `AuthenticationError`: Invalid or expired token, unauthorized access
- `UserNotFoundError`: User doesn't exist

## Production Considerations

**Database Integration:**

The current implementation uses an in-memory repository for demonstration. For production:

1. Replace `InMemoryUserRepository` with a proper database implementation (PostgreSQL, MySQL, etc.)
2. Use SQLAlchemy or another ORM for database operations
3. Implement proper transaction handling
4. Add database migrations (e.g., Alembic)

**Example PostgreSQL Repository:**

```python
from sqlalchemy.orm import Session
from .models import User

class PostgreSQLUserRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def update_username(self, user_id: int, new_username: str):
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        user.username = new_username
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # ... implement other methods
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.
