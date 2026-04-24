# Notification Preferences Management Interface

A comprehensive Python implementation for managing user notification preferences across multiple channels (email, SMS, push, in-app) and event categories.

## Features

- **Multi-channel notification support**: Email, SMS, Push, and In-App notifications
- **Event categories**: Security, Account, Marketing, Product Updates, System, and Social
- **Global controls**: Global mute and quiet hours functionality
- **Timezone support**: Per-user timezone configuration
- **RESTful API**: FastAPI-based endpoints for preference management
- **Flexible storage**: Pluggable storage backend (default: in-memory)
- **Comprehensive validation**: Pydantic models with built-in validation
- **Full test coverage**: Unit tests for all major components

## Installation

1. Clone the repository:
```bash
git clone https://github.com/synproconsulting/synpro-virtual-dev-team.git
cd synpro-virtual-dev-team
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
.
├── src/
│   └── auth/
│       ├── __init__.py
│       ├── notification_preferences.py  # Core business logic
│       └── notification_api.py          # REST API endpoints
├── tests/
│   ├── __init__.py
│   ├── test_notification_preferences.py  # Unit tests for core module
│   └── test_notification_api.py          # API endpoint tests
├── requirements.txt
└── README.md
```

## Usage

### Basic Usage

```python
from src.auth import NotificationPreferencesManager, NotificationType, EventCategory

# Initialize the manager
manager = NotificationPreferencesManager()

# Get user preferences (creates defaults for new users)
profile = manager.get_user_preferences("user123")

# Update a single preference
manager.update_preference(
    user_id="user123",
    event_category=EventCategory.SECURITY,
    notification_type=NotificationType.EMAIL,
    enabled=True
)

# Update global settings
manager.update_global_settings(
    user_id="user123",
    global_mute=False,
    quiet_hours_enabled=True,
    quiet_hours_start="22:00",
    quiet_hours_end="08:00",
    timezone="America/New_York"
)

# Check if notification is allowed
allowed = manager.is_notification_allowed(
    user_id="user123",
    event_category=EventCategory.SECURITY,
    notification_type=NotificationType.EMAIL
)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from src.auth import notification_router

app = FastAPI()
app.include_router(notification_router)

# Run with: uvicorn main:app --reload
```

## API Endpoints

### Get User Preferences
```
GET /api/v1/notifications/preferences
GET /api/v1/notifications/preferences?user_id={user_id}
```

### Update Single Preference
```
PUT /api/v1/notifications/preferences/single
Body: {
    "event_category": "security",
    "notification_type": "email",
    "enabled": false
}
```

### Bulk Update Preferences
```
PUT /api/v1/notifications/preferences/bulk
Body: {
    "preferences": [
        {
            "event_category": "security",
            "notification_type": "email",
            "enabled": false
        },
        {
            "event_category": "marketing",
            "notification_type": "sms",
            "enabled": true
        }
    ]
}
```

### Update Global Settings
```
PUT /api/v1/notifications/preferences/global
Body: {
    "global_mute": true,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00",
    "timezone": "America/New_York"
}
```

### Check Notification Allowed
```
POST /api/v1/notifications/check
Body: {
    "event_category": "security",
    "notification_type": "email"
}
```

### Get Metadata
```
GET /api/v1/notifications/categories  # List all event categories
GET /api/v1/notifications/types       # List all notification types
```

## Event Categories

- `security` - Security-related notifications
- `account` - Account activity notifications
- `marketing` - Marketing and promotional content
- `product_updates` - Product feature updates
- `system` - System maintenance and alerts
- `social` - Social interactions and comments

## Notification Types

- `email` - Email notifications
- `sms` - SMS/text message notifications
- `push` - Push notifications (mobile/web)
- `in_app` - In-application notifications

## Default Behavior

When a new user is created, default preferences are automatically generated:
- All notification types are **enabled** for all event categories
- **Except**: Marketing notifications are **disabled** by default
- Global mute is **off**
- Quiet hours are **disabled**
- Timezone is set to **UTC**

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_notification_preferences.py
pytest tests/test_notification_api.py
```

## Storage Backends

The system supports pluggable storage backends. The default is in-memory storage.

### Custom Storage Backend

Implement the `StorageBackend` interface:

```python
from src.auth import StorageBackend, NotificationPreferencesProfile
from typing import Optional

class MyCustomStorage(StorageBackend):
    def get_profile(self, user_id: str) -> Optional[NotificationPreferencesProfile]:
        # Your implementation
        pass
    
    def save_profile(self, profile: NotificationPreferencesProfile) -> None:
        # Your implementation
        pass

# Use custom storage
manager = NotificationPreferencesManager(storage_backend=MyCustomStorage())
```

## Security Considerations

- All user inputs are validated using Pydantic models
- No secrets or API keys are hardcoded
- Authentication dependency is designed to integrate with existing auth systems
- Input sanitization is handled automatically by FastAPI and Pydantic

## Future Enhancements

- Database storage backend (PostgreSQL, MongoDB)
- Notification delivery scheduling
- A/B testing for notification effectiveness
- Notification batching and digest options
- User preference import/export
- Admin dashboard for preference management
- Notification history and analytics

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

Copyright © 2024 Synpro Consulting. All rights reserved.
