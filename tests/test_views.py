"""
Unit tests for notification views.
"""

import pytest
from src.notifications.views import NotificationHistoryView
from src.notifications.service import NotificationService
from src.notifications.repository import NotificationRepository
from src.notifications.models import NotificationType


@pytest.fixture
def view():
    """Create a fresh view with service for each test."""
    repository = NotificationRepository()
    service = NotificationService(repository)
    return NotificationHistoryView(service)


@pytest.fixture
def view_with_data(view):
    """Create view with some test data."""
    # Create test notifications
    for i in range(3):
        view.service.create_notification(
            user_id="user-123",
            notification_type=NotificationType.EMAIL,
            title=f"Test Notification {i}",
            message=f"Test message {i}",
        )
    return view


def test_get_history_data(view_with_data):
    """Test getting history data."""
    data = view_with_data.get_history_data("user-123")
    
    assert "notifications" in data
    assert "pagination" in data
    assert "metadata" in data
    assert len(data["notifications"]) == 3


def test_get_history_data_with_filters(view):
    """Test getting history with filters."""
    # Create notifications of different types
    view.service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Email",
        message="Email message",
    )
    view.service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="SMS",
        message="SMS message",
    )
    
    # Filter by email type
    data = view.get_history_data("user-123", type_filter="email")
    
    assert len(data["notifications"]) == 1
    assert data["notifications"][0]["type"] == "email"


def test_get_history_data_invalid_filter(view_with_data):
    """Test getting history with invalid filter."""
    # Invalid filter should be ignored
    data = view_with_data.get_history_data(
        "user-123",
        status_filter="invalid_status"
    )
    
    assert len(data["notifications"]) == 3


def test_render_notification_card(view_with_data):
    """Test rendering single notification card."""
    data = view_with_data.get_history_data("user-123")
    notification = data["notifications"][0]
    
    html = view_with_data.render_notification_card(notification)
    
    assert isinstance(html, str)
    assert "notification-card" in html
    assert notification["title"] in html
    assert notification["message"] in html
    assert notification["id"] in html


def test_render_notification_card_unread(view):
    """Test rendering unread notification card."""
    notif = view.service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Unread",
        message="Unread message",
    )
    
    html = view.render_notification_card(notif.to_dict())
    
    assert "unread" in html


def test_render_notification_card_read(view):
    """Test rendering read notification card."""
    notif = view.service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Read",
        message="Read message",
    )
    view.service.mark_as_read(notif.id, "user-123")
    
    data = view.get_history_data("user-123")
    html = view.render_notification_card(data["notifications"][0])
    
    assert "badge-read" in html


def test_render_notification_list(view_with_data):
    """Test rendering complete notification list."""
    html = view_with_data.render_notification_list("user-123")
    
    assert isinstance(html, str)
    assert "notification-history-view" in html
    assert "notification-list" in html
    assert "pagination" in html
    assert "notification-stats" in html


def test_render_notification_list_empty(view):
    """Test rendering empty notification list."""
    html = view.render_notification_list("user-123")
    
    assert "No notifications found" in html


def test_render_notification_list_with_filters(view):
    """Test rendering list with filters."""
    view.service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Email",
        message="Email message",
    )
    
    html = view.render_notification_list(
        "user-123",
        type_filter="email"
    )
    
    assert "notification-history-view" in html
    assert "Email" in html


def test_get_filter_options(view):
    """Test getting filter options."""
    options = view.get_filter_options()
    
    assert "statuses" in options
    assert "types" in options
    
    # Check that all statuses are present
    status_values = [s["value"] for s in options["statuses"]]
    assert "pending" in status_values
    assert "sent" in status_values
    assert "delivered" in status_values
    assert "failed" in status_values
    assert "read" in status_values
    
    # Check that all types are present
    type_values = [t["value"] for t in options["types"]]
    assert "email" in type_values
    assert "sms" in type_values
    assert "push" in type_values
    assert "in_app" in type_values
    assert "webhook" in type_values


def test_get_status_class(view):
    """Test getting CSS class for status."""
    assert view._get_status_class("pending") == "status-pending"
    assert view._get_status_class("sent") == "status-sent"
    assert view._get_status_class("delivered") == "status-delivered"
    assert view._get_status_class("failed") == "status-failed"
    assert view._get_status_class("read") == "status-read"
    assert view._get_status_class("unknown") == "status-default"


def test_get_type_icon(view):
    """Test getting icon for notification type."""
    assert view._get_type_icon("email") == "📧"
    assert view._get_type_icon("sms") == "📱"
    assert view._get_type_icon("push") == "🔔"
    assert view._get_type_icon("in_app") == "💬"
    assert view._get_type_icon("webhook") == "🔗"
    assert view._get_type_icon("unknown") == "📬"


def test_format_timestamp(view):
    """Test formatting timestamps."""
    from datetime import datetime, timedelta
    
    # Test recent timestamp
    now = datetime.utcnow()
    recent = now - timedelta(minutes=5)
    formatted = view._format_timestamp(recent.isoformat())
    assert "minute" in formatted or "Just now" in formatted
    
    # Test None
    assert view._format_timestamp(None) == "N/A"
    
    # Test invalid
    assert view._format_timestamp("invalid") == "invalid"


def test_render_pagination(view_with_data):
    """Test rendering pagination controls."""
    data = view_with_data.get_history_data("user-123", page=1, page_size=2)
    html = view_with_data._render_pagination(data["pagination"])
    
    assert "pagination" in html
    assert "Previous" in html
    assert "Next" in html
    assert "Page" in html


def test_render_stats(view_with_data):
    """Test rendering statistics."""
    data = view_with_data.get_history_data("user-123")
    html = view_with_data._render_stats(data["metadata"])
    
    assert "notification-stats" in html
    assert "Unread" in html
    assert "Mark All as Read" in html


def test_render_filters(view):
    """Test rendering filter controls."""
    html = view._render_filters(None, None)
    
    assert "filters" in html
    assert "filter-status" in html
    assert "filter-type" in html
    assert "All Statuses" in html
    assert "All Types" in html


def test_render_filters_with_selection(view):
    """Test rendering filters with selected values."""
    html = view._render_filters("pending", "email")
    
    assert 'value="pending" selected' in html
    assert 'value="email" selected' in html


def test_get_json_data(view_with_data):
    """Test getting JSON data."""
    import json
    
    json_str = view_with_data.get_json_data("user-123")
    
    # Verify it's valid JSON
    data = json.loads(json_str)
    
    assert "notifications" in data
    assert "pagination" in data
    assert "metadata" in data


def test_render_notification_list_pagination(view):
    """Test list rendering with pagination."""
    # Create many notifications
    for i in range(10):
        view.service.create_notification(
            user_id="user-123",
            notification_type=NotificationType.EMAIL,
            title=f"Notification {i}",
            message=f"Message {i}",
        )
    
    # Render first page
    html = view.render_notification_list("user-123", page=1, page_size=5)
    
    assert "notification-history-view" in html
    assert "Page 1 of 2" in html


def test_notification_card_has_actions(view_with_data):
    """Test that notification card includes action buttons."""
    data = view_with_data.get_history_data("user-123")
    notification = data["notifications"][0]
    
    html = view_with_data.render_notification_card(notification)
    
    assert "btn-mark-read" in html
    assert "btn-delete" in html
    assert "Mark as Read" in html
    assert "Delete" in html
