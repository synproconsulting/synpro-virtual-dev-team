"""
backend/main.py
───────────────
FastAPI application for the SynPro Virtual Dev Team UAT environment.
Wraps the auth module with a REST API and PostgreSQL persistence.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from contextlib import asynccontextmanager
import os
import uuid
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
import jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db, init_db
from models import User, PasswordResetToken

# ── Config ─────────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")
JWT_SECRET   = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_EXPIRY   = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")


# ── App setup ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    if DATABASE_URL:
        print("✓ Database configured. Use 'alembic upgrade head' to run migrations.")
    else:
        print("WARNING: DATABASE_URL not set — running without database")
    yield

app = FastAPI(
    title="SynPro Virtual Dev Team — Auth API",
    description="UAT environment for the authentication module",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class ResetPasswordRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class ConfirmResetRequest(BaseModel):
    """Confirm password reset request."""
    token: str
    new_password: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + pwdhash.hex()


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        stored_password: Hashed password from database
        provided_password: Plain text password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    salt = bytes.fromhex(stored_password[:64])
    stored_hash = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash.hex() == stored_hash


def create_jwt(user_id: str, email: str) -> str:
    """Create a JWT token for a user.
    
    Args:
        user_id: User's UUID
        email: User's email address
        
    Returns:
        JWT token string
    """
    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def generate_reset_token() -> str:
    """Generate a secure random token for password reset.
    
    Returns:
        Random token string
    """
    return hashlib.sha256(os.urandom(32)).hexdigest()


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "auth-api", "version": "1.0.0"}


@app.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user.
    
    Args:
        req: Registration request with email, username, and password
        db: Database session
        
    Returns:
        Success message and JWT token
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    # Validate input
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(req.username) < 2:
        raise HTTPException(status_code=400, detail="Username must be at least 2 characters")

    # Check if user exists
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=req.email,
        username=req.username,
        password_hash=hash_password(req.password)
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

    token = create_jwt(user.id, user.email)
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username
        }
    }


@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user.
    
    Args:
        req: Login request with email and password
        db: Database session
        
    Returns:
        JWT token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user or not verify_password(user.password_hash, req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_jwt(user.id, user.email)
    return {
        "token": token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username
        }
    }


@app.post("/auth/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Initiate password reset process.
    
    Args:
        req: Password reset request with email
        db: Database session
        
    Returns:
        Reset token (in production, this would be sent via email)
    """
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset token has been sent"}

    # Generate reset token
    token = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(reset_token)
    db.commit()

    # In production, send this via email
    return {
        "message": "Password reset token generated",
        "token": token,  # Remove this in production
        "expires_at": expires_at.isoformat()
    }


@app.post("/auth/confirm-reset")
def confirm_reset(req: ConfirmResetRequest, db: Session = Depends(get_db)):
    """Confirm password reset with token.
    
    Args:
        req: Confirm reset request with token and new password
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Find valid token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == req.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
    ).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Update password
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(req.new_password)
    reset_token.used = True
    
    db.commit()

    return {"message": "Password reset successfully"}


@app.get("/auth/verify")
def verify_token(token: str):
    """Verify a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Token payload if valid
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
