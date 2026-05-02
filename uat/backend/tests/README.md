# UAT Backend Tests

## Overview

This directory contains tests for the UAT backend API, with a focus on security and authentication functionality.

## Running Tests

### Run all tests
```bash
cd uat/backend
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth_security.py -v
```

### Run specific test class
```bash
pytest tests/test_auth_security.py::TestPasswordResetSecurity -v
```

### Run specific test
```bash
pytest tests/test_auth_security.py::TestPasswordResetSecurity::test_password_reset_request_does_not_return_token -v
```

## Test Structure

### `test_auth_security.py`
Security-focused tests for authentication endpoints, particularly:
- Password reset token security (SDT1-62)
- Token exposure prevention
- Logging security
- Email enumeration prevention

## Test Fixtures

### `mock_db`
Provides a mocked database connection and cursor for testing without requiring a real database.

### `client`
FastAPI test client with mocked database dependency injection.

## Writing New Tests

When adding new tests:

1. **Use type hints**: All test functions should have proper type hints
2. **Use descriptive names**: Test names should clearly describe what they test
3. **Mock external dependencies**: Use `@patch` for database, email, and external services
4. **Test security**: Always consider security implications
5. **Document with docstrings**: Explain what the test verifies

Example:
```python
@patch('auth.send_password_reset_email', new_callable=AsyncMock)
def test_new_feature(self, mock_send_email, client, mock_db):
    """
    Test that new feature works correctly and securely.
    """
    # Arrange
    mock_conn, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = {"id": "test-id"}
    
    # Act
    response = client.post("/endpoint", json={"data": "test"})
    
    # Assert
    assert response.status_code == 200
    assert "sensitive_data" not in response.json()
```

## Continuous Integration

These tests run automatically on:
- Every pull request
- Every commit to main
- Scheduled daily runs

All tests must pass before code can be merged.

## Coverage Goals

- **Target**: 80%+ code coverage
- **Critical paths**: 100% coverage for authentication and security code
- **Focus areas**: Error handling, edge cases, security boundaries
