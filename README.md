# Profile Management API

A comprehensive FastAPI-based profile management system with authentication, authorization, and user profile operations.

## Features

- **Get Profile**: Retrieve user profile information
- **Update Profile**: Update user details (name, email, phone, bio, avatar)
- **Change Password**: Secure password change with validation
- **Deactivate Profile**: Soft delete user profiles
- **JWT Authentication**: Bearer token-based authentication
- **Input Validation**: Comprehensive validation using Pydantic models
- **Password Security**: Bcrypt hashing with complexity requirements

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py       # Module exports
│       ├── profile.py        # Profile models and service layer
│       └── api.py            # FastAPI endpoints
├── tests/
│   ├── __init__.py
│   ├── test_profile.py       # Profile model and service tests
│   └── test_api.py           # API endpoint tests
├── requirements.txt          # Project dependencies
└── README.md                 # This file
```

## Installation

### Prerequisites

- Python 3.11+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
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

4. Set environment variables:
```bash
export JWT_SECRET_KEY="your-secret-key-here"
export JWT_ALGORITHM="HS256"
```

## API Endpoints

### Base URL: `/api/v1/profile`

All endpoints require JWT authentication via Bearer token in the `Authorization` header.

### 1. Get Current User Profile

**GET** `/api/v1/profile/me`

Retrieve the authenticated user's profile.

**Response:**
```json
{
  "user_id": "123",
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "bio": "Software developer",
  "avatar_url": "https://example.com/avatar.jpg",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "is_active": true
}
```

### 2. Update Current User Profile

**PUT** `/api/v1/profile/me`

Update the authenticated user's profile.

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "full_name": "Jane Doe",
  "phone_number": "+1234567890",
  "bio": "Updated bio",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

All fields are optional. Only provided fields will be updated.

**Response:** Updated profile object (same as GET)

### 3. Change Password

**POST** `/api/v1/profile/me/change-password`

Change the authenticated user's password.

**Request Body:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456",
  "confirm_password": "NewPass456"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- Must be different from current password

**Response:**
```json
{
  "message": "Password changed successfully",
  "changed_at": "2024-01-01T12:00:00"
}
```

### 4. Deactivate Profile

**DELETE** `/api/v1/profile/me`

Deactivate (soft delete) the authenticated user's profile.

**Response:**
```json
{
  "message": "Profile deactivated successfully",
  "deactivated_at": "2024-01-01T12:00:00"
}
```

### 5. Get User Profile by ID

**GET** `/api/v1/profile/{user_id}`

Retrieve a specific user's profile. Currently restricted to own profile only (future: admin access).

**Response:** Profile object (same as GET /me)

## Authentication

All endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

The JWT token must contain a `sub` (subject) claim with the user ID.

## Running Tests

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_profile.py

# Run with verbose output
pytest -v
```

## Usage Example

### Using Python requests:

```python
import requests

# Base URL
base_url = "http://localhost:8000/api/v1/profile"

# JWT token (obtain from authentication endpoint)
token = "your-jwt-token-here"
headers = {"Authorization": f"Bearer {token}"}

# Get profile
response = requests.get(f"{base_url}/me", headers=headers)
print(response.json())

# Update profile
update_data = {
    "full_name": "Jane Smith",
    "bio": "Python developer"
}
response = requests.put(f"{base_url}/me", json=update_data, headers=headers)
print(response.json())

# Change password
password_data = {
    "current_password": "OldPass123",
    "new_password": "NewPass456",
    "confirm_password": "NewPass456"
}
response = requests.post(f"{base_url}/me/change-password", json=password_data, headers=headers)
print(response.json())
```

### Using curl:

```bash
# Get profile
curl -X GET "http://localhost:8000/api/v1/profile/me" \
  -H "Authorization: Bearer your-jwt-token"

# Update profile
curl -X PUT "http://localhost:8000/api/v1/profile/me" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Jane Smith", "bio": "Python developer"}'

# Change password
curl -X POST "http://localhost:8000/api/v1/profile/me/change-password" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPass123",
    "new_password": "NewPass456",
    "confirm_password": "NewPass456"
  }'
```

## Integration with FastAPI Application

To integrate the profile router into your FastAPI application:

```python
from fastapi import FastAPI
from src.auth import profile_router

app = FastAPI(title="My Application")

# Include the profile management router
app.include_router(profile_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Database Integration

The current implementation includes placeholder methods that raise `NotImplementedError`. To integrate with a database:

1. **Create database models** (e.g., using SQLAlchemy or your ORM of choice)
2. **Implement the ProfileService methods** in `src/auth/profile.py`
3. **Update the dependency** `get_profile_service()` in `src/auth/api.py` to return a service with an actual database connection

Example SQLAlchemy integration:

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_profile_service(db: AsyncSession = Depends(get_db)):
    return ProfileService(database_connection=db)
```

## Security Considerations

- **Environment Variables**: Never commit `JWT_SECRET_KEY` to version control
- **Password Hashing**: Uses bcrypt with automatic salting
- **JWT Expiration**: Implement token expiration in your authentication system
- **HTTPS**: Always use HTTPS in production
- **Rate Limiting**: Consider adding rate limiting to prevent brute force attacks
- **Input Validation**: All inputs are validated using Pydantic models

## Error Handling

The API returns standard HTTP status codes:

- **200 OK**: Request successful
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Not authorized to access resource
- **404 Not Found**: Resource not found
- **501 Not Implemented**: Database integration required

Error responses include a detail message:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Development

### Code Quality Tools

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/
```

### Running the Development Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Follow PEP 8 style guidelines
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on the project repository.
