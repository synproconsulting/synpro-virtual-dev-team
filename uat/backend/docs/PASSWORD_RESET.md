# Password Reset Flow

This document describes the secure password reset flow implemented in the UAT backend.

## Overview

The password reset flow allows users to securely reset their password by receiving a unique, time-limited token via email. This implementation follows security best practices to prevent common vulnerabilities.

## Flow Diagram

```
User                    Frontend                Backend                 Email Service
  |                        |                       |                         |
  |-- Request Reset ------>|                       |                         |
  |                        |-- POST /auth/         |                         |
  |                        |   password-reset/     |                         |
  |                        |   request             |                         |
  |                        |                       |-- Generate Token ------>|
  |                        |                       |                         |
  |                        |<-- Success Response --|                         |
  |                        |                       |                         |
  |<-------------------- Email with Reset Link -------------------------|
  |                        |                       |                         |
  |-- Click Link --------->|                       |                         |
  |                        |                       |                         |
  |-- Enter New Password ->|                       |                         |
  |                        |-- POST /auth/         |                         |
  |                        |   password-reset/     |                         |
  |                        |   complete            |                         |
  |                        |                       |-- Validate Token ------>|
  |                        |                       |-- Update Password ----->|
  |                        |                       |-- Mark Token Used ----->|
  |                        |<-- Success Response --|                         |
  |<-- Confirmation -------|                       |                         |
```

## API Endpoints

### 1. Request Password Reset

**Endpoint:** `POST /auth/password-reset/request`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "If that email exists in our system, a password reset link has been sent"
}
```

**Notes:**
- Always returns the same success message, regardless of whether the email exists
- This prevents email enumeration attacks
- If the email exists, a token is generated and sent via email
- Tokens expire after 1 hour

### 2. Complete Password Reset

**Endpoint:** `POST /auth/password-reset/complete`

**Request Body:**
```json
{
  "token": "uuid-token-from-email",
  "new_password": "NewSecurePassword123!"
}
```

**Success Response:** `200 OK`
```json
{
  "message": "Password reset successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid token, expired token, already used token, or weak password
- Token validation errors include:
  - "Invalid reset token"
  - "Token already used"
  - "Token has expired"
  - Password validation errors

## Security Features

### 1. Email Enumeration Prevention
The API always returns the same success message regardless of whether the email exists in the system. This prevents attackers from using the endpoint to discover valid email addresses.

### 2. Token Security
- Tokens are UUIDs (128-bit random values)
- Tokens are single-use only
- Tokens expire after 1 hour
- Tokens are marked as "used" after successful password reset
- Used or expired tokens cannot be reused

### 3. Password Requirements
The new password must meet the following requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

### 4. Email Delivery
- Emails are sent asynchronously to avoid blocking the API response
- Email failures are logged but don't expose information to the user
- HTML and plain text versions are provided for compatibility

### 5. Rate Limiting
The password reset endpoints are protected by the global rate limiter to prevent abuse.

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=SynPro Virtual Dev Team

# Frontend URL (for reset links)
FRONTEND_URL=http://localhost:3000
```

### Gmail Setup

If using Gmail:

1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification
   - App passwords
   - Generate a password for "Mail"
3. Use the app password as `SMTP_PASSWORD`

### Other SMTP Providers

For other providers (SendGrid, AWS SES, etc.):
- Update `SMTP_HOST` and `SMTP_PORT` accordingly
- Adjust authentication if needed (see `email_service.py`)

## Database Schema

### password_reset_tokens Table

```sql
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
```

## Email Template

The password reset email includes:

- Clear subject line: "Reset Your Password - SynPro Virtual Dev Team"
- Prominent reset button linking to the frontend
- Plain URL as fallback
- Expiration notice (1 hour)
- Security warnings:
  - Ignore if not requested
  - Never share the link
- Both HTML and plain text versions

## Testing

Run the test suite:

```bash
# Run all password reset tests
pytest uat/backend/tests/test_password_reset.py -v

# Run email service tests
pytest uat/backend/tests/test_email_service.py -v

# Run all tests
pytest uat/backend/tests/ -v
```

## Frontend Integration

### Request Password Reset

```typescript
const requestPasswordReset = async (email: string) => {
  const response = await fetch('/auth/password-reset/request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  
  const data = await response.json();
  // Always show success message to user
  return data.message;
};
```

### Complete Password Reset

```typescript
const completePasswordReset = async (token: string, newPassword: string) => {
  const response = await fetch('/auth/password-reset/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password: newPassword })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Password reset failed');
  }
  
  return await response.json();
};
```

### Frontend Pages

1. **Request Page** (`/forgot-password`):
   - Email input field
   - Submit button
   - Display generic success message after submission

2. **Reset Page** (`/reset-password?token=...`):
   - Extract token from URL query parameter
   - New password input field
   - Confirm password input field
   - Display password requirements
   - Submit button
   - Handle errors (expired token, weak password, etc.)

## Troubleshooting

### Emails Not Being Sent

1. **Check SMTP credentials:**
   ```bash
   # Verify environment variables are set
   echo $SMTP_USERNAME
   echo $SMTP_HOST
   ```

2. **Check logs:**
   ```bash
   # Look for email-related errors
   tail -f logs/app.log | grep -i email
   ```

3. **Test SMTP connection:**
   ```python
   import aiosmtplib
   import asyncio
   
   async def test_smtp():
       await aiosmtplib.send(
           message,
           hostname="smtp.gmail.com",
           port=587,
           username="your-email@gmail.com",
           password="your-app-password",
           start_tls=True,
       )
   
   asyncio.run(test_smtp())
   ```

### Token Not Working

1. **Check token expiration:**
   - Tokens expire after 1 hour
   - Request a new token if expired

2. **Check if token was already used:**
   - Tokens are single-use only
   - Request a new token if needed

3. **Verify token in database:**
   ```sql
   SELECT * FROM password_reset_tokens 
   WHERE token = 'your-token-here';
   ```

## Security Considerations

### Do NOT:
- Return different messages for existing vs. non-existing emails
- Return the token in the API response (email only)
- Allow token reuse
- Set long expiration times (> 1 hour)
- Skip password validation

### DO:
- Log all password reset attempts for auditing
- Monitor for suspicious patterns (many requests from same IP)
- Use HTTPS in production
- Implement rate limiting
- Invalidate all sessions after password change (future enhancement)
- Consider adding IP/device verification (future enhancement)

## Future Enhancements

Potential improvements for the password reset flow:

1. **Session Invalidation:** Invalidate all active sessions when password is reset
2. **Device Verification:** Send notification to known devices when password is reset
3. **IP Logging:** Track IP addresses for reset requests
4. **Account Lockout:** Temporarily lock account after multiple failed reset attempts
5. **Two-Factor Authentication:** Require 2FA code in addition to email token
6. **Password History:** Prevent reuse of recent passwords
7. **Security Questions:** Add security questions as additional verification
