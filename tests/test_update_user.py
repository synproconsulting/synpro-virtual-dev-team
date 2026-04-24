"""
Unit tests for user update functionality.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from src.auth.update_user import (
    UserUpdateService,
    ValidationError,
    AuthenticationError,
    UserNotFoundError,
    UserUpdateError,
    validate_email,
    validate_username,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
)
from src.auth.user_repository import InMemoryUserRepository


@pytest.fixture
def user_repository():
    """Create a fresh user repository for each test."""
    return InMemoryUserRepository()


@pytest.fixture
def user_service(user_repository):
    """Create a user update service instance."""
    return UserUpdateService(user_repository)


@pytest.fixture
def test_user(user_repository):
    """Create a test user in the repository."""
    return user_repository.create(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_here"
    )


@pytest.fixture
def valid_token(test_user):
    """Create a valid JWT token for the test user."""
    payload = {
        "sub": str(test_user["id"]),
        "username": test_user["username"],
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


class TestValidateEmail:
    """Test email validation function."""
    
    def test_valid_email(self):
        """Test that valid email formats are accepted."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user@example.co.uk") is True
        assert validate_email("user+tag@example.com") is True
    
    def test_invalid_email(self):
        """Test that invalid email formats are rejected."""
        assert validate_email("invalid") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("user@.com") is False
        assert validate_email("") is False


class TestValidateUsername:
    """Test username validation function."""
    
    def test_valid_username(self):
        """Test that valid usernames are accepted."""
        assert validate_username("user123") is True
        assert validate_username("test_user") is True
        assert validate_username("user-name") is True
        assert validate_username("abc") is True
    
    def test_invalid_username(self):
        """Test that invalid usernames are rejected."""
        assert validate_username("ab") is False  # Too short
        assert validate_username("a" * 31) is False  # Too long
        assert validate_username("user@name") is False  # Invalid character
        assert validate_username("user name") is False  # Space not allowed
        assert validate_username("") is False  # Empty


