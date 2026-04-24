# Notification History View and UI Components

A comprehensive notification management system with history view and UI components for displaying, filtering, and managing user notifications.

## Features

- **Notification Models**: Complete data models for notifications with support for multiple types (email, SMS, push, in-app, webhook)
- **Status Management**: Track notification lifecycle through pending, sent, delivered, failed, and read states
- **Repository Layer**: Data access layer with filtering, pagination, and search capabilities
- **Service Layer**: Business logic for notification operations including creation, updates, and statistics
- **View Layer**: UI rendering components that generate HTML for notification display
- **REST API**: FastAPI endpoints for all notification operations
- **Comprehensive Testing**: Full test coverage with pytest

## Architecture

```
src/notifications/
├── __init__.py          # Module exports
├── models.py            # Data models (Notification, enums)
├── repository.py        # Data access layer
├── service.py           # Business logic layer
├── views.py             # UI rendering layer
├── api.py               # FastAPI endpoints
└── styles.css           # CSS styles for UI components

tests/
├── test_models.py       # Model tests
├── test_repository.py   # Repository tests
├── test_service.py      # Service tests
└── test_views.py        # View tests
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Creating Notifications

```python
from src.notifications import NotificationService, NotificationType

service = NotificationService()

# Create a notification
notification = service.create_notification(
    user_id="user-123",
    notification_type=NotificationType.EMAIL,
    title="Welcome!",
    message="Welcome to our platform",
    metadata={"campaign": "onboarding"}
)
```

### Viewing Notification History

```python
from src.notifications import NotificationHistoryView

view = NotificationHistoryView()

# Get notification history data
history = view.get_history_data(
    user_id="user-123",
    page=1,
    page_size=20,
    status_filter="pending",
    type_filter="email"
)

# Render as HTML
html = view.render_notification_list(
    user_id="user-123",
    page=1,
    page_size=20
)
```

### Using the API

```python
from fastapi import FastAPI
from src.notifications.api import create_notification_routes

app = FastAPI()
create_notification_routes(app)

# Run with: uvicorn main:app --reload
```

#### API Endpoints

- `POST /api/notifications` - Create a new notification
- `GET /api/notifications/history/{user_id}` - Get notification history (JSON)
- `GET /api/notifications/history/{user_id}/html` - Get notification history (HTML)
- `PUT /api/notifications/{notification_id}/read` - Mark notification as read
- `PUT /api/notifications/read-all/{user_id}` - Mark all as read
- `DELETE /api/notifications/{notification_id}` - Delete notification
- `GET /api/notifications/stats/{user_id}` - Get statistics
- `GET /api/notifications/filters` - Get filter options

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/notifications --cov-report=html

# Run specific test file
pytest tests/test_service.py

# Run with verbose output
pytest -v
```

## Data Models

### Notification

```python
@dataclass
class Notification:
    id: str
    user_id: str
    type: NotificationType
    status: NotificationStatus
    title: str
    message: str
    metadata: dict
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    error_message: Optional[str]
```

### NotificationType (Enum)

- `EMAIL` - Email notifications
- `SMS` - SMS/text notifications
- `PUSH` - Push notifications
- `IN_APP` - In-app notifications
- `WEBHOOK` - Webhook notifications

### NotificationStatus (Enum)

- `PENDING` - Notification created but not sent
- `SENT` - Notification sent
- `DELIVERED` - Notification delivered to recipient
- `FAILED` - Notification failed to send
- `READ` - Notification read by user

## UI Components

The view layer provides several HTML rendering methods:

- `render_notification_card()` - Single notification card
- `render_notification_list()` - Complete notification list with pagination
- `render_pagination()` - Pagination controls
- `render_stats()` - Notification statistics
- `render_filters()` - Filter dropdowns

All components are styled with the included `styles.css` file.

## Features in Detail

### Pagination

```python
history = service.get_notification_history(
    user_id="user-123",
    page=2,
    page_size=10
)

print(history["pagination"])
# {
#     "page": 2,
#     "page_size": 10,
#     "total_count": 45,
#     "total_pages": 5,
#     "has_next": True,
#     "has_previous": True
# }
```

### Filtering

```python
# Filter by status
history = service.get_notification_history(
    user_id="user-123",
    status=NotificationStatus.UNREAD
)

# Filter by type
history = service.get_notification_history(
    user_id="user-123",
    notification_type=NotificationType.EMAIL
)
```

### Statistics

```python
stats = service.get_notification_stats("user-123")
# {
#     "total_count": 150,
#     "unread_count": 12,
#     "by_type": {"email": 80, "sms": 40, "push": 30},
#     "by_status": {"pending": 5, "sent": 100, "read": 45}
# }
```

### Bulk Operations

```python
# Mark all notifications as read
count = service.mark_all_as_read("user-123")
print(f"Marked {count} notifications as read")
```

## Configuration

The system uses in-memory storage by default. For production use, replace the `NotificationRepository` implementation with a database-backed version.

## Development

### Code Style

This project follows PEP 8 style guidelines:

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/
```

### Adding New Notification Types

1. Add to `NotificationType` enum in `models.py`
2. Add icon mapping in `views.py` `_get_type_icon()`
3. Update tests

### Adding New Status Types

1. Add to `NotificationStatus` enum in `models.py`
2. Add status class mapping in `views.py` `_get_status_class()`
3. Add CSS styles in `styles.css`
4. Update tests

## License

MIT License

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues or questions, please open an issue in the repository.
