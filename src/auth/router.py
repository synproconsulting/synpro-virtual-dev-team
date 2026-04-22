"""
FastAPI router for authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from src.auth.database import get_db
from src.auth.schemas import (
    UserCreate, UserResponse, Token, PasswordResetRequest,
    PasswordResetConfirm, MessageResponse
)
from src.auth.service import AuthService
from src.auth.security import create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    service = AuthService(db)
    user = service.get_user_by_email(email)
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user data
        
    Raises:
        HTTPException: If email already exists
    """
    service = AuthService(db)
    try:
        user = service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token.
    
    Args:
        form_data: Login credentials (username as email, password)
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    service = AuthService(db)
    user = service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset(request_data: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Request a password reset token.
    
    Args:
        request_data: Password reset request with email
        db: Database session
        
    Returns:
        Success message
        
    Note:
        Always returns success even if email doesn't exist (security best practice)
    """
    service = AuthService(db)
    token = service.create_password_reset_token(request_data.email)
    
    # In production, send token via email instead of returning it
    # Always return success to prevent email enumeration
    message = "If the email exists, a password reset link has been sent"
    
    # For development/testing purposes, you might want to log or return the token
    # In production, this should be sent via email
    if token:
        # TODO: Send email with reset token
        pass
    
    return {"message": message}


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(reset_data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Reset password using a reset token.
    
    Args:
        reset_data: Reset token and new password
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    service = AuthService(db)
    success = service.reset_password(reset_data.token, reset_data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password has been reset successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        Current user data
    """
    return current_user
