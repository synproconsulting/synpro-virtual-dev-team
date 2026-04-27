# In-App Notification Storage and Data Model

This module provides a complete implementation for in-app notification storage and data models with support for multiple storage backends.

## Features

- **Comprehensive Data Models**: Well-defined notification models using Pydantic with validation
- **Flexible Storage Layer**: Abstract storage interface with in-memory implementation
- **Database Support**: SQLAlchemy models for persistent storage (PostgreSQL, SQLite)
- **Status Management**: Track notification states (unread, read, archived)
- **Type Classification**: Multiple notification types (info, success, warning, error, system, user_action, reminder)
- **Expiration Support**: Time-sensitive notifications with automatic expiration
- **Rich Metadata**: Extensible metadata field for custom data
- **Pagination**: Built-in support for paginated queries
- **Full Test Coverage**: Comprehensive unit tests using pytest

## Project Structure

```
src/
  notifications/
    __init__.py           # Package initialization
    models.py             # Pydantic data models
    storage.py            # Storage layer implementation
    database.py           # SQLAlchemy database models
tests/
  test_notification_models.py    # Model unit tests
  test_notification_storage.py   # Storage unit tests
requirements.txt          # Project dependencies
README.md                # This file
```

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Creating Notifications

```python
from src.notifications.models import NotificationCreate, NotificationType
from src.notifications.storage import NotificationStorage

# Initialize storage
storage = NotificationStorage()

# Create a notification
notification_data = NotificationCreate(
    user_id="user_123",
    notification_type=NotificationType.INFO,
    title="Welcome!",
    message="Thank you for joining our platform",
    metadata={"source": "onboarding"},
    action_url="https://example.com/getting-started"
)

notification = await storage.create_notification(notification_data)
```

### Retrieving Notifications

```python
# Get a specific notification
notification = await storage.get_notification(notification_id)

# Get all notifications for a user
notifications = await storage.get_user_notifications("user_123")

# Get unread notifications only
unread = await storage.get_user_notifications(
    "user_123",
    status=NotificationStatus.UNREAD
)

# Get with pagination
page1 = await storage.get_user_notifications(
    "user_123",
    limit=10,
    offset=0
)
```

### Managing Notification Status

```python
# Mark a notification as read
await storage.mark_notification_as_read(notification_id)

# Mark all user notifications as read
count = await storage.mark_all_user_notifications_as_read("user_123")

# Get unread count
unread_count = await storage.get_user_unread_count("user_123")
```

### Updating and Deleting

```python
from src.notifications.models import NotificationUpdate, NotificationStatus

# Update a notification
update_data = NotificationUpdate(
    title="Updated Title",
    status=NotificationStatus.ARCHIVED
)
updated = await storage.update_notification(notification_id, update_data)

# Delete a notification
deleted = await storage.delete_notification(notification_id)
```

### Cleanup Expired Notifications

```python
# Delete all expired notifications
deleted_count = await storage.cleanup_expired_notifications()
```

## Data Models

### Notification

The main notification model with the following fields:

- `id` (UUID): Unique identifier
- `user_id` (str): User who receives the notification
- `notification_type` (NotificationType): Type of notification
- `title` (str): Notification title (max 200 chars)
- `message` (str): Notification content (max 1000 chars)
- `status` (NotificationStatus): Current status (default: unread)
- `created_at` (datetime): Creation timestamp
- `read_at` (datetime, optional): When marked as read
- `archived_at` (datetime, optional): When archived
- `metadata` (dict): Custom metadata
- `action_url` (str, optional): URL for action button
- `expires_at` (datetime, optional): Expiration timestamp

### NotificationStatus Enum

- `UNREAD`: Notification hasn't been read
- `READ`: Notification has been read
- `ARCHIVED`: Notification has been archived

### NotificationType Enum

- `INFO`: Informational notification
- `SUCCESS`: Success message
- `WARNING`: Warning message
- `ERROR`: Error notification
- `SYSTEM`: System notification
- `USER_ACTION`: User action required
- `REMINDER`: Reminder notification

## Database Setup

### Using SQLite (Development)

SQLite is used by default:

```python
from src.notifications.database import create_database_engine, create_tables

engine = create_database_engine()
create_tables(engine)
```

### Using PostgreSQL (Production)

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/notifications"
```

Then create the tables:

```python
from src.notifications.database import create_database_engine, create_tables

engine = create_database_engine()
create_tables(engine)
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/notifications

# Run specific test file
pytest tests/test_notification_models.py

# Run with verbose output
pytest -v
```

## Environment Variables

- `DATABASE_URL`: Database connection string (default: `sqlite:///./notifications.db`)
- `DATABASE_ECHO`: Enable SQLAlchemy SQL logging (default: `false`)

## Architecture

### Storage Layer

The storage layer uses an abstract interface pattern, allowing for multiple backend implementations:

- **InMemoryNotificationStorage**: For development and testing
- **Database Storage** (future): For production use with SQLAlchemy

### Data Validation

All models use Pydantic for automatic validation:
- Type checking
- Field constraints (min/max length)
- Required vs optional fields
- Default values

## API Methods

### NotificationStorage

- `create_notification(data)`: Create a new notification
- `get_notification(id)`: Get notification by ID
- `get_user_notifications(user_id, status, limit, offset)`: Get user's notifications
- `update_notification(id, data)`: Update a notification
- `delete_notification(id)`: Delete a notification
- `mark_notification_as_read(id)`: Mark as read
- `mark_all_user_notifications_as_read(user_id)`: Mark all as read
- `get_user_unread_count(user_id)`: Get unread count
- `cleanup_expired_notifications()`: Delete expired notifications

## Best Practices

1. **Never hardcode user IDs**: Always use IDs from authentication system
2. **Set expiration for time-sensitive notifications**: Use `expires_at` field
3. **Use appropriate notification types**: Choose the right type for better UI rendering
4. **Add meaningful metadata**: Store additional context for processing
5. **Regular cleanup**: Schedule periodic cleanup of expired notifications
6. **Handle pagination**: Use limit/offset for large notification lists

## Future Enhancements

- WebSocket real-time notification delivery
- Email/SMS notification channels
- Notification templates
- Bulk operations
- Advanced filtering and search
- Notification preferences per user
- Read receipts and delivery confirmation

## License

This implementation is part of the SDT1-22 ticket for in-app notification storage and data model.

## PM Agent Chat Interface - Feature Brief Submission

Provides a chat-based interface for product managers to submit and manage feature briefs with validation, priority levels, and status tracking. Supports creating draft briefs, submitting for review, and listing briefs by user with full type safety and comprehensive validation.

## Dependency Management

Define and visualize story execution order with dependency graph management. The `DependencyGraph` class manages dependencies between stories, detects cycles, and calculates execution order using topological sorting. The `DependencyVisualizer` class provides multiple visualization formats including ASCII trees, Mermaid diagrams, DOT format, and JSON structures, with execution summaries showing parallelization opportunities and dependency levels.

## Email Notifications for Account Registration

This module provides email notification functionality for account registration events. It includes a flexible `RegistrationEmailNotifier` that works with any email provider implementation through the `EmailProvider` protocol, customizable email templates via the `EmailTemplate` base class, and a pre-built `WelcomeEmailTemplate` for standard registration welcome emails with optional email verification links.

## Notification Preferences Management

Provides a flexible interface for managing user notification preferences across multiple channels (email, SMS, push, in-app, webhook) and categories (security, account, marketing, updates, alerts, social). Supports global channel overrides, category-specific settings, and quiet hours configuration for granular control over notification delivery.