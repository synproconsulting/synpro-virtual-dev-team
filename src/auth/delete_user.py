"""
User account deletion module.

This module provides functionality for deleting user accounts from the system,
including proper validation, authorization, and cleanup of user data.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


class UserDeletionError(Exception):
    """Exception raised when user deletion fails."""
    pass


class UserNotFoundError(Exception):
    """Exception raised when user is not found."""
    pass


class UnauthorizedDeletionError(Exception):
    """Exception raised when user is not authorized to delete account."""
    pass


def get_database_connection():
    """
    Get a database connection using environment variables.
    
    Returns:
        psycopg2.connection: Database connection object
        
    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432')
    )


def verify_user_exists(user_id: int, cursor) -> Dict[str, Any]:
    """
    Verify that a user exists in the database.
    
    Args:
        user_id: The ID of the user to verify
        cursor: Database cursor
        
    Returns:
        Dict containing user information
        
    Raises:
        UserNotFoundError: If user is not found
    """
    cursor.execute(
        "SELECT id, email, username, is_active FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()
    
    if not user:
        raise UserNotFoundError(f"User with ID {user_id} not found")
    
    return dict(user)


def verify_deletion_authorization(
    user_id: int,
    requesting_user_id: int,
    is_admin: bool = False
) -> None:
    """
    Verify that the requesting user is authorized to delete the account.
    
    Args:
        user_id: The ID of the user to be deleted
        requesting_user_id: The ID of the user requesting deletion
        is_admin: Whether the requesting user is an admin
        
    Raises:
        UnauthorizedDeletionError: If user is not authorized
    """
    if not is_admin and user_id != requesting_user_id:
        raise UnauthorizedDeletionError(
            "Users can only delete their own accounts unless they are admins"
        )


def soft_delete_user(user_id: int, cursor) -> None:
    """
    Soft delete a user by marking them as inactive and anonymizing data.
    
    Args:
        user_id: The ID of the user to soft delete
        cursor: Database cursor
    """
    deleted_timestamp = datetime.utcnow()
    anonymized_email = f"deleted_{user_id}_{int(deleted_timestamp.timestamp())}@deleted.local"
    
    cursor.execute(
        """
        UPDATE users 
        SET is_active = FALSE,
            email = %s,
            username = %s,
            deleted_at = %s
        WHERE id = %s
        """,
        (anonymized_email, f"deleted_user_{user_id}", deleted_timestamp, user_id)
    )
    
    logger.info(f"Soft deleted user {user_id} at {deleted_timestamp}")


def hard_delete_user(user_id: int, cursor) -> None:
    """
    Permanently delete a user and all associated data.
    
    Args:
        user_id: The ID of the user to permanently delete
        cursor: Database cursor
    """
    # Delete related data first (maintain referential integrity)
    cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM user_tokens WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM user_preferences WHERE user_id = %s", (user_id,))
    
    # Finally delete the user
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    
    logger.info(f"Hard deleted user {user_id} and all associated data")


def delete_user_account(
    user_id: int,
    requesting_user_id: int,
    is_admin: bool = False,
    hard_delete: bool = False
) -> Dict[str, Any]:
    """
    Delete a user account from the system.
    
    Args:
        user_id: The ID of the user to delete
        requesting_user_id: The ID of the user requesting the deletion
        is_admin: Whether the requesting user is an admin
        hard_delete: Whether to permanently delete (True) or soft delete (False)
        
    Returns:
        Dict containing deletion status and details
        
    Raises:
        UserNotFoundError: If user is not found
        UnauthorizedDeletionError: If user is not authorized
        UserDeletionError: If deletion fails
    """
    try:
        # Verify authorization
        verify_deletion_authorization(user_id, requesting_user_id, is_admin)
        
        connection = get_database_connection()
        
        try:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Verify user exists
                user = verify_user_exists(user_id, cursor)
                
                # Perform deletion
                if hard_delete:
                    hard_delete_user(user_id, cursor)
                    deletion_type = "hard"
                else:
                    soft_delete_user(user_id, cursor)
                    deletion_type = "soft"
                
                connection.commit()
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "deletion_type": deletion_type,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "message": f"User account successfully deleted ({deletion_type} delete)"
                }
                
        except (UserNotFoundError, UnauthorizedDeletionError):
            connection.rollback()
            raise
        except Exception as e:
            connection.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise UserDeletionError(f"Failed to delete user account: {str(e)}")
        finally:
            connection.close()
            
    except (UserNotFoundError, UnauthorizedDeletionError, UserDeletionError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user deletion: {str(e)}")
        raise UserDeletionError(f"Unexpected error: {str(e)}")


def bulk_delete_inactive_users(
    days_inactive: int = 365,
    requesting_admin_id: int = None,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Bulk delete users who have been inactive for a specified period.
    
    Args:
        days_inactive: Number of days of inactivity before deletion
        requesting_admin_id: The ID of the admin requesting bulk deletion
        dry_run: If True, only return count without deleting
        
    Returns:
        Dict containing deletion results
        
    Raises:
        UserDeletionError: If bulk deletion fails
    """
    try:
        connection = get_database_connection()
        
        try:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Find inactive users
                cursor.execute(
                    """
                    SELECT id, email, username, last_login_at
                    FROM users
                    WHERE is_active = TRUE
                    AND last_login_at < NOW() - INTERVAL '%s days'
                    """,
                    (days_inactive,)
                )
                
                inactive_users = cursor.fetchall()
                user_count = len(inactive_users)
                
                if dry_run:
                    return {
                        "success": True,
                        "dry_run": True,
                        "users_to_delete": user_count,
                        "message": f"Found {user_count} users inactive for {days_inactive}+ days"
                    }
                
                # Perform soft deletion for all inactive users
                deleted_count = 0
                for user in inactive_users:
                    soft_delete_user(user['id'], cursor)
                    deleted_count += 1
                
                connection.commit()
                
                logger.info(f"Bulk deleted {deleted_count} inactive users by admin {requesting_admin_id}")
                
                return {
                    "success": True,
                    "dry_run": False,
                    "users_deleted": deleted_count,
                    "message": f"Successfully deleted {deleted_count} inactive users"
                }
                
        except Exception as e:
            connection.rollback()
            logger.error(f"Error during bulk deletion: {str(e)}")
            raise UserDeletionError(f"Bulk deletion failed: {str(e)}")
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"Unexpected error during bulk deletion: {str(e)}")
        raise UserDeletionError(f"Unexpected error: {str(e)}")
