"""Tests for PM chat interface."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.auth.pm_chat_interface import (
    ChatCommand,
    ChatMessage,
    ChatResponse,
    PMChatInterface,
)
from src.auth.sprint_planning_agent import SprintPlanningAgent, ApprovalStatus


@pytest.fixture
def mock_agent() -> MagicMock:
    """Create mock sprint planning agent."""
    agent = MagicMock(spec=SprintPlanningAgent)
    agent.generate_sprint_plan = AsyncMock()
    agent.approve_plan = AsyncMock()
    agent.reject_plan = AsyncMock()
    return agent


@pytest.fixture
def chat_interface(mock_agent: MagicMock) -> PMChatInterface:
    """Create PM chat interface instance."""
    return PMChatInterface(mock_agent, user_id="pm@example.com")


@pytest.mark.asyncio
async def test_process_help_command(chat_interface: PMChatInterface) -> None:
    """Test help command processing."""
    response = await chat_interface.process_message("help")
    
    assert "Available commands" in response.content
    assert response.requires_approval is False
    assert response.sprint_plan is None


@pytest.mark.asyncio
async def test_process_plan_sprint_command(
    chat_interface: PMChatInterface, mock_agent: MagicMock
) -> None:
    """Test sprint planning command."""
    from src.auth.sprint_planning_agent import SprintPlan
    
    mock_plan = SprintPlan(
        sprint_id="test_sprint",
        tasks=[],
        total_capacity=40,
        total_estimated=35,
        created_at=datetime.utcnow(),
    )
    mock_agent.generate_sprint_plan.return_value = mock_plan
    
    response = await chat_interface.process_message("plan sprint with capacity 40")
    
    assert response.requires_approval is True
    assert response.sprint_plan is not None
    assert "Created sprint plan" in response.content
    mock_agent.generate_sprint_plan.assert_called_once()


@pytest.mark.asyncio
async def test_process_approve_command(
    chat_interface: PMChatInterface, mock_agent: MagicMock
) -> None:
    """Test approval command processing."""
    from src.auth.sprint_planning_agent import SprintPlan
    
    mock_plan = SprintPlan(
        sprint_id="test_sprint",
        tasks=[],
        total_capacity=40,
        total_estimated=35,
        created_at=datetime.utcnow(),
        status=ApprovalStatus.APPROVED,
    )
    mock_agent.approve_plan.return_value = mock_plan
    
    # Need to specify sprint_id in message - simplified for test
    with patch.object(chat_interface, "_extract_approval_params") as mock_extract:
        mock_extract.return_value = {"sprint_id": "test_sprint", "notes": "Approved"}
        response = await chat_interface.process_message("approve test_sprint")
    
    assert "approved successfully" in response.content


@pytest.mark.asyncio
async def test_process_reject_command(
    chat_interface: PMChatInterface, mock_agent: MagicMock
) -> None:
    """Test rejection command processing."""
    from src.auth.sprint_planning_agent import SprintPlan
    
    mock_plan = SprintPlan(
        sprint_id="test_sprint",
        tasks=[],
        total_capacity=40,
        total_estimated=35,
        created_at=datetime.utcnow(),
        status=ApprovalStatus.REJECTED,
    )
    mock_agent.reject_plan.return_value = mock_plan
    
    with patch.object(chat_interface, "_extract_rejection_params") as mock_extract:
        mock_extract.return_value = {"sprint_id": "test_sprint", "reason": "Too ambitious"}
        response = await chat_interface.process_message("reject test_sprint")
    
    assert "rejected" in response.content


@pytest.mark.asyncio
async def test_process_unknown_command(chat_interface: PMChatInterface) -> None:
    """Test handling of unknown commands."""
    response = await chat_interface.process_message("do something random")
    
    assert "didn't understand" in response.content or "help" in response.content


def test_parse_command_help(chat_interface: PMChatInterface) -> None:
    """Test command parsing for help."""
    command, params = chat_interface._parse_command("help")
    assert command == ChatCommand.HELP


def test_parse_command_plan_sprint(chat_interface: PMChatInterface) -> None:
    """Test command parsing for sprint planning."""
    command, params = chat_interface._parse_command("plan sprint for next week")
    assert command == ChatCommand.PLAN_SPRINT
    assert "sprint_id" in params


def test_chat_message_creation() -> None:
    """Test ChatMessage dataclass creation."""
    message = ChatMessage(
        user_id="pm@example.com",
        content="test message",
        timestamp=datetime.utcnow(),
    )
    
    assert message.user_id == "pm@example.com"
    assert message.content == "test message"
    assert message.metadata == {}


def test_chat_response_creation() -> None:
    """Test ChatResponse dataclass creation."""
    response = ChatResponse(
        content="test response",
        requires_approval=True,
    )
    
    assert response.content == "test response"
    assert response.requires_approval is True
    assert response.timestamp is not None
