# Security Guidelines

## Password Reset Security (SDT1-62)

### Overview
The password reset flow is designed with security as a top priority. This document outlines the security measures implemented to protect user accounts.

### Key Security Principles

#### 1. Token Never in API Response
**CRITICAL:** The password reset token must NEVER be returned in any API response body.

- ✅ **Correct:** Token sent only via email
- ❌ **Incorrect:** Token returned in API response JSON

**Implementation:**
- The `/auth/password-reset/request` endpoint returns only a `MessageResponse` with a generic success message
- The actual token is generated internally and sent via email using `send_password_reset_email()`
- Response model explicitly constrains the response to `{"message": "..."}`

**Code Example:**
```python
@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(req: ResetRequestModel, db=Depends(get_db)):
    # Generate token
    token = str(uuid.uuid4())
    
    # Send via email (secure channel)
    await send_password_reset_email(req.email.lower(), token)
    
    # NEVER return token in response
    return MessageResponse(message="If that email exists in our system, a password reset link has been sent")
```

#### 2. Email Enumeration Prevention
The API returns the same message regardless of whether the email exists in the system. This prevents attackers from using the password reset endpoint to discover which emails are registered.

**Standard Message:**
```
"If that email exists in our system, a password reset link has been sent"
```

This message is returned in ALL cases:
- Email exists and reset email sent successfully
- Email exists but email sending failed
- Email does not exist in the system

#### 3. Token Security Properties
All password reset tokens must have the following security properties:

- **Single-use:** Token is marked as `used=true` after successful password reset
- **Time-limited:** Token expires 1 hour after generation
- **Unpredictable:** Generated using UUID v4 (cryptographically random)
- **Validated:** Token existence, expiry, and used status checked before accepting reset

#### 4. Logging Security
Sensitive information is never logged:

- ✅ **Log:** "Password reset requested for email: user@example.com"
- ❌ **Never log:** The actual reset token value
- ❌ **Never log:** User passwords (old or new)

#### 5. Email as Secure Channel
The reset token is transmitted only through email, which serves as:
- **Identity verification:** User must have access to registered email
- **Secure transport:** Token not exposed to API clients/logs
- **User notification:** Account owner is alerted to reset attempt

### Testing Security Requirements

Security tests are implemented in `tests/test_password_reset.py`:

1. **test_request_password_reset_token_not_in_response:** Explicitly verifies token is never in API response
2. **test_request_password_reset_nonexistent_user_no_token_in_response:** Verifies same behavior for non-existent users
3. **test_request_password_reset_response_model_structure:** Validates response model contains only 'message' field
4. **test_complete_password_reset_response_model_structure:** Validates completion endpoint response structure

### Security Checklist for Code Reviews

When reviewing password reset code changes, verify:

- [ ] Token is never returned in any API response
- [ ] Token is never logged (even at DEBUG level)
- [ ] Same generic message returned for all request outcomes
- [ ] Response models explicitly constrain response structure
- [ ] Token has expiry and single-use enforcement
- [ ] Email is the only transmission channel for tokens
- [ ] Tests verify token absence from responses

### Related Tickets
- **SDT1-62:** Remove password reset token from API response body
- Related security tickets should be listed here as implemented

### Last Updated
2024 - SDT1-62 Implementation