class TestVerifyToken:
    """Test JWT token verification."""
    
    def test_valid_token(self, valid_token, test_user):
        """Test that valid tokens are verified correctly."""
        payload = verify_token(valid_token)
        assert payload["sub"] == str(test_user["id"])
        assert payload["username"] == test_user["username"]
    
    def test_invalid_token(self):
        """Test that invalid tokens raise AuthenticationError."""
        with pytest.raises(AuthenticationError):
            verify_token("invalid.token.here")
    
    def test_expired_token(self, test_user):
        """Test that expired tokens are rejected."""
        payload = {
            "sub": str(test_user["id"]),
            "username": test_user["username"],
            "exp": datetime.utcnow() - timedelta(minutes=1)  # Expired
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(AuthenticationError):
            verify_token(expired_token)
    
    def test_token_missing_user_id(self):
        """Test that tokens without user ID are rejected."""
        payload = {
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(AuthenticationError, match="missing user ID"):
            verify_token(token)


class TestUpdateUsername:
    """Test username update functionality."""
    
    def test_update_username_success(self, user_service, test_user, valid_token):
        """Test successful username update."""
        new_username = "newusername"
        result = user_service.update_username(test_user["id"], new_username, valid_token)
        
        assert result["username"] == new_username
        assert result["email"] == test_user["email"]
        assert result["id"] == test_user["id"]
    
    def test_update_username_invalid_format(self, user_service, test_user, valid_token):
        """Test that invalid username format raises ValidationError."""
        with pytest.raises(ValidationError):
            user_service.update_username(test_user["id"], "ab", valid_token)
        
        with pytest.raises(ValidationError):
            user_service.update_username(test_user["id"], "user@name", valid_token)
    
    def test_update_username_already_taken(self, user_service, user_repository, test_user, valid_token):
        """Test that updating to an existing username raises error."""
        # Create another user
        other_user = user_repository.create(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed"
        )
        
        with pytest.raises(UserUpdateError, match="already taken"):
            user_service.update_username(test_user["id"], "otheruser", valid_token)
    
    def test_update_username_user_not_found(self, user_service, valid_token):
        """Test that updating non-existent user raises error."""
        # Create token for non-existent user
        payload = {
            "sub": "999",
            "username": "nonexistent",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(UserNotFoundError):
            user_service.update_username(999, "newname", token)
    
    def test_update_username_unauthorized(self, user_service, user_repository, test_user, valid_token):
        """Test that users cannot update other users' usernames."""
        # Create another user
        other_user = user_repository.create(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed"
        )
        
        # Try to update other user's username with test_user's token
        with pytest.raises(AuthenticationError, match="Unauthorized"):
            user_service.update_username(other_user["id"], "newname", valid_token)


class TestUpdateEmail:
    """Test email update functionality."""
    
    def test_update_email_success(self, user_service, test_user, valid_token):
        """Test successful email update."""
        new_email = "newemail@example.com"
        result = user_service.update_email(test_user["id"], new_email, valid_token)
        
        assert result["email"] == new_email
        assert result["username"] == test_user["username"]
        assert result["id"] == test_user["id"]
    
    def test_update_email_invalid_format(self, user_service, test_user, valid_token):
        """Test that invalid email format raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            user_service.update_email(test_user["id"], "invalid-email", valid_token)
        
        with pytest.raises(ValidationError):
            user_service.update_email(test_user["id"], "@example.com", valid_token)
    
    def test_update_email_already_taken(self, user_service, user_repository, test_user, valid_token):
        """Test that updating to an existing email raises error."""
        # Create another user
        other_user = user_repository.create(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed"
        )
        
        with pytest.raises(UserUpdateError, match="already taken"):
            user_service.update_email(test_user["id"], "other@example.com", valid_token)
    
    def test_update_email_user_not_found(self, user_service, valid_token):
        """Test that updating non-existent user raises error."""
        # Create token for non-existent user
        payload = {
            "sub": "999",
            "username": "nonexistent",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(UserNotFoundError):
            user_service.update_email(999, "new@example.com", token)
    
    def test_update_email_unauthorized(self, user_service, user_repository, test_user, valid_token):
        """Test that users cannot update other users' emails."""
        # Create another user
        other_user = user_repository.create(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed"
        )
        
        # Try to update other user's email with test_user's token
        with pytest.raises(AuthenticationError, match="Unauthorized"):
            user_service.update_email(other_user["id"], "new@example.com", valid_token)


class TestUpdateUserProfile:
    """Test combined profile update functionality."""
    
    def test_update_profile_both_fields(self, user_service, test_user, valid_token):
        """Test updating both username and email."""
        result = user_service.update_user_profile(
            test_user["id"],
            username="newusername",
            email="newemail@example.com",
            token=valid_token
        )
        
        assert result["username"] == "newusername"
        assert result["email"] == "newemail@example.com"
        assert result["id"] == test_user["id"]
    
    def test_update_profile_username_only(self, user_service, test_user, valid_token):
        """Test updating only username."""
        result = user_service.update_user_profile(
            test_user["id"],
            username="newusername",
            token=valid_token
        )
        
        assert result["username"] == "newusername"
        assert result["email"] == test_user["email"]  # Email unchanged
    
    def test_update_profile_email_only(self, user_service, test_user, valid_token):
        """Test updating only email."""
        result = user_service.update_user_profile(
            test_user["id"],
            email="newemail@example.com",
            token=valid_token
        )
        
        assert result["email"] == "newemail@example.com"
        assert result["username"] == test_user["username"]  # Username unchanged
    
    def test_update_profile_no_fields(self, user_service, test_user, valid_token):
        """Test that updating without any fields raises error."""
        with pytest.raises(ValidationError, match="At least one field"):
            user_service.update_user_profile(test_user["id"], token=valid_token)
    
    def test_update_profile_invalid_username(self, user_service, test_user, valid_token):
        """Test that invalid username in profile update raises error."""
        with pytest.raises(ValidationError):
            user_service.update_user_profile(
                test_user["id"],
                username="ab",  # Too short
                token=valid_token
            )
    
    def test_update_profile_invalid_email(self, user_service, test_user, valid_token):
        """Test that invalid email in profile update raises error."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            user_service.update_user_profile(
                test_user["id"],
                email="invalid",
                token=valid_token
            )
    
    def test_update_profile_username_taken(self, user_service, user_repository, test_user, valid_token):
        """Test that updating to taken username raises error."""
        # Create another user
        user_repository.create(
            username="takenuser",
            email="taken@example.com",
            hashed_password="hashed"
        )
        
        with pytest.raises(UserUpdateError, match="Username is already taken"):
            user_service.update_user_profile(
                test_user["id"],
                username="takenuser",
                token=valid_token
            )
    
    def test_update_profile_email_taken(self, user_service, user_repository, test_user, valid_token):
        """Test that updating to taken email raises error."""
        # Create another user
        user_repository.create(
            username="otheruser",
            email="taken@example.com",
            hashed_password="hashed"
        )
        
        with pytest.raises(UserUpdateError, match="Email is already taken"):
            user_service.update_user_profile(
                test_user["id"],
                email="taken@example.com",
                token=valid_token
            )
