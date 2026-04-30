# Changelog

All notable changes to the UAT backend will be documented in this file.

## [SDT1-50] - Password Reset Flow - Email Only

### Added
- **Email Service Module** (`email_service.py`):
  - Async SMTP email sending using `aiosmtplib`
  - `send_email()` function for generic email sending
  - `send_password_reset_email()` for password reset emails with branded HTML template
  - Comprehensive error handling and logging
  - Support for both HTML and plain text email formats

- **Enhanced Password Reset Flow** (`auth.py`):
  - Updated `/auth/password-reset/request` endpoint to send tokens via email only
  - Removed direct token exposure in API responses (security improvement)
  - Added email enumeration protection (same response for existing/non-existing emails)
  - Added comprehensive logging for security audit trail
  - Made password reset request handler async to support email sending

- **SMTP Configuration** (`.env.example`):
  - `SMTP_HOST` - SMTP server hostname
  - `SMTP_PORT` - SMTP server port (default: 587)
  - `SMTP_USERNAME` - SMTP authentication username
  - `SMTP_PASSWORD` - SMTP authentication password
  - `SMTP_FROM_EMAIL` - Sender email address
  - `SMTP_FROM_NAME` - Sender display name

- **Dependencies** (`requirements.txt`):
  - `aiosmtplib==3.0.1` - Async SMTP client
  - `email-validator==2.1.0` - Email validation utilities

- **Test Suite**:
  - `tests/test_password_reset.py` - Comprehensive tests for password reset flow:
    - Request reset for existing users
    - Request reset for non-existent users
    - Email failure handling
    - Token validation (invalid, used, expired)
    - Password strength validation
    - Case-insensitive email handling
  - `tests/test_email_service.py` - Email service tests:
    - Successful email sending
    - Missing credentials handling
    - SMTP failure handling
    - HTML-only and multipart emails
    - Password reset email content validation
    - Email structure validation

- **Documentation** (`docs/PASSWORD_RESET.md`):
  - Complete flow diagram
  - API endpoint specifications
  - Security features documentation
  - Configuration guide
  - Frontend integration examples
  - Troubleshooting guide
  - Future enhancement ideas

### Changed
- **Password Reset Request Endpoint**:
  - Changed from synchronous to asynchronous (`async def`)
  - No longer returns token in response body
  - Returns consistent message for security (prevents email enumeration)
  - Sends password reset link via email instead

### Security Improvements
- **Email Enumeration Prevention**: Same response message regardless of email existence
- **No Token Exposure**: Tokens are never returned in API responses
- **Comprehensive Logging**: All password reset attempts are logged for audit
- **Email Validation**: Added email validation library for better email handling
- **Single-Use Tokens**: Existing token validation ensures one-time use
- **Time-Limited Tokens**: Existing 1-hour expiration maintained

### Migration Notes
- **Breaking Change**: The `/auth/password-reset/request` endpoint no longer returns the token in the response
- **Required Configuration**: SMTP credentials must be configured for password reset to work
- **Backward Compatibility**: The `/auth/password-reset/complete` endpoint remains unchanged

### Testing
Run the test suite to verify the implementation:
```bash
# Run all password reset tests
pytest uat/backend/tests/test_password_reset.py -v

# Run email service tests  
pytest uat/backend/tests/test_email_service.py -v

# Run all tests
pytest uat/backend/tests/ -v
```

### Deployment Checklist
- [ ] Update environment variables with SMTP credentials
- [ ] Test email delivery in staging environment
- [ ] Verify password reset flow end-to-end
- [ ] Update frontend to remove any token display logic
- [ ] Monitor logs for email delivery issues
- [ ] Document SMTP provider setup for team

### Known Issues
None at this time.

### Future Enhancements
- Session invalidation on password reset
- Device/IP verification
- Account lockout after multiple failed attempts
- Two-factor authentication integration
- Password history to prevent reuse
