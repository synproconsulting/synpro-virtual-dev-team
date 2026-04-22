"""
User registration service with email and password validation.
"""
from typing import Tuple, Optional
from src.auth.models import User
from src.auth.validators import EmailValidator, PasswordValidator
from src.auth.password_hasher import PasswordHasher
from src.auth.storage import UserStorage


class RegistrationError(Exception):
    """Custom exception for registration errors."""
    pass


class UserRegistration:
    """
    Handles user registration with email and password validation.
    
    Provides methods to register new users with proper validation
    and secure password hashing.
    """
    
    def __init__(
        self,
        storage: Optional[UserStorage] = None,
        password_hasher: Optional[PasswordHasher] = None,
    ):
        """
        Initialize the registration service.
        
        Args:
            storage: User storage instance (creates new if not provided)
            password_hasher: Password hasher instance (creates new if not provided)
        """
        self.storage = storage or UserStorage()
        self.password_hasher = password_hasher or PasswordHasher()
        self.email_validator = EmailValidator()
        self.password_validator = PasswordValidator()
    
    def register_user(self, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user with email and password.
        
        Args:
            email: User's email address
            password: User's plaintext password
            
        Returns:
            Tuple of (success, message, user)
            - success: Boolean indicating if registration succeeded
            - message: Success or error message
            - user: User object if successful, None otherwise
        """
        # Validate email
        email_valid, email_error = self.email_validator.validate(email)
        if not email_valid:
            return False, email_error, None
        
        # Normalize email
        email = email.strip().lower()
        
        # Check if email already exists
        if self.storage.email_exists(email):
            return False, "Email address is already registered", None
        
        # Validate password
        password_valid, password_error = self.password_validator.validate(password)
        if not password_valid:
            return False, password_error, None
        
        # Hash password
        password_hash = self.password_hasher.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
        )
        
        # Save user
        self.storage.save_user(user)
        
        return True, "User registered successfully", user
    
    def register_user_strict(self, email: str, password: str) -> User:
        """
        Register a new user with email and password (strict mode).
        
        This method raises exceptions on validation errors instead of
        returning error tuples.
        
        Args:
            email: User's email address
            password: User's plaintext password
            
        Returns:
            The created User object
            
        Raises:
            RegistrationError: If validation fails or email already exists
        """
        success, message, user = self.register_user(email, password)
        
        if not success:
            raise RegistrationError(message)
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Args:
            email: The user's email address
            
        Returns:
            User object if found, None otherwise
        """
        return self.storage.get_user_by_email(email)
    
    def verify_credentials(self, email: str, password: str) -> Tuple[bool, Optional[User]]:
        """
        Verify user credentials for login.
        
        Args:
            email: User's email address
            password: User's plaintext password
            
        Returns:
            Tuple of (is_valid, user)
            - is_valid: True if credentials are correct
            - user: User object if valid, None otherwise
        """
        user = self.storage.get_user_by_email(email)
        
        if not user:
            return False, None
        
        if self.password_hasher.verify_password(password, user.password_hash):
            return True, user
        
        return False, None
