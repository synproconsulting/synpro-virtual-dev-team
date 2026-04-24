"""
API routes for user account deletion.

Provides REST API endpoints for deleting user accounts,
supporting both authenticated self-deletion and admin-initiated deletion.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DeleteUserRequest:
    """Request model for user deletion."""
    
    def __init__(
        self,
        user_id: str,
        force_hard_delete: bool = False,
        confirmation_token: Optional[str] = None
    ):
        """
        Initialize delete user request.
        
        Args:
            user_id: ID of user to delete
            force_hard_delete: Whether to force hard deletion
            confirmation_token: Optional confirmation token for verification
        """
        self.user_id = user_id
        self.force_hard_delete = force_hard_delete
        self.confirmation_token = confirmation_token


class DeleteUserResponse:
    """Response model for user deletion."""
    
    def __init__(
        self,
        success: bool,
        user_id: str,
        deletion_type: str,
        deleted_at: str,
        message: str
    ):
        """
        Initialize delete user response.
        
        Args:
            success: Whether deletion was successful
            user_id: ID of deleted user
            deletion_type: Type of deletion (soft/hard)
            deleted_at: Timestamp of deletion
            message: Human-readable message
        """
        self.success = success
        self.user_id = user_id
        self.deletion_type = deletion_type
        self.deleted_at = deleted_at
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "success": self.success,
            "user_id": self.user_id,
            "deletion_type": self.deletion_type,
            "deleted_at": self.deleted_at,
            "message": self.message
        }


class UserDeletionRoutes:
    """
    Handler class for user deletion API routes.
    
    Provides methods that can be integrated with web frameworks
    like FastAPI, Flask, or Django.
    """
    
    def __init__(self, deletion_service: Any):
        """
        Initialize routes handler.
        
        Args:
            deletion_service: UserDeletionService instance
        """
        self.deletion_service = deletion_service
    
    def delete_current_user(
        self,
        current_user_id: str,
        force_hard_delete: bool = False,
        confirmation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle DELETE request for current authenticated user.
        
        Args:
            current_user_id: ID of the authenticated user
            force_hard_delete: Whether to force hard deletion
            confirmation_token: Optional confirmation token
            
        Returns:
            Response dictionary
        """
        try:
            # Verify confirmation token if required
            if not self._verify_confirmation(
                current_user_id, 
                confirmation_token
            ):
                return {
                    "success": False,
                    "error": "Invalid or missing confirmation token",
                    "status_code": 400
                }
            
            result = self.deletion_service.delete_user(
                user_id=current_user_id,
                requesting_user_id=current_user_id,
                force_hard_delete=force_hard_delete
            )
            
            response = DeleteUserResponse(
                success=True,
                user_id=result["user_id"],
                deletion_type=result["deletion_type"],
                deleted_at=result["deleted_at"],
                message="Your account has been successfully deleted"
            )
            
            return {
                **response.to_dict(),
                "status_code": 200
            }
            
        except Exception as e:
            logger.error(f"Error deleting current user: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }
    
    def delete_user_by_admin(
        self,
        admin_user_id: str,
        target_user_id: str,
        force_hard_delete: bool = False,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle DELETE request by admin for another user.
        
        Args:
            admin_user_id: ID of the admin user
            target_user_id: ID of the user to delete
            force_hard_delete: Whether to force hard deletion
            reason: Optional reason for deletion
            
        Returns:
            Response dictionary
        """
        try:
            result = self.deletion_service.delete_user(
                user_id=target_user_id,
                requesting_user_id=admin_user_id,
                force_hard_delete=force_hard_delete
            )
            
            # Log admin action
            self._log_admin_action(
                admin_user_id=admin_user_id,
                target_user_id=target_user_id,
                action="delete_user",
                reason=reason
            )
            
            response = DeleteUserResponse(
                success=True,
                user_id=result["user_id"],
                deletion_type=result["deletion_type"],
                deleted_at=result["deleted_at"],
                message=f"User {target_user_id} has been deleted"
            )
            
            return {
                **response.to_dict(),
                "status_code": 200
            }
            
        except Exception as e:
            logger.error(
                f"Error deleting user {target_user_id} by admin: {str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }
    
    def anonymize_current_user(
        self,
        current_user_id: str,
        confirmation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle anonymization request for current user.
        
        Args:
            current_user_id: ID of the authenticated user
            confirmation_token: Optional confirmation token
            
        Returns:
            Response dictionary
        """
        try:
            if not self._verify_confirmation(
                current_user_id, 
                confirmation_token
            ):
                return {
                    "success": False,
                    "error": "Invalid or missing confirmation token",
                    "status_code": 400
                }
            
            result = self.deletion_service.anonymize_user(current_user_id)
            
            return {
                "success": True,
                "user_id": result["user_id"],
                "anonymized": result["anonymized"],
                "anonymized_at": result["anonymized_at"],
                "message": "Your account has been anonymized",
                "status_code": 200
            }
            
        except Exception as e:
            logger.error(f"Error anonymizing current user: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }
    
    def _verify_confirmation(
        self,
        user_id: str,
        confirmation_token: Optional[str]
    ) -> bool:
        """
        Verify confirmation token for deletion.
        
        Args:
            user_id: User ID to verify
            confirmation_token: Confirmation token to check
            
        Returns:
            True if valid or not required, False otherwise
        """
        # Check if confirmation is required
        require_confirmation = True  # Could be configurable
        
        if not require_confirmation:
            return True
        
        if not confirmation_token:
            return False
        
        # In production, verify token against stored value
        # This is a simplified implementation
        expected_token = f"confirm_delete_{user_id}"
        return confirmation_token == expected_token
    
    def _log_admin_action(
        self,
        admin_user_id: str,
        target_user_id: str,
        action: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Log administrative action for audit trail.
        
        Args:
            admin_user_id: ID of admin performing action
            target_user_id: ID of affected user
            action: Type of action performed
            reason: Optional reason for action
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "admin_user_id": admin_user_id,
            "target_user_id": target_user_id,
            "action": action,
            "reason": reason
        }
        
        logger.info(f"Admin action logged: {log_entry}")
        
        # In production, this would be stored in an audit log table


def create_deletion_routes(deletion_service: Any) -> UserDeletionRoutes:
    """
    Factory function to create user deletion routes handler.
    
    Args:
        deletion_service: UserDeletionService instance
        
    Returns:
        UserDeletionRoutes instance
    """
    return UserDeletionRoutes(deletion_service)
