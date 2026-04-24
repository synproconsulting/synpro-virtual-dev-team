# Email Notifications for Authentication Events

## Overview

This module provides email notification functionality for authentication-related events, including:
- Password reset requests
- Login alerts
- Password change confirmations

## Features

- **Password Reset Emails**: Send secure password reset links with expiration warnings
- **Login Alerts**: Notify users of new logins with device and location information
- **Password Changed Notifications**: Confirm password changes with security warnings
- **HTML and Plain Text**: All emails sent in both formats for maximum compatibility
- **Configurable SMTP**: Easy configuration via environment variables or constructor parameters

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USERNAME=your_username
export SMTP_PASSWORD=your_password
export FROM_EMAIL=noreply@example.com
export PASSWORD_RESET_URL=https://yourapp.com/reset-password
```

## Usage

### Basic Example

```python
from src.auth.email_notifications import EmailNotificationService

# Initialize the service
email_service = EmailNotificationService(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your_email@gmail.com",
    smtp_password="your_app_password",
    from_email="noreply@yourapp.com"
)

# Send password reset email
success = email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_token="secure_random_token_here",
    reset_url_base="https://yourapp.com/reset-password"
)

# Send login alert
from datetime import datetime

success = email_service.send_login_alert_email(
    to_email="user@example.com",
    login_time=datetime.utcnow(),
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    location="New York, USA"
)

# Send password changed confirmation
success = email_service.send_password_changed_email(
    to_email="user@example.com"
)
```

### Using Environment Variables

```python
from src.auth.email_notifications import EmailNotificationService

# Service will automatically use environment variables
email_service = EmailNotificationService()

# Use the service
email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_token="token123"
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
| `PASSWORD_RESET_URL` | Base URL for password reset | `https://example.com/reset-password` |

### Security Considerations

- **Never commit credentials**: Always use environment variables for sensitive data
- **Use app-specific passwords**: For Gmail and similar services, use app-specific passwords
- **Enable TLS**: The service uses STARTTLS for secure connections
- **Token expiration**: Password reset tokens should expire (mentioned in email, implement server-side)
- **Rate limiting**: Implement rate limiting on the application side to prevent abuse

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_email_notifications.py

# Run with verbose output
pytest -v tests/
```

## Email Templates

All emails include:
- Professional HTML templates with inline CSS
- Plain text fallback versions
- Clear call-to-action buttons (in HTML version)
- Security warnings and instructions
- Consistent branding elements

### Customization

To customize email templates, modify the HTML and text content in the respective methods:
- `send_password_reset_email()` - Password reset template
- `send_login_alert_email()` - Login alert template  
- `send_password_changed_email()` - Password changed template

## Error Handling

The service includes comprehensive error handling:
- All methods return `bool` indicating success/failure
- Errors are logged using Python's logging module
- SMTP exceptions are caught and logged
- Failed emails return `False` without raising exceptions

## API Reference

### EmailNotificationService

#### `__init__(smtp_host, smtp_port, smtp_username, smtp_password, from_email)`
Initialize the email notification service with SMTP configuration.

#### `send_password_reset_email(to_email, reset_token, reset_url_base) -> bool`
Send a password reset email with a secure reset link.

#### `send_login_alert_email(to_email, login_time, ip_address, user_agent, location) -> bool`
Send a login alert notification with login details.

#### `send_password_changed_email(to_email) -> bool`
Send a confirmation email after password change.

## Integration Examples

### Flask Integration

```python
from flask import Flask, request
from src.auth.email_notifications import EmailNotificationService

app = Flask(__name__)
email_service = EmailNotificationService()

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')
    # Generate reset token (implement your token generation)
    reset_token = generate_reset_token(email)
    
    # Send email
    success = email_service.send_password_reset_email(
        to_email=email,
        reset_token=reset_token
    )
    
    if success:
        return {'message': 'Password reset email sent'}, 200
    return {'error': 'Failed to send email'}, 500
```

### Django Integration

```python
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from src.auth.email_notifications import EmailNotificationService

email_service = EmailNotificationService()

@receiver(user_logged_in)
def send_login_notification(sender, request, user, **kwargs):
    email_service.send_login_alert_email(
        to_email=user.email,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
    )
```

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please contact the development team.
