"""
API endpoints for notification history.
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .service import NotificationService
from .views import NotificationHistoryView
from .models import NotificationType


class CreateNotificationRequest(BaseModel):
    """Request model for creating a notification."""
    user_id: str
    notification_type: str
    title: str
    message: str
    metadata: Optional[dict] = None


class MarkAsReadRequest(BaseModel):
    """Request model for marking notification as read."""
    user_id: str


def create_notification_routes(app: FastAPI) -> None:
    """
    Register notification API routes with FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    service = NotificationService()
    view = NotificationHistoryView(service)
    
    @app.post("/api/notifications")
    async def create_notification(request: CreateNotificationRequest) -> dict:
        """
        Create a new notification.
        
        Args:
            request: Notification creation request
            
        Returns:
            Created notification data
        """
        try:
            notification_type = NotificationType(request.notification_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification type")
        
        notification = service.create_notification(
            user_id=request.user_id,
            notification_type=notification_type,
            title=request.title,
            message=request.message,
            metadata=request.metadata,
        )
        
        return notification.to_dict()
    
    @app.get("/api/notifications/history/{user_id}")
    async def get_notification_history(
        user_id: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: Optional[str] = None,
        type: Optional[str] = None,
    ) -> dict:
        """
        Get notification history for a user.
        
        Args:
            user_id: User identifier
            page: Page number (default: 1)
            page_size: Items per page (default: 20, max: 100)
            status: Optional status filter
            type: Optional type filter
            
        Returns:
            Paginated notification history
        """
        return view.get_history_data(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status_filter=status,
            type_filter=type,
        )
    
    @app.get("/api/notifications/history/{user_id}/html")
    async def get_notification_history_html(
        user_id: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: Optional[str] = None,
        type: Optional[str] = None,
    ) -> dict:
        """
        Get notification history as HTML.
        
        Args:
            user_id: User identifier
            page: Page number
            page_size: Items per page
            status: Optional status filter
            type: Optional type filter
            
        Returns:
            HTML content for notification history
        """
        html = view.render_notification_list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status_filter=status,
            type_filter=type,
        )
        
        return {"html": html}
    
    @app.put("/api/notifications/{notification_id}/read")
    async def mark_notification_as_read(
        notification_id: str,
        request: MarkAsReadRequest,
    ) -> dict:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification identifier
            request: Request with user_id for authorization
            
        Returns:
            Updated notification data
        """
        notification = service.mark_as_read(notification_id, request.user_id)
        
        if not notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found or unauthorized"
            )
        
        return notification.to_dict()
    
    @app.put("/api/notifications/read-all/{user_id}")
    async def mark_all_notifications_as_read(user_id: str) -> dict:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Count of notifications marked as read
        """
        count = service.mark_all_as_read(user_id)
        return {"marked_as_read": count}
    
    @app.delete("/api/notifications/{notification_id}")
    async def delete_notification(
        notification_id: str,
        user_id: str = Query(...),
    ) -> dict:
        """
        Delete a notification.
        
        Args:
            notification_id: Notification identifier
            user_id: User identifier for authorization
            
        Returns:
            Success message
        """
        success = service.delete_notification(notification_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Notification not found or unauthorized"
            )
        
        return {"message": "Notification deleted successfully"}
    
    @app.get("/api/notifications/stats/{user_id}")
    async def get_notification_stats(user_id: str) -> dict:
        """
        Get notification statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Notification statistics
        """
        return service.get_notification_stats(user_id)
    
    @app.get("/api/notifications/filters")
    async def get_filter_options() -> dict:
        """
        Get available filter options.
        
        Returns:
            Available status and type filters
        """
        return view.get_filter_options()
