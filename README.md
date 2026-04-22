# User Authentication Module

A production-ready user authentication module with login, registration, and password reset functionality.

## Features

- **User Registration**: Secure user registration with email validation and password hashing
- **User Login**: JWT-based authentication with access tokens
- **Password Reset**: Token-based password reset flow
- **Secure Password Hashing**: Using bcrypt via passlib
- **JWT Tokens**: Industry-standard JWT tokens for authentication

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py
│       ├── models.py          # User data models
│       ├── schemas.py         # Pydantic schemas for request/response
│       ├── security.py        # Password hashing and JWT utilities
│       ├── database.py        # Database configuration
│       ├── service.py         # Business logic for auth operations
│       └── router.py          # FastAPI routes
├── tests/
│   ├── __init__.py
│   ├── test_security.py       # Tests for security utilities
│   ├── test_service.py        # Tests for auth service
│   └── test_router.py         # Integration tests for API endpoints
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export DATABASE_URL="sqlite:///./auth.db"  # or your database URL
   export ACCESS_TOKEN_EXPIRE_MINUTES="30"
   ```

## Usage

### Running the Application

```python
from fastapi import FastAPI
from src.auth.router import router as auth_router
from src.auth.database import init_db

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

@app.on_event("startup")
async def startup():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### API Endpoints

#### Register a New User
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

#### Login
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePassword123!
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Request Password Reset
```bash
POST /auth/password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Reset Password
```bash
POST /auth/password-reset/confirm
Content-Type: application/json

{
  "token": "reset-token-here",
  "new_password": "NewSecurePassword123!"
}
```

## Running Tests

```bash
pytest tests/ -v
```

## Security Considerations

- Passwords are hashed using bcrypt with automatic salt generation
- JWT tokens are signed with HS256 algorithm
- Password reset tokens expire after a configurable time period
- Never commit the SECRET_KEY to version control
- Use environment variables for all sensitive configuration

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | Secret key for JWT signing | (required) |
| DATABASE_URL | Database connection string | sqlite:///./auth.db |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT token expiration time | 30 |
| RESET_TOKEN_EXPIRE_HOURS | Password reset token expiration | 24 |

## License

MIT
