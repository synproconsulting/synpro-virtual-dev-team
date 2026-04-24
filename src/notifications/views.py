"""
View layer for notification history with UI rendering capabilities.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from .models import NotificationStatus, NotificationType
from .service import NotificationService


class NotificationHistoryView:
    """
    View controller for notification history display and interaction.
    
    Provides methods to generate UI-ready data structures and
    HTML components for notification history display.
    """
    
    def __init__(self, service: Optional[NotificationService] = None) -> None:
        """
        Initialize the notification history view.
        
        Args:
            service: Optional notification service instance
        """
        self.service = service or NotificationService()
    
    def get_history_data(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get notification history data for display.
        
        Args:
            user_id: User identifier
            page: Page number (1-indexed)
            page_size: Number of items per page
            status_filter: Optional status filter string
            type_filter: Optional type filter string
            
        Returns:
            Dictionary with formatted data ready for UI rendering
        """
        status = None
        if status_filter:
            try:
                status = NotificationStatus(status_filter)
            except ValueError:
                pass
        
        notification_type = None
        if type_filter:
            try:
                notification_type = NotificationType(type_filter)
            except ValueError:
                pass
        
        return self.service.get_notification_history(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status,
            notification_type=notification_type,
        )
    
    def render_notification_card(self, notification_data: Dict[str, Any]) -> str:
        """
        Render a single notification as an HTML card.
        
        Args:
            notification_data: Notification dictionary
            
        Returns:
            HTML string for notification card
        """
        status_class = self._get_status_class(notification_data["status"])
        type_icon = self._get_type_icon(notification_data["type"])
        
        read_indicator = "" if notification_data["status"] == "read" else "unread"
        
        created_at = self._format_timestamp(notification_data["created_at"])
        
        html = f"""
        <div class="notification-card {status_class} {read_indicator}" data-id="{notification_data['id']}">
            <div class="notification-header">
                <span class="notification-icon">{type_icon}</span>
                <span class="notification-type">{notification_data['type']}</span>
                <span class="notification-time">{created_at}</span>
            </div>
            <div class="notification-body">
                <h4 class="notification-title">{notification_data['title']}</h4>
                <p class="notification-message">{notification_data['message']}</p>
            </div>
            <div class="notification-footer">
                <span class="notification-status badge-{notification_data['status']}">{notification_data['status']}</span>
                <div class="notification-actions">
                    <button class="btn-mark-read" data-id="{notification_data['id']}">Mark as Read</button>
                    <button class="btn-delete" data-id="{notification_data['id']}">Delete</button>
                </div>
            </div>
        </div>
        """
        return html
    
    def render_notification_list(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> str:
        """
        Render complete notification list with pagination.
        
        Args:
            user_id: User identifier
            page: Page number
            page_size: Items per page
            status_filter: Optional status filter
            type_filter: Optional type filter
            
        Returns:
            HTML string for complete notification list
        """
        data = self.get_history_data(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            type_filter=type_filter,
        )
        
        cards_html = "\n".join([
            self.render_notification_card(notif)
            for notif in data["notifications"]
        ])
        
        pagination_html = self._render_pagination(data["pagination"])
        
        stats_html = self._render_stats(data["metadata"])
        
        html = f"""
        <div class="notification-history-view">
            {stats_html}
            <div class="notification-filters">
                {self._render_filters(status_filter, type_filter)}
            </div>
            <div class="notification-list">
                {cards_html if cards_html else '<p class="no-notifications">No notifications found.</p>'}
            </div>
            {pagination_html}
        </div>
        """
        return html
    
    def get_filter_options(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get available filter options for the UI.
        
        Returns:
            Dictionary with status and type filter options
        """
        return {
            "statuses": [
                {"value": status.value, "label": status.value.replace("_", " ").title()}
                for status in NotificationStatus
            ],
            "types": [
                {"value": ntype.value, "label": ntype.value.replace("_", " ").title()}
                for ntype in NotificationType
            ],
        }
    
    def _get_status_class(self, status: str) -> str:
        """Get CSS class for notification status."""
        status_classes = {
            "pending": "status-pending",
            "sent": "status-sent",
            "delivered": "status-delivered",
            "failed": "status-failed",
            "read": "status-read",
        }
        return status_classes.get(status, "status-default")
    
    def _get_type_icon(self, notification_type: str) -> str:
        """Get icon/emoji for notification type."""
        type_icons = {
            "email": "📧",
            "sms": "📱",
            "push": "🔔",
            "in_app": "💬",
            "webhook": "🔗",
        }
        return type_icons.get(notification_type, "📬")
    
    def _format_timestamp(self, timestamp_str: Optional[str]) -> str:
        """Format timestamp for display."""
        if not timestamp_str:
            return "N/A"
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.utcnow()
            diff = now - timestamp
            
            if diff.days == 0:
                if diff.seconds < 60:
                    return "Just now"
                elif diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                else:
                    hours = diff.seconds // 3600
                    return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return timestamp.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return timestamp_str
    
    def _render_pagination(self, pagination: Dict[str, Any]) -> str:
        """Render pagination controls."""
        current = pagination["page"]
        total = pagination["total_pages"]
        
        prev_disabled = "disabled" if not pagination["has_previous"] else ""
        next_disabled = "disabled" if not pagination["has_next"] else ""
        
        html = f"""
        <div class="pagination">
            <button class="btn-page-prev" {prev_disabled} data-page="{current - 1}">Previous</button>
            <span class="page-info">Page {current} of {total}</span>
            <button class="btn-page-next" {next_disabled} data-page="{current + 1}">Next</button>
        </div>
        """
        return html
    
    def _render_stats(self, metadata: Dict[str, Any]) -> str:
        """Render notification statistics."""
        unread = metadata.get("unread_count", 0)
        
        html = f"""
        <div class="notification-stats">
            <div class="stat-item">
                <span class="stat-label">Unread:</span>
                <span class="stat-value unread-count">{unread}</span>
            </div>
            <button class="btn-mark-all-read">Mark All as Read</button>
        </div>
        """
        return html
    
    def _render_filters(
        self,
        status_filter: Optional[str],
        type_filter: Optional[str],
    ) -> str:
        """Render filter controls."""
        filter_options = self.get_filter_options()
        
        status_options_html = '<option value="">All Statuses</option>'
        for option in filter_options["statuses"]:
            selected = 'selected' if option["value"] == status_filter else ''
            status_options_html += f'<option value="{option["value"]}" {selected}>{option["label"]}</option>'
        
        type_options_html = '<option value="">All Types</option>'
        for option in filter_options["types"]:
            selected = 'selected' if option["value"] == type_filter else ''
            type_options_html += f'<option value="{option["value"]}" {selected}>{option["label"]}</option>'
        
        html = f"""
        <div class="filters">
            <label>
                Status:
                <select class="filter-status" name="status">
                    {status_options_html}
                </select>
            </label>
            <label>
                Type:
                <select class="filter-type" name="type">
                    {type_options_html}
                </select>
            </label>
            <button class="btn-apply-filters">Apply Filters</button>
        </div>
        """
        return html
    
    def get_json_data(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> str:
        """
        Get notification history as JSON string for API responses.
        
        Args:
            user_id: User identifier
            page: Page number
            page_size: Items per page
            status_filter: Optional status filter
            type_filter: Optional type filter
            
        Returns:
            JSON string with notification data
        """
        data = self.get_history_data(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            type_filter=type_filter,
        )
        return json.dumps(data, indent=2)
