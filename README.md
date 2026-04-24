# Notification Service and Email Integration

A comprehensive notification service with email integration capabilities for Python applications.

## Features

- **Email Notifications**: Send emails via SMTP with support for:
  - Plain text and HTML emails
  - CC and BCC recipients
  - File attachments
  - Custom reply-to addresses
  
- **Pre-built Templates**: Common notification templates including:
  - Welcome emails
  - Password reset emails
  - Email verification emails
  
- **Notification Tracking**: Track all sent notifications with:
  - Status monitoring (sent, failed, pending, queued)
  - Historical records
  - Metadata storage
  - Searchable history

- **Extensible Architecture**: Easy to add new notification channels (SMS, push notifications, etc.)

- **Testing Support**: Mock email provider for testing without sending real emails

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# SMTP Configuration
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export SMTP_USE_TLS=true
```

## Usage

### Basic Email Sending

```python
from src.notifications import NotificationService

# Initialize service (uses environment variables)
service = NotificationService()

# Send a simple email
record = service.send_email(
    to=["recipient@example.com"],
    subject="Hello",
    body="This is a test email",
    from_email="sender@example.com"
)

print(f"Email sent with status: {record.status}")
```

### Send HTML Email

```python
html_body = """
<html>
<body>
    <h1>Welcome!</h1>
    <p>This is an HTML email.</p>
</body>
</html>
"""

record = service.send_email(
    to=["recipient@example.com"],
    subject="HTML Email",
    body=html_body,
    from_email="sender@example.com",
    html=True
)
```

### Send Email with Attachments

```python
record = service.send_email(
    to=["recipient@example.com"],
    subject="Document Attached",
    body="Please find the document attached.",
    from_email="sender@example.com",
    attachments=["/path/to/document.pdf"]
)
```

### Pre-built Email Templates

#### Welcome Email
```python
record = service.send_welcome_email(
    to_email="newuser@example.com",
    user_name="John Doe",
    from_email="noreply@example.com"
)
```

#### Password Reset Email
```python
record = service.send_password_reset_email(
    to_email="user@example.com",
    reset_token="secure-token-123",
    reset_url="https://yourapp.com/reset",
    from_email="noreply@example.com"
)
```

#### Email Verification
```python
record = service.send_verification_email(
    to_email="user@example.com",
    verification_token="verify-token-456",
    verification_url="https://yourapp.com/verify",
    from_email="noreply@example.com"
)
```

### Notification History

```python
# Get all notifications
history = service.get_notification_history()

# Filter by type
email_history = service.get_notification_history(notification_type="email")

# Filter by status
from src.notifications.models import NotificationStatus
sent_notifications = service.get_notification_history(status=NotificationStatus.SENT)

# Get recent notifications
recent = service.get_notification_history(limit=10)

# Get specific notification by ID
notification = service.get_notification_by_id("notification-id-123")
```

### Using Mock Provider for Testing

```python
from src.notifications import NotificationService, MockEmailProvider

# Initialize with mock provider
mock_provider = MockEmailProvider()
service = NotificationService(email_provider=mock_provider)

# Send emails (won't actually send, just logs and stores)
service.send_email(
    to=["test@example.com"],
    subject="Test",
    body="Testing",
    from_email="sender@example.com"
)

# Check sent emails
print(f"Sent {len(mock_provider.sent_emails)} emails")
for email in mock_provider.sent_emails:
    print(f"To: {email.to}, Subject: {email.subject}")

# Clear mock data
mock_provider.clear()
```

### Custom Email Provider

You can implement your own email provider by extending the `EmailProvider` base class:

```python
from src.notifications.email_provider import EmailProvider
from src.notifications.models import EmailMessage

class CustomEmailProvider(EmailProvider):
    def send_email(self, message: EmailMessage) -> bool:
        # Your custom implementation
        # Return True on success, False on failure
        pass
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/notifications tests/

# Run specific test file
pytest tests/test_notification_service.py

# Run with verbose output
pytest -v
```

## Project Structure

```
├── src/
│   └── notifications/
│       ├── __init__.py          # Package exports
│       ├── models.py            # Data models
│       ├── email_provider.py    # Email provider implementations
│       └── service.py           # Main notification service
├── tests/
│   ├── __init__.py
│   ├── test_models.py           # Model tests
│   ├── test_email_provider.py   # Provider tests
│   └── test_notification_service.py  # Service tests
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMTP_HOST` | SMTP server hostname | - | Yes |
| `SMTP_PORT` | SMTP server port | 587 | No |
| `SMTP_USERNAME` | SMTP authentication username | - | Yes |
| `SMTP_PASSWORD` | SMTP authentication password | - | Yes |
| `SMTP_USE_TLS` | Whether to use TLS encryption | true | No |

## Security Best Practices

1. **Never commit credentials**: Always use environment variables for sensitive data
2. **Use app passwords**: For Gmail, use app-specific passwords instead of your main password
3. **Enable TLS**: Always use TLS encryption for SMTP connections
4. **Validate inputs**: The service validates email data, but always sanitize user inputs
5. **Rate limiting**: Consider implementing rate limiting for production use

## Error Handling

The service handles errors gracefully and returns notification records with error information:

```python
record = service.send_email(...)

if record.status == NotificationStatus.FAILED:
    print(f"Email failed: {record.error_message}")
else:
    print(f"Email sent successfully at {record.sent_at}")
```

## Contributing

1. Write tests for new features
2. Follow PEP 8 style guidelines
3. Add type hints to all functions
4. Update documentation

## License

MIT License
