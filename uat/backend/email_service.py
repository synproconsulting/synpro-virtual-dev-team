"""Email service for sending transactional emails."""

import os
import logging
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────────

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "SynPro Virtual Dev Team")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


# ── Email Service ────────────────────────────────────────────────────────────────

async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an email via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional, defaults to stripped HTML)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning(
            "SMTP credentials not configured - email not sent to %s",
            to_email
        )
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        
        # Add text and HTML parts
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)
        
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        
        logger.info("Email sent successfully to %s", to_email)
        return True
        
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, str(e))
        return False


async def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send a password reset email with a reset link.
    
    Args:
        to_email: User's email address
        reset_token: Password reset token
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = "Reset Your Password - SynPro Virtual Dev Team"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
            <h2 style="color: #2c3e50; margin-top: 0;">Password Reset Request</h2>
            <p>You requested to reset your password for your SynPro Virtual Dev Team account.</p>
            <p>Click the button below to reset your password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                    Reset Password
                </a>
            </div>
            <p style="color: #666; font-size: 14px;">
                Or copy and paste this link into your browser:<br>
                <a href="{reset_url}" style="color: #007bff; word-break: break-all;">{reset_url}</a>
            </p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                This link will expire in 1 hour. If you didn't request this password reset, you can safely ignore this email.
            </p>
            <p style="color: #666; font-size: 12px;">
                For security reasons, never share this link with anyone.
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
Password Reset Request

You requested to reset your password for your SynPro Virtual Dev Team account.

Visit this link to reset your password:
{reset_url}

This link will expire in 1 hour. If you didn't request this password reset, you can safely ignore this email.

For security reasons, never share this link with anyone.
    """
    
    return await send_email(to_email, subject, html_content, text_content)
