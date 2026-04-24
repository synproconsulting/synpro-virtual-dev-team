# Profile Page UI/UX Implementation

## Overview

This module provides a complete backend implementation for user profile page UI/UX design and layout. It includes profile data management, API endpoints, and UI rendering structures for a modern profile page experience.

## Features

- **Profile Data Management**: Comprehensive user profile data models with validation
- **RESTful API Endpoints**: Complete CRUD operations for user profiles
- **UI Layout Rendering**: Structured UI components for profile display and editing
- **Form Generation**: Dynamic profile edit form generation
- **Preview Functionality**: Preview profile changes before saving
- **Validation**: Robust input validation for all profile fields
- **Type Safety**: Full type hints using Python 3.11+ and Pydantic

## Architecture

### Components

1. **ProfileData Model**: Pydantic model for user profile data with built-in validation
2. **ProfileUpdateRequest Model**: Request model for profile updates
3. **ProfileService**: Service layer for business logic and database operations
4. **ProfileUIRenderer**: Utility class for generating UI layout structures
5. **API Routes**: FastAPI routes for all profile operations

### File Structure

```
src/auth/
├── __init__.py          # Package initialization
├── profile.py           # Core profile models and service
└── profile_routes.py    # API route handlers

tests/
├── __init__.py          # Test package initialization
├── test_profile.py      # Unit tests for profile module
└── test_profile_routes.py  # Unit tests for API routes
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (if needed):
```bash
export DATABASE_URL="your_database_connection_string"
```

## Usage

### Basic Profile Operations

```python
from src.auth.profile import ProfileService, ProfileUpdateRequest

# Initialize service (with database connection in production)
service = ProfileService(database_connection=db)

# Get user profile
profile = await service.get_profile("user123")

# Update profile
update_data = ProfileUpdateRequest(
    full_name="John Doe",
    bio="Software developer",
    location="San Francisco, USA"
)
updated_profile = await service.update_profile("user123", update_data)
```

### UI Rendering

```python
from src.auth.profile import ProfileUIRenderer

# Generate profile page layout
layout = ProfileUIRenderer.render_profile_layout(profile)

# Generate edit form
form = ProfileUIRenderer.render_edit_form(profile)
```

### API Integration

```python
from fastapi import FastAPI
from src.auth import profile_router

app = FastAPI()
app.include_router(profile_router)
```

## API Endpoints

### GET `/api/profile/{user_id}`
Get user profile page data and UI layout.

**Response:**
```json
{
  "success": true,
  "profile": {
    "user_id": "user123",
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    ...
  },
  "ui": {
    "layout": "profile-page",
    "sections": [...]
  }
}
```

### GET `/api/profile/{user_id}/edit`
Get profile edit form structure (authenticated user only).

**Response:**
```json
{
  "success": true,
  "profile": {...},
  "form": {
    "form": "profile-edit",
    "fields": [...]
  }
}
```

### PUT `/api/profile/{user_id}`
Update user profile (authenticated user only).

**Request Body:**
```json
{
  "full_name": "John Doe",
  "bio": "Software developer",
  "phone": "+1234567890",
  "location": "San Francisco, USA",
  "website": "https://johndoe.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "profile": {...}
}
```

### DELETE `/api/profile/{user_id}`
Delete (deactivate) user profile (authenticated user only).

**Response:**
```json
{
  "success": true,
  "message": "Profile deleted successfully"
}
```

### GET `/api/profile/{user_id}/preview`
Preview profile changes without saving.

**Query Parameters:**
- `full_name` (optional)
- `bio` (optional)
- `phone` (optional)
- `location` (optional)
- `website` (optional)

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src/auth tests/
```

Run specific test file:
```bash
pytest tests/test_profile.py
pytest tests/test_profile_routes.py
```

## Validation Rules

### Username
- 3-50 characters
- Alphanumeric, hyphens, and underscores only
- Automatically converted to lowercase

### Email
- Valid email format (validated by Pydantic EmailStr)

### Full Name
- Maximum 100 characters

### Bio
- Maximum 500 characters

### Phone
- Maximum 20 characters

### Location
- Maximum 100 characters

### Website
- Maximum 200 characters
- Must start with `http://` or `https://`

## UI Layout Structure

The profile page layout is organized into sections:

1. **Header Section**: Avatar, username, full name, and bio
2. **Stats Section**: Member since date and last updated date
3. **Contact Info Section**: Email, phone, location, and website
4. **Actions Section**: Edit profile button and actions

## Security Considerations

- All profile update/delete operations require authentication
- Users can only edit their own profiles
- Soft delete (sets `is_active` to `false`) for profile deletion
- Input validation on all fields
- No sensitive data in responses

## Database Schema (Recommended)

```sql
CREATE TABLE user_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    bio VARCHAR(500),
    avatar_url VARCHAR(500),
    phone VARCHAR(20),
    location VARCHAR(100),
    website VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_username ON user_profiles(username);
CREATE INDEX idx_email ON user_profiles(email);
CREATE INDEX idx_is_active ON user_profiles(is_active);
```

## Development

### Code Style
- Python 3.11+
- Type hints on all functions
- Docstrings on all classes and public functions
- PEP 8 compliant (use `black` for formatting)

### Running Linters
```bash
# Format code
black src/ tests/

# Check code quality
flake8 src/ tests/

# Type checking
mypy src/
```

## Future Enhancements

- Avatar upload functionality
- Profile visibility settings (public/private)
- Social media links integration
- Activity history tracking
- Profile completeness indicator
- Custom themes/layouts per user

## License

Internal project - All rights reserved

## Support

For issues or questions, contact the development team.
