"""
User account deletion module.

Provides functionality to delete user accounts with proper validation,
authentication, and cascade deletion of related data.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserDeletionError(Exception):
    """Raised when user deletion fails."""
    pass


class UserNotFoundError(UserDeletionError):
    """Raised when the user to be deleted is not found."""
    pass


class UnauthorizedDeletionError(UserDeletionError):
    """Raised when deletion is attempted without proper authorization."""
    pass


class UserDeletionService:
    """
    Service for handling user account deletion.
    
    Provides methods to safely delete user accounts with proper
    validation, authorization checks, and cascade deletion of
    related user data.
    """
    
    def __init__(self, database_connection: Any = None):
        """
        Initialize the user deletion service.
        
        Args:
            database_connection: Database connection object for persistence
        """
        self.db = database_connection
        self.soft_delete_enabled = os.getenv(
            "SOFT_DELETE_ENABLED", 
            "true"
        ).lower() == "true"
    
    def delete_user(
        self,
        user_id: str,
        requesting_user_id: str,
        force_hard_delete: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a user account.
        
        Args:
            user_id: ID of the user to delete
            requesting_user_id: ID of the user requesting deletion
            force_hard_delete: If True, perform hard delete regardless of settings
            
        Returns:
            Dictionary containing deletion details
            
        Raises:
            UserNotFoundError: If user does not exist
            UnauthorizedDeletionError: If requester lacks permission
            UserDeletionError: If deletion fails
        """
        # Validate authorization
        if not self._is_authorized(user_id, requesting_user_id):
            logger.warning(
                f"Unauthorized deletion attempt: user {requesting_user_id} "
                f"tried to delete user {user_id}"
            )
            raise UnauthorizedDeletionError(
                "You are not authorized to delete this account"
            )
        
        # Check if user exists
        user = self._get_user(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        # Determine deletion type
        perform_hard_delete = force_hard_delete or not self.soft_delete_enabled
        
        try:
            if perform_hard_delete:
                result = self._hard_delete_user(user_id)
            else:
                result = self._soft_delete_user(user_id)
            
            logger.info(
                f"User {user_id} deleted successfully "
                f"({'hard' if perform_hard_delete else 'soft'} delete)"
            )
            
            return {
                "user_id": user_id,
                "deletion_type": "hard" if perform_hard_delete else "soft",
                "deleted_at": datetime.utcnow().isoformat(),
                "success": True,
                **result
            }
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise UserDeletionError(f"Deletion failed: {str(e)}")
    
    def _is_authorized(
        self, 
        user_id: str, 
        requesting_user_id: str
    ) -> bool:
        """
        Check if the requesting user is authorized to delete the account.
        
        Args:
            user_id: ID of user to delete
            requesting_user_id: ID of user requesting deletion
            
        Returns:
            True if authorized, False otherwise
        """
        # User can delete their own account
        if user_id == requesting_user_id:
            return True
        
        # Check if requesting user is admin
        requesting_user = self._get_user(requesting_user_id)
        if requesting_user and requesting_user.get("is_admin", False):
            return True
        
        return False
    
    def _get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user from database.
        
        Args:
            user_id: User ID to retrieve
            
        Returns:
            User dictionary or None if not found
        """
        if self.db is None:
            # Mock implementation for testing
            return {"id": user_id, "is_admin": False}
        
        # Real database implementation would go here
        try:
            return self.db.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}")
            return None
    
    def _soft_delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Perform soft delete (mark as deleted without removing data).
        
        Args:
            user_id: ID of user to soft delete
            
        Returns:
            Dictionary with soft delete details
        """
        deleted_at = datetime.utcnow()
        
        if self.db is None:
            # Mock implementation
            return {
                "marked_deleted": True,
                "data_retained": True
            }
        
        # Update user record to mark as deleted
        self.db.update_user(
            user_id,
            {
                "deleted_at": deleted_at,
                "is_active": False,
                "status": "deleted"
            }
        )
        
        return {
            "marked_deleted": True,
            "data_retained": True
        }
    
    def _hard_delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Perform hard delete (permanently remove user and related data).
        
        Args:
            user_id: ID of user to hard delete
            
        Returns:
            Dictionary with hard delete details
        """
        if self.db is None:
            # Mock implementation
            return {
                "user_removed": True,
                "sessions_removed": True,
                "data_removed": True
            }
        
        # Delete related data in correct order
        deleted_sessions = self.db.delete_user_sessions(user_id)
        deleted_tokens = self.db.delete_user_tokens(user_id)
        deleted_profile = self.db.delete_user_profile(user_id)
        
        # Finally delete the user record
        self.db.delete_user(user_id)
        
        return {
            "user_removed": True,
            "sessions_removed": deleted_sessions,
            "tokens_removed": deleted_tokens,
            "profile_removed": deleted_profile,
            "data_removed": True
        }
    
    def anonymize_user(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize user data instead of deleting (GDPR-compliant alternative).
        
        Args:
            user_id: ID of user to anonymize
            
        Returns:
            Dictionary with anonymization details
            
        Raises:
            UserNotFoundError: If user does not exist
            UserDeletionError: If anonymization fails
        """
        user = self._get_user(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        try:
            anonymized_data = {
                "email": f"deleted_{user_id}@anonymized.local",
                "username": f"deleted_user_{user_id}",
                "first_name": "Deleted",
                "last_name": "User",
                "phone": None,
                "is_active": False,
                "anonymized_at": datetime.utcnow()
            }
            
            if self.db:
                self.db.update_user(user_id, anonymized_data)
            
            logger.info(f"User {user_id} anonymized successfully")
            
            return {
                "user_id": user_id,
                "anonymized": True,
                "anonymized_at": anonymized_data["anonymized_at"].isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Failed to anonymize user {user_id}: {str(e)}")
            raise UserDeletionError(f"Anonymization failed: {str(e)}")


def delete_user_account(
    user_id: str,
    requesting_user_id: str,
    database_connection: Any = None,
    force_hard_delete: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to delete a user account.
    
    Args:
        user_id: ID of the user to delete
        requesting_user_id: ID of the user requesting deletion
        database_connection: Database connection object
        force_hard_delete: If True, perform hard delete
        
    Returns:
        Dictionary containing deletion details
        
    Raises:
        UserNotFoundError: If user does not exist
        UnauthorizedDeletionError: If requester lacks permission
        UserDeletionError: If deletion fails
    """
    service = UserDeletionService(database_connection)
    return service.delete_user(user_id, requesting_user_id, force_hard_delete)
