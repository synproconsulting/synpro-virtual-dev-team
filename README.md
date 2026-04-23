# User Profile Viewing Module

## Overview

This module provides functionality to view user profile details from a PostgreSQL database. It includes methods to retrieve user profiles by ID or username, get public profile information, and format profile data for display.

## Features

- **Retrieve user profile by ID**: Get complete user profile information using user ID
- **Retrieve user profile by username**: Get complete user profile information using username
- **Public profile view**: Get public profile information (excludes sensitive data like email)
- **Profile formatting**: Format profile data for display
- **Error handling**: Comprehensive error handling with custom exceptions
- **Type safety**: Full type hints for all functions
- **Logging**: Built-in logging for debugging and monitoring

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your database connection by setting the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

## Database Schema

The module expects a `users` table with the following structure:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

## Usage

### Basic Usage

```python
from src.auth.profile import UserProfile

# Initialize with environment variable DATABASE_URL
profile_service = UserProfile()

# Or initialize with explicit database URL
profile_service = UserProfile(database_url="postgresql://user:password@localhost:5432/dbname")

# Get user profile by ID
try:
    user = profile_service.get_profile_by_id(1)
    print(user)
except UserNotFoundError:
    print("User not found")

# Get user profile by username
try:
    user = profile_service.get_profile_by_username("johndoe")
    print(user)
except UserNotFoundError:
    print("User not found")

# Get public profile (excludes sensitive information)
public_profile = profile_service.get_public_profile(1)
print(public_profile)

# Format profile for display
formatted = profile_service.format_profile_display(user)
print(formatted)
```

### Error Handling

The module provides custom exceptions for different error scenarios:

```python
from src.auth.profile import (
    UserProfile,
    UserProfileError,
    UserNotFoundError,
    DatabaseConnectionError
)

profile_service = UserProfile()

try:
    user = profile_service.get_profile_by_id(123)
except UserNotFoundError as e:
    print(f"User not found: {e}")
except DatabaseConnectionError as e:
    print(f"Database error: {e}")
except UserProfileError as e:
    print(f"Profile error: {e}")
```

## API Reference

### UserProfile Class

#### `__init__(database_url: Optional[str] = None)`

Initialize the UserProfile instance.

- **Parameters:**
  - `database_url` (str, optional): PostgreSQL connection string. If not provided, reads from `DATABASE_URL` environment variable.
- **Raises:**
  - `DatabaseConnectionError`: If database URL is not provided and not found in environment variables.

#### `get_profile_by_id(user_id: int) -> Dict[str, Any]`

Retrieve user profile by user ID.

- **Parameters:**
  - `user_id` (int): The unique identifier of the user.
- **Returns:** Dictionary containing user profile information.
- **Raises:**
  - `UserNotFoundError`: If user with given ID doesn't exist.
  - `DatabaseConnectionError`: If database operation fails.

#### `get_profile_by_username(username: str) -> Dict[str, Any]`

Retrieve user profile by username.

- **Parameters:**
  - `username` (str): The username of the user.
- **Returns:** Dictionary containing user profile information.
- **Raises:**
  - `UserNotFoundError`: If user with given username doesn't exist.
  - `DatabaseConnectionError`: If database operation fails.

#### `get_public_profile(user_id: int) -> Dict[str, Any]`

Retrieve public user profile information (excludes sensitive data).

- **Parameters:**
  - `user_id` (int): The unique identifier of the user.
- **Returns:** Dictionary containing public user profile information (id, username, full_name, bio, avatar_url, created_at).
- **Raises:**
  - `UserNotFoundError`: If user with given ID doesn't exist.
  - `DatabaseConnectionError`: If database operation fails.

#### `format_profile_display(profile: Dict[str, Any]) -> str`

Format user profile for display.

- **Parameters:**
  - `profile` (dict): Dictionary containing user profile data.
- **Returns:** Formatted string representation of the profile.

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/auth --cov-report=html

# Run specific test file
pytest tests/test_profile.py

# Run with verbose output
pytest -v
```

## Security Considerations

- **No hardcoded credentials**: All database credentials must be provided via environment variables
- **Public profile filtering**: Sensitive information like email addresses are excluded from public profiles
- **SQL injection protection**: Uses parameterized queries to prevent SQL injection
- **Error logging**: Database errors are logged for monitoring without exposing sensitive details to users

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (required)
  - Format: `postgresql://username:password@host:port/database`

## Dependencies

- `psycopg2-binary`: PostgreSQL database adapter
- `pytest`: Testing framework
- `pytest-cov`: Code coverage plugin for pytest
- `pytest-mock`: Mocking plugin for pytest

## License

This module is part of the SDT1-15 implementation.

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request
