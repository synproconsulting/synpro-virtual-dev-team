# Profile Page UI/UX Design and Layout

## Overview

This implementation provides a complete backend solution for a user profile page with modern UI/UX design principles. The module includes profile data management, API endpoints, validation, and UI rendering configuration.

## Features

- **User Profile Management**: Complete CRUD operations for user profiles
- **Avatar Upload**: Support for image upload with validation (JPEG, PNG, WebP)
- **Profile Updates**: Secure profile editing with field validation
- **UI Configuration**: Dynamic UI layout and theming support
- **Type Safety**: Full type hints using Pydantic models
- **Validation**: Comprehensive input validation and sanitization
- **Security**: Environment-based configuration, no hardcoded secrets

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py           # Package initialization
│       ├── profile.py            # Core profile logic and models
│       └── profile_routes.py     # FastAPI routes and endpoints
├── tests/
│   ├── test_profile.py           # Unit tests for profile module
│   └── test_profile_routes.py    # Unit tests for API routes
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL database (or compatible)
- Virtual environment tool (venv, virtualenv, or conda)

### Setup

1. Clone the repository and navigate to the project directory:

```bash
cd synpro-virtual-dev-team
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# UI Theme (optional)
DEFAULT_AVATAR_URL=/static/images/default-avatar.png
THEME_PRIMARY_COLOR=#007bff
THEME_SECONDARY_COLOR=#6c757d
THEME_ACCENT_COLOR=#28a745
```

## API Endpoints

### Get User Profile

```http
GET /api/profile/{user_id}
```

Returns formatted profile data for the specified user.

**Response:**
```json
{
  "userId": "user123",
  "username": "johndoe",
  "email": "john@example.com",
  "fullName": "John Doe",
  "bio": "Software developer",
  "avatarUrl": "https://example.com/avatar.jpg",
  "memberSince": "January 2023",
  "verified": true,
  "contactInfo": {
    "phone": "+1234567890",
    "location": "San Francisco, CA",
    "website": "https://johndoe.com"
  }
}
```

### Get Current User Profile

```http
GET /api/profile/me
```

Returns the authenticated user's profile.

### Update Profile

```http
PUT /api/profile/me
Content-Type: application/json

{
  "full_name": "John Updated Doe",
  "bio": "Updated bio text",
  "phone_number": "+1234567890",
  "location": "New York, NY",
  "website": "https://example.com"
}
```

### Upload Avatar

```http
POST /api/profile/me/avatar
Content-Type: multipart/form-data

file: [image file]
```

**Constraints:**
- Accepted formats: JPEG, PNG, WebP
- Maximum size: 5MB

### Delete Avatar

```http
DELETE /api/profile/me/avatar
```

Resets avatar to default image.

### Get UI Layout Configuration

```http
GET /api/profile/ui/layout
```

Returns UI section configuration and theme settings.

## Data Models

### UserProfile

Core profile data model with the following fields:

- `user_id` (str): Unique user identifier
- `username` (str): User's username
- `email` (EmailStr): Validated email address
- `full_name` (Optional[str]): User's full name
- `bio` (Optional[str]): Biography (max 500 chars)
- `avatar_url` (Optional[str]): Profile picture URL
- `created_at` (datetime): Account creation timestamp
- `updated_at` (datetime): Last update timestamp
- `is_verified` (bool): Email verification status
- `phone_number` (Optional[str]): Phone number
- `location` (Optional[str]): User location
- `website` (Optional[str]): Personal website URL

### ProfileUpdateRequest

Model for profile update operations (only editable fields):

- `full_name` (Optional[str]): Max 100 characters
- `bio` (Optional[str]): Max 500 characters
- `phone_number` (Optional[str]): Min 10 digits
- `location` (Optional[str]): Max 100 characters
- `website` (Optional[str]): Must start with http:// or https://

## Testing

Run the test suite:

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

### Test Coverage

The implementation includes comprehensive unit tests for:

- Profile model validation
- Update request validation
- Profile service operations
- API endpoint behavior
- UI rendering and formatting
- Error handling and edge cases

## Usage Examples

### Basic Profile Retrieval

```python
from src.auth.profile import ProfileService

service = ProfileService()
profile = await service.get_profile("user123")
```

### Profile Update

```python
from src.auth.profile import ProfileService, ProfileUpdateRequest

service = ProfileService()
update_data = ProfileUpdateRequest(
    full_name="Jane Doe",
    bio="Updated bio"
)
updated_profile = await service.update_profile("user123", update_data)
```

### UI Rendering

```python
from src.auth.profile import ProfileUIRenderer, UserProfile

# Get formatted profile data
formatted = ProfileUIRenderer.format_profile_for_display(profile)

# Get UI layout configuration
layout = ProfileUIRenderer.get_profile_sections()
```

## UI/UX Design Principles

The profile page follows these design principles:

1. **User-Centered Design**: Clear information hierarchy with editable/non-editable sections
2. **Responsive Layout**: Section-based layout adaptable to different screen sizes
3. **Visual Consistency**: Configurable theme with primary, secondary, and accent colors
4. **Progressive Disclosure**: Information organized in collapsible sections
5. **Clear Feedback**: Validation messages and success/error states
6. **Accessibility**: Semantic structure and ARIA-compatible layout

## Security Considerations

- All sensitive configuration via environment variables
- Input validation on all user-provided data
- File type and size validation for avatar uploads
- SQL injection protection through Pydantic models
- XSS prevention through input sanitization
- Authentication required for profile modifications

## Future Enhancements

- Social media link integration
- Privacy settings for profile visibility
- Profile activity timeline
- Multi-language support
- Dark mode theme support
- Profile export functionality

## Contributing

1. Create a feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass: `pytest`
4. Format code: `black src/ tests/`
5. Check types: `mypy src/`
6. Submit pull request

## License

Copyright © 2024 Synpro Consulting. All rights reserved.

## Support

For questions or issues, please contact the development team or create an issue in the repository.
