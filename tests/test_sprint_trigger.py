"""Tests for sprint trigger functionality."""

import pytest
from datetime import datetime, timedelta
from src.auth.sprint_trigger import SprintTrigger, SprintConfig


@pytest.fixture
def sprint_config():
    """Create a test sprint configuration."""
    return SprintConfig(
        sprint_duration_days=14,
        auto_start=True,
        notification_enabled=False,
        team_id="test-team-123"
    )


@pytest.fixture
def sprint_trigger(sprint_config):
    """Create a sprint trigger instance."""
    return SprintTrigger(sprint_config)


@pytest.mark.asyncio
async def test_trigger_sprint_success(sprint_trigger):
    """Test successful sprint triggering."""
    result = await sprint_trigger.trigger_sprint("Sprint 1")
    
    assert result["name"] == "Sprint 1"
    assert result["status"] == "active"
    assert result["team_id"] == "test-team-123"
    assert "start_date" in result
    assert "end_date" in result


@pytest.mark.asyncio
async def test_trigger_sprint_with_custom_date(sprint_trigger):
    """Test sprint triggering with custom start date."""
    custom_date = datetime(2024, 1, 1, 0, 0, 0)
    result = await sprint_trigger.trigger_sprint("Sprint 2", start_date=custom_date)
    
    assert result["name"] == "Sprint 2"
    assert custom_date.isoformat() in result["start_date"]


@pytest.mark.asyncio
async def test_trigger_sprint_prevents_duplicate(sprint_trigger):
    """Test that duplicate active sprints are prevented."""
    await sprint_trigger.trigger_sprint("Sprint 1")
    
    with pytest.raises(ValueError, match="Cannot start new sprint"):
        await sprint_trigger.trigger_sprint("Sprint 2")


@pytest.mark.asyncio
async def test_get_active_sprint(sprint_trigger):
    """Test retrieving active sprint information."""
    await sprint_trigger.trigger_sprint("Sprint 1")
    active = sprint_trigger.get_active_sprint()
    
    assert active is not None
    assert active["name"] == "Sprint 1"
    assert active["status"] == "active"


@pytest.mark.asyncio
async def test_complete_sprint(sprint_trigger):
    """Test completing an active sprint."""
    await sprint_trigger.trigger_sprint("Sprint 1")
    result = await sprint_trigger.complete_sprint()
    
    assert result["status"] == "completed"
    assert "completed_at" in result


@pytest.mark.asyncio
async def test_complete_sprint_without_active(sprint_trigger):
    """Test that completing without active sprint raises error."""
    with pytest.raises(ValueError, match="No active sprint"):
        await sprint_trigger.complete_sprint()


def test_sprint_config_defaults():
    """Test default sprint configuration values."""
    config = SprintConfig(team_id="team-1")
    
    assert config.sprint_duration_days == 14
    assert config.auto_start is True
    assert config.notification_enabled is True
    assert config.team_id == "team-1"
