# Security Guidelines

## Password Reset Token Security (SDT1-62)

### Overview
Password reset tokens are sensitive credentials that must be protected from exposure. This document outlines the security measures implemented to ensure tokens are never leaked through API responses.

### Implementation

#### Password Reset Request (`POST /auth/password-reset/request`)

**Security Measures:**
1. **No Token in Response**: The reset token is NEVER included in the API response body
2. **Email-Only Delivery**: Tokens are only sent to the user's verified email address
3. **Generic Response**: Always returns the same message regardless of whether the email exists (prevents email enumeration)
4. **No Logging of Tokens**: The actual token value is never written to logs

**Response Format:**
```json
{
  "message": "If that email exists in our system, a password reset link has been sent"
}
```

**Why This Matters:**
- Prevents token exposure through browser developer tools
- Prevents token logging in application logs or monitoring systems
- Prevents token caching by CDNs or proxies
- Prevents token exposure in client-side code
- Reduces risk of token interception

#### Password Reset Complete (`POST /auth/password-reset/complete`)

**Security Measures:**
1. **No Token Echo**: The token submitted in the request is never echoed back in the response
2. **Success-Only Response**: Only returns a success or error message
3. **Token Validation**: Ensures token is valid, unused, and not expired before accepting

**Response Format:**
```json
{
  "message": "Password reset successfully"
}
```

### Testing

Security tests are implemented in `tests/test_auth_security.py` to verify:

1. ✅ Token never appears in response body
2. ✅ Token never appears in response headers
3. ✅ Token never appears in logs
4. ✅ Same response for existent and non-existent emails
5. ✅ Token only delivered via email

Run security tests:
```bash
cd uat/backend
pytest tests/test_auth_security.py -v
```

### Best Practices

#### For Developers

1. **Never return tokens in API responses** - Tokens should only be sent via secure, out-of-band channels (email, SMS)
2. **Use generic error messages** - Don't reveal whether an email/user exists
3. **Log user IDs, not tokens** - When logging, use `user_id` instead of sensitive tokens
4. **Validate early, fail secure** - Check token validity before performing any operations

#### Code Review Checklist

When reviewing password reset code, verify:
- [ ] Response models don't include token fields
- [ ] Log statements don't include token values
- [ ] Error messages don't reveal token validity
- [ ] Same response returned for valid/invalid emails
- [ ] Tokens expire after reasonable time (1 hour)
- [ ] Tokens are single-use only

### Related Tickets

- **SDT1-62**: Remove password reset token from API response body (this implementation)
- **SDT1-63**: JWT secret validation and configuration hardening
- **SDT1-56**: CORS configuration hardening

### References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Password Reset Guide](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
