"""Tests for sprint trigger functionality."""

import pytest
from datetime import datetime, timedelta
from src.auth.sprint_trigger import SprintTrigger, SprintConfig


@pytest.fixture
def sprint_config():
    """Fixture for sprint configuration."""
    return SprintConfig(
        sprint_name="Sprint 1",
        start_date=datetime.utcnow(),
        duration_days=14,
        team_id="team-alpha",
        auto_review_enabled=True
    )


@pytest.fixture
def sprint_trigger(sprint_config):
    """Fixture for sprint trigger."""
    return SprintTrigger(sprint_config)


def test_sprint_trigger_initialization(sprint_trigger, sprint_config):
    """Test sprint trigger initialization."""
    assert sprint_trigger.config == sprint_config
    assert sprint_trigger._status == "idle"
    assert sprint_trigger._sprint_id is None


def test_trigger_sprint_success(sprint_trigger):
    """Test successful sprint triggering."""
    result = sprint_trigger.trigger_sprint()
    
    assert "sprint_id" in result
    assert result["name"] == "Sprint 1"
    assert result["status"] == "running"
    assert result["team_id"] == "team-alpha"
    assert result["auto_review_enabled"] is True
    assert "triggered_at" in result


def test_trigger_sprint_already_running(sprint_trigger):
    """Test error when triggering already running sprint."""
    sprint_trigger.trigger_sprint()
    
    with pytest.raises(ValueError, match="Sprint is already running"):
        sprint_trigger.trigger_sprint()


def test_stop_sprint(sprint_trigger):
    """Test stopping a sprint."""
    sprint_trigger.trigger_sprint()
    result = sprint_trigger.stop_sprint()
    
    assert result["status"] == "stopped"
    assert "stopped_at" in result
    assert "sprint_id" in result


def test_get_status(sprint_trigger):
    """Test getting sprint status."""
    sprint_trigger.trigger_sprint()
    status = sprint_trigger.get_status()
    
    assert status["status"] == "running"
    assert status["config"]["name"] == "Sprint 1"
    assert status["config"]["team_id"] == "team-alpha"
    assert status["config"]["auto_review_enabled"] is True


def test_sprint_id_generation(sprint_trigger):
    """Test sprint ID generation is unique."""
    result1 = sprint_trigger.trigger_sprint()
    sprint_trigger.stop_sprint()
    
    sprint_trigger._status = "idle"
    result2 = sprint_trigger.trigger_sprint()
    
    assert result1["sprint_id"] != result2["sprint_id"]
    assert "sprint-team-alpha-" in result1["sprint_id"]
