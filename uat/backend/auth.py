"""Authentication router - extracted from main.py (SDT1-47 refactor)."""

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

# ── Config ────────────────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")
JWT_SECRET   = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_EXPIRY   = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))


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
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        key  = bytes.fromhex(key_hex)
        new  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return hmac.compare_digest(key, new)
    except Exception:
        return False


def create_jwt(user_id: str, email: str) -> str:
    payload = {
        "sub":   user_id,
        "email": email,
        "iat":   datetime.now(timezone.utc),
        "exp":   datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def validate_password(password: str) -> list[str]:
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

    token = create_jwt(user_id, req.email.lower())
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=req.email.lower(),
                          username=username,
                          created_at=datetime.now(timezone.utc).isoformat())
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT id, email, username, password_hash, created_at FROM users WHERE email = %s",
        (req.email.lower(),)
    )
    user = cur.fetchone()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_jwt(str(user["id"]), user["email"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=str(user["id"]), email=user["email"],
                          username=user["username"],
                          created_at=user["created_at"].isoformat())
    )


@router.post("/password-reset/request")
def request_password_reset(req: ResetRequestModel, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (req.email.lower(),))
    user = cur.fetchone()

    if not user:
        return {"message": "If that email exists, a reset link has been sent"}

    token      = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    cur.execute(
        "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
        (str(user["id"]), token, expires_at)
    )
    db.commit()

    return {"message": "Reset token generated",
            "token": token,
            "note": "UAT mode: token returned directly instead of emailed"}


@router.post("/password-reset/complete")
def complete_password_reset(req: ResetCompleteModel, db=Depends(get_db)):
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
    return {"message": "Password reset successfully"}


@router.get("/me")
def get_current_user(
    authorization: str | None = Header(None),
    db=Depends(get_db),
):
    # C-3 fix: Header(None) reads from the Authorization HTTP header, not a query param
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    cur = db.cursor()
    cur.execute(
        "SELECT id, email, username, created_at FROM users WHERE id = %s",
        (payload["sub"],)
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(id=str(user["id"]), email=user["email"],
                        username=user["username"],
                        created_at=user["created_at"].isoformat())
