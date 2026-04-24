# User Account Deletion - SDT1-13

This module provides comprehensive user account deletion functionality with support for both soft and hard deletion methods.

## Features

- **Soft Delete**: Marks user as inactive and anonymizes personal data while retaining the record
- **Hard Delete**: Permanently removes user and all associated data from the database
- **Authorization Verification**: Ensures users can only delete their own accounts (unless admin)
- **Bulk Deletion**: Admin functionality to clean up inactive users
- **Comprehensive Error Handling**: Custom exceptions for different failure scenarios
- **Transaction Safety**: All operations use database transactions with proper rollback on errors

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export DB_HOST=localhost
export DB_NAME=your_database
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_PORT=5432  # Optional, defaults to 5432
```

## Usage

### Delete User Account

```python
from src.auth.delete_user import delete_user_account

# Soft delete (default)
result = delete_user_account(
    user_id=123,
    requesting_user_id=123,
    is_admin=False,
    hard_delete=False
)

# Hard delete (permanent)
result = delete_user_account(
    user_id=123,
    requesting_user_id=123,
    is_admin=False,
    hard_delete=True
)

# Admin deleting another user's account
result = delete_user_account(
    user_id=456,
    requesting_user_id=1,
    is_admin=True,
    hard_delete=False
)
```

### Bulk Delete Inactive Users

```python
from src.auth.delete_user import bulk_delete_inactive_users

# Dry run to see how many users would be deleted
result = bulk_delete_inactive_users(
    days_inactive=365,
    requesting_admin_id=1,
    dry_run=True
)

# Actual deletion
result = bulk_delete_inactive_users(
    days_inactive=365,
    requesting_admin_id=1,
    dry_run=False
)
```

## Database Schema Requirements

The module expects the following database tables:

### users table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

### Related tables (for hard delete)
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE user_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id)
);
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_delete_user.py

# Run with coverage
pytest tests/test_delete_user.py --cov=src/auth --cov-report=html

# Run specific test class
pytest tests/test_delete_user.py::TestDeleteUserAccount

# Run with verbose output
pytest tests/test_delete_user.py -v
```

## Error Handling

The module defines custom exceptions:

- **UserNotFoundError**: Raised when the specified user does not exist
- **UnauthorizedDeletionError**: Raised when user lacks permission to delete the account
- **UserDeletionError**: Raised when deletion operation fails

Example:
```python
from src.auth.delete_user import (
    delete_user_account,
    UserNotFoundError,
    UnauthorizedDeletionError,
    UserDeletionError
)

try:
    result = delete_user_account(user_id=123, requesting_user_id=123)
except UserNotFoundError:
    print("User not found")
except UnauthorizedDeletionError:
    print("Not authorized to delete this account")
except UserDeletionError as e:
    print(f"Deletion failed: {e}")
```

## Security Considerations

1. **Environment Variables**: Never commit database credentials to version control
2. **Authorization**: The module enforces that users can only delete their own accounts unless they have admin privileges
3. **Soft Delete by Default**: Soft deletion is the default to prevent accidental data loss
4. **Transaction Safety**: All database operations use transactions to ensure data integrity
5. **Audit Trail**: Soft deletes preserve records with deletion timestamp for audit purposes

## Response Format

Successful deletion returns:
```python
{
    "success": True,
    "user_id": 123,
    "deletion_type": "soft",  # or "hard"
    "deleted_at": "2024-01-01T12:00:00",
    "message": "User account successfully deleted (soft delete)"
}
```

## Development

### Code Style
- Python 3.11+
- Type hints on all functions
- Docstrings following Google style
- Maximum function length: 30 lines
- No hardcoded secrets

### Logging
The module uses Python's logging module. Configure it in your application:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## License

Internal use only - Synpro Consulting
