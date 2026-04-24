# Email Notifications for Account Registration

This module provides email notification functionality for account registration events. It sends automated welcome emails to new users and optional notifications to administrators.

## Features

- **Welcome Emails**: Automated welcome emails sent to newly registered users
- **Admin Notifications**: Optional notifications to administrators about new registrations
- **HTML & Plain Text**: Emails support both HTML and plain text formats
- **Configurable**: SMTP settings configurable via environment variables or code
- **Logging**: Comprehensive logging of email sending operations
- **Type Safe**: Full type hints for better IDE support and type checking

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (optional):
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export FROM_EMAIL="noreply@yourcompany.com"
export FROM_NAME="Your Company"
```

## Usage

### Basic Usage

Send a welcome email to a newly registered user:

```python
from src.auth.email_notifications import send_registration_notification

# Send welcome email to user only
results = send_registration_notification(
    user_name="John Doe",
    user_email="john.doe@example.com"
)

print(results["user_email"])  # True if successful
```

### With Admin Notification

Send welcome email to user and notification to admin:

```python
from src.auth.email_notifications import send_registration_notification

results = send_registration_notification(
    user_name="John Doe",
    user_email="john.doe@example.com",
    admin_email="admin@yourcompany.com"
)

print(results["user_email"])   # True if user email sent
print(results["admin_email"])  # True if admin email sent
```

### Advanced Usage

Use the service class directly for more control:

```python
from datetime import datetime
from src.auth.email_notifications import RegistrationEmailService, EmailConfig

# Custom configuration
config = EmailConfig(
    smtp_host="smtp.example.com",
    smtp_port=587,
    smtp_username="notifications@example.com",
    smtp_password="secure-password",
    from_email="noreply@example.com",
    from_name="Example Platform"
)

# Create service
service = RegistrationEmailService(config)

# Send welcome email
success = service.send_welcome_email(
    user_name="Jane Smith",
    user_email="jane@example.com",
    registration_date=datetime.utcnow()
)

# Send admin notification
admin_success = service.send_admin_notification(
    user_name="Jane Smith",
    user_email="jane@example.com",
    registration_date=datetime.utcnow(),
    admin_email="admin@example.com"
)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `localhost` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USERNAME` | SMTP authentication username | `""` |
| `SMTP_PASSWORD` | SMTP authentication password | `""` |
| `FROM_EMAIL` | Sender email address | `noreply@example.com` |
| `FROM_NAME` | Sender display name | `Registration Service` |

### Using Gmail

To use Gmail as your SMTP server:

1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password
3. Set environment variables:
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/auth --cov-report=html

# Run specific test file
pytest tests/test_email_notifications.py

# Run with verbose output
pytest -v
```

## Email Templates

### Welcome Email

The welcome email includes:
- Personalized greeting with user's name
- Account confirmation message
- Account details (email, registration date)
- Security notice
- Company branding

### Admin Notification

The admin notification includes:
- New user's name and email
- Registration timestamp
- Clean, professional formatting

## Error Handling

The service handles errors gracefully:
- Returns `True` on successful send, `False` on failure
- Logs all errors for debugging
- Does not raise exceptions (uses return values)
- Continues processing even if one notification fails

## Security Considerations

- **Never commit credentials**: Use environment variables for sensitive data
- **Use app passwords**: Don't use your main email password
- **Enable TLS**: The service uses STARTTLS for secure connections
- **Validate inputs**: Ensure email addresses are validated before passing to this service
- **Rate limiting**: Consider implementing rate limiting in production

## Architecture

```
src/auth/
├── __init__.py                  # Module exports
└── email_notifications.py       # Email notification service

tests/
├── __init__.py
└── test_email_notifications.py  # Comprehensive unit tests
```

## Dependencies

- Python 3.11+
- Standard library modules: `smtplib`, `email`, `logging`
- Dev dependencies: `pytest`, `pytest-cov`, `pytest-mock`

## Contributing

1. Write clean, type-hinted code
2. Add docstrings to all public functions
3. Include unit tests for new features
4. Run tests before committing
5. Follow PEP 8 style guidelines

## License

Copyright © 2024. All rights reserved.
