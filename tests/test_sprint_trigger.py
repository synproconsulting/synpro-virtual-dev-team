"""Tests for sprint trigger functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from src.auth.sprint_trigger import SprintTrigger
import httpx


@pytest.fixture
def sprint_trigger():
    """Create SprintTrigger instance for testing."""
    return SprintTrigger(
        api_base_url="https://api.example.com",
        api_token="test-token-123",
    )


@pytest.mark.asyncio
async def test_trigger_sprint_success(sprint_trigger):
    """Test successful sprint triggering."""
    mock_response = {
        "id": "sprint-123",
        "name": "Test Sprint",
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        result = await sprint_trigger.trigger_sprint(
            sprint_name="Test Sprint",
            duration_days=14,
            board_id="board-456",
        )

        assert result["id"] == "sprint-123"
        assert result["name"] == "Test Sprint"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_sprint_missing_credentials():
    """Test sprint trigger with missing credentials."""
    trigger = SprintTrigger(api_base_url="", api_token="")

    with pytest.raises(ValueError, match="Sprint API credentials not configured"):
        await trigger.trigger_sprint("Test Sprint")


@pytest.mark.asyncio
async def test_get_sprint_status(sprint_trigger):
    """Test getting sprint status."""
    mock_response = {"id": "sprint-123", "status": "active", "progress": 45}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = lambda: None

        result = await sprint_trigger.get_sprint_status("sprint-123")

        assert result["status"] == "active"
        assert result["progress"] == 45


@pytest.mark.asyncio
async def test_complete_sprint(sprint_trigger):
    """Test completing a sprint."""
    mock_response = {"id": "sprint-123", "status": "completed"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        result = await sprint_trigger.complete_sprint("sprint-123")

        assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_trigger_sprint_api_error(sprint_trigger):
    """Test sprint trigger with API error."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "API Error", request=None, response=None
        )

        with pytest.raises(httpx.HTTPStatusError):
            await sprint_trigger.trigger_sprint("Test Sprint")
