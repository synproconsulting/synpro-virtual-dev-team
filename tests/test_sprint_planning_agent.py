"""Tests for sprint planning agent."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.auth.sprint_planning_agent import (
    ApprovalStatus,
    SprintPlan,
    SprintPlanningAgent,
    TaskEstimate,
)


@pytest.fixture
def mock_ai_client() -> MagicMock:
    """Create mock AI client."""
    return MagicMock()


@pytest.fixture
def agent(mock_ai_client: MagicMock) -> SprintPlanningAgent:
    """Create sprint planning agent instance."""
    return SprintPlanningAgent(mock_ai_client, approval_threshold=0.8)


@pytest.fixture
def sample_backlog() -> list[dict]:
    """Sample backlog items for testing."""
    return [
        {"id": "TASK-1", "title": "Feature A", "estimate": 8, "confidence": 0.9},
        {"id": "TASK-2", "title": "Feature B", "estimate": 5, "confidence": 0.85},
        {"id": "TASK-3", "title": "Feature C", "estimate": 3, "confidence": 0.95},
    ]


@pytest.mark.asyncio
async def test_generate_sprint_plan(agent: SprintPlanningAgent, sample_backlog: list) -> None:
    """Test sprint plan generation."""
    plan = await agent.generate_sprint_plan(
        sprint_id="SPRINT-1",
        backlog_items=sample_backlog,
        team_capacity=20,
    )
    
    assert plan.sprint_id == "SPRINT-1"
    assert plan.total_capacity == 20
    assert plan.status == ApprovalStatus.PENDING
    assert len(plan.tasks) > 0
    assert plan.total_estimated <= 20


@pytest.mark.asyncio
async def test_capacity_utilization(agent: SprintPlanningAgent, sample_backlog: list) -> None:
    """Test capacity utilization calculation."""
    plan = await agent.generate_sprint_plan(
        sprint_id="SPRINT-2",
        backlog_items=sample_backlog,
        team_capacity=20,
    )
    
    expected_utilization = (plan.total_estimated / plan.total_capacity) * 100
    assert plan.capacity_utilization == pytest.approx(expected_utilization)


@pytest.mark.asyncio
async def test_approve_plan(agent: SprintPlanningAgent, sample_backlog: list) -> None:
    """Test plan approval workflow."""
    plan = await agent.generate_sprint_plan(
        sprint_id="SPRINT-3",
        backlog_items=sample_backlog,
        team_capacity=20,
    )
    
    approved_plan = await agent.approve_plan(
        sprint_id="SPRINT-3",
        approver="pm@example.com",
        notes="Looks good!",
    )
    
    assert approved_plan.status == ApprovalStatus.APPROVED
    assert approved_plan.approver == "pm@example.com"
    assert approved_plan.approval_notes == "Looks good!"
    assert approved_plan.modified_at is not None


@pytest.mark.asyncio
async def test_reject_plan(agent: SprintPlanningAgent, sample_backlog: list) -> None:
    """Test plan rejection workflow."""
    plan = await agent.generate_sprint_plan(
        sprint_id="SPRINT-4",
        backlog_items=sample_backlog,
        team_capacity=20,
    )
    
    rejected_plan = await agent.reject_plan(
        sprint_id="SPRINT-4",
        approver="pm@example.com",
        reason="Needs more detail",
    )
    
    assert rejected_plan.status == ApprovalStatus.REJECTED
    assert rejected_plan.approver == "pm@example.com"
    assert rejected_plan.approval_notes == "Needs more detail"


@pytest.mark.asyncio
async def test_get_plan(agent: SprintPlanningAgent, sample_backlog: list) -> None:
    """Test retrieving plan by ID."""
    await agent.generate_sprint_plan(
        sprint_id="SPRINT-5",
        backlog_items=sample_backlog,
        team_capacity=20,
    )
    
    retrieved_plan = agent.get_plan("SPRINT-5")
    assert retrieved_plan is not None
    assert retrieved_plan.sprint_id == "SPRINT-5"
    
    missing_plan = agent.get_plan("NONEXISTENT")
    assert missing_plan is None


@pytest.mark.asyncio
async def test_task_selection_respects_capacity(agent: SprintPlanningAgent) -> None:
    """Test that task selection doesn't exceed capacity."""
    large_backlog = [
        {"id": f"TASK-{i}", "title": f"Task {i}", "estimate": 5, "confidence": 0.9}
        for i in range(20)
    ]
    
    plan = await agent.generate_sprint_plan(
        sprint_id="SPRINT-6",
        backlog_items=large_backlog,
        team_capacity=15,
    )
    
    assert plan.total_estimated <= plan.total_capacity


def test_task_estimate_creation() -> None:
    """Test TaskEstimate dataclass creation."""
    estimate = TaskEstimate(
        task_id="TASK-1",
        title="Test Task",
        story_points=5,
        confidence=0.9,
        reasoning="Simple task",
    )
    
    assert estimate.task_id == "TASK-1"
    assert estimate.story_points == 5
    assert estimate.dependencies == []
