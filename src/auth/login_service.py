"""User login service with credential verification."""

from dataclasses import dataclass
from typing import Optional
from src.auth.credentials import Credentials
from src.auth.password_hasher import PasswordHasher
from src.auth.user_repository import UserRepository


@dataclass(frozen=True)
class LoginResult:
    """Result of a login attempt."""
    
    success: bool
    username: Optional[str] = None
    user_id: Optional[str] = None
    error_message: Optional[str] = None


class LoginService:
    """Service for handling user authentication."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: Optional[PasswordHasher] = None
    ) -> None:
        """Initialize login service.
        
        Args:
            user_repository: Repository for user data access
            password_hasher: Password hasher instance (uses default if None)
        """
        self.user_repository = user_repository
        self.password_hasher = password_hasher or PasswordHasher()
    
    def login(self, credentials: Credentials) -> LoginResult:
        """Authenticate user with provided credentials.
        
        Args:
            credentials: User credentials to verify
            
        Returns:
            LoginResult indicating success or failure with details
        """
        try:
            # Retrieve user record
            user = self.user_repository.get_user_by_username(credentials.username)
            
            if user is None:
                return LoginResult(
                    success=False,
                    error_message="Invalid username or password"
                )
            
            # Check if user account is active
            if not user.is_active:
                return LoginResult(
                    success=False,
                    error_message="Account is inactive"
                )
            
            # Verify password
            password_valid = self.password_hasher.verify_password(
                credentials.password,
                user.password_hash,
                user.salt
            )
            
            if not password_valid:
                return LoginResult(
                    success=False,
                    error_message="Invalid username or password"
                )
            
            # Successful login
            return LoginResult(
                success=True,
                username=user.username,
                user_id=user.user_id
            )
            
        except ValueError as e:
            # Handle credential validation errors
            return LoginResult(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            # Handle unexpected errors
            return LoginResult(
                success=False,
                error_message="An error occurred during login"
            )
