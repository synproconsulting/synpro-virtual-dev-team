"""Authentication router - extracted from main.py (SDT1-47 refactor).

Updated for SDT1-63: Hardened JWT secret key handling.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
import os
import uuid
import hashlib
import hmac
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
import jwt
import logging

from email_service import send_password_reset_email
from jwt_config import get_jwt_config, JWTConfigError

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Initialize JWT config (validates on startup)
try:
    jwt_config = get_jwt_config()
except JWTConfigError as e:
    logger.error(f"❌ JWT configuration error: {e}")
    raise


# ── Database ────────────────────────────────────────────────────────────────────────

def get_db():
    """Get a database connection."""
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Database not configured")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


# ── Helpers ─────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256.
    
    Args:
        password: Plain text password
        
    Returns:
        Salted hash in format "salt_hex:key_hex"
    """
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored: str) -> bool:
    """
    Verify a password against a stored hash.
    
    Args:
        password: Plain text password to verify
        stored: Stored hash in format "salt_hex:key_hex"
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        key  = bytes.fromhex(key_hex)
        new  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return hmac.compare_digest(key, new)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False


def create_jwt(user_id: str, email: str) -> str:
    """
    Create a JWT token for a user.
    
    Uses hardened JWT configuration with validated secret keys.
    
    Args:
        user_id: User ID
        email: User email
        
    Returns:
        Encoded JWT token
        
    Raises:
        HTTPException: If token creation fails
    """
    try:
        return jwt_config.create_token(user_id, email)
    except JWTConfigError as e:
        logger.error(f"Failed to create JWT token for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")


def decode_jwt(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Supports key rotation - validates with current and old secrets.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        return jwt_config.decode_token(token)
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Authentication error")


def validate_password(password: str) -> list[str]:
    """
    Validate password complexity requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    if len(password) < 8:
        errors.append("Minimum 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("At least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("At least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("At least one number")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("At least one special character")
    return errors


# ── Request / Response models ────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    str
    password: str
    username: str = ""


class LoginRequest(BaseModel):
    email:    str
    password: str


class ResetRequestModel(BaseModel):
    email: str


class ResetCompleteModel(BaseModel):
    token:        str
    new_password: str


class UserResponse(BaseModel):
    id:         str
    email:      str
    username:   str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse


# ── Router ────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db=Depends(get_db)):
    """
    Register a new user account.
    
    Validates password complexity and creates a JWT token.
    """
    errors = validate_password(req.password)
    if errors:
        raise HTTPException(status_code=400,
                            detail={"message": "Password requirements not met",
                                    "errors": errors})

    username = req.username or req.email.split("@")[0]
    cur      = db.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s", (req.email.lower(),))
    if cur.fetchone():
        raise HTTPException(status_code=409,
                            detail="An account with this email already exists")

    user_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO users (id, email, username, password_hash) VALUES (%s, %s, %s, %s)",
        (user_id, req.email.lower(), username, hash_password(req.password))
    )
    db.commit()

    logger.info(f"User registered: {user_id} ({req.email.lower()})")
    token = create_jwt(user_id, req.email.lower())
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=req.email.lower(),
                          username=username,
                          created_at=datetime.now(timezone.utc).isoformat())
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db=Depends(get_db)):
    """
    Authenticate a user and return a JWT token.
    
    Validates credentials and creates a new JWT token.
    """
    cur = db.cursor()
    cur.execute(
        "SELECT id, email, username, password_hash, created_at FROM users WHERE email = %s",
        (req.email.lower(),)
    )
    user = cur.fetchone()

    if not user or not verify_password(req.password, user["password_hash"]):
        logger.warning(f"Failed login attempt for email: {req.email.lower()}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    logger.info(f"User logged in: {user['id']} ({user['email']})")
    token = create_jwt(str(user["id"]), user["email"])
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=str(user["id"]), email=user["email"],
                          username=user["username"],
                          created_at=user["created_at"].isoformat())
    )


@router.post("/password-reset/request")
async def request_password_reset(req: ResetRequestModel, db=Depends(get_db)):
    """
    Request a password reset token.
    
    Generates a reset token and sends it to the user's email address.
    For security, always returns success message even if email doesn't exist.
    """
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (req.email.lower(),))
    user = cur.fetchone()

    # Always return the same message to prevent email enumeration
    response_message = "If that email exists in our system, a password reset link has been sent"

    if not user:
        logger.info("Password reset requested for non-existent email: %s", req.email.lower())
        return {"message": response_message}

    # Generate reset token
    token      = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    cur.execute(
        "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
        (str(user["id"]), token, expires_at)
    )
    db.commit()

    # Send email with reset token
    try:
        email_sent = await send_password_reset_email(req.email.lower(), token)
        if email_sent:
            logger.info("Password reset email sent to %s", req.email.lower())
        else:
            logger.warning("Failed to send password reset email to %s", req.email.lower())
    except Exception as e:
        logger.error("Error sending password reset email to %s: %s", req.email.lower(), str(e))
    
    return {"message": response_message}


@router.post("/password-reset/complete")
def complete_password_reset(req: ResetCompleteModel, db=Depends(get_db)):
    """
    Complete the password reset using a valid token.
    
    Validates the token and updates the user's password.
    """
    cur = db.cursor()
    cur.execute(
        """SELECT t.id, t.user_id, t.expires_at, t.used
           FROM password_reset_tokens t
           WHERE t.token = %s""",
        (req.token,)
    )
    token_row = cur.fetchone()

    if not token_row:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    if token_row["used"]:
        raise HTTPException(status_code=400, detail="Token already used")
    if token_row["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token has expired")

    errors = validate_password(req.new_password)
    if errors:
        raise HTTPException(status_code=400,
                            detail={"message": "Password requirements not met",
                                    "errors": errors})

    cur.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (hash_password(req.new_password), str(token_row["user_id"]))
    )
    cur.execute(
        "UPDATE password_reset_tokens SET used = TRUE WHERE id = %s",
        (str(token_row["id"]),)
    )
    db.commit()
    
    logger.info("Password reset completed for user_id: %s", str(token_row["user_id"]))
    return {"message": "Password reset successfully"}


@router.get("/me")
def get_current_user(
    authorization: str | None = Header(None),
    db=Depends(get_db),
):
    """
    Get current authenticated user information.
    
    Validates JWT token and returns user data.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization[7:]
    payload = decode_jwt(token)

    cur = db.cursor()
    cur.execute(
        "SELECT id, email, username, created_at FROM users WHERE id = %s",
        (payload["sub"],)
    )
    user = cur.fetchone()
    if not user:
        logger.warning(f"Token valid but user not found: {payload['sub']}")
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(id=str(user["id"]), email=user["email"],
                        username=user["username"],
                        created_at=user["created_at"].isoformat())
