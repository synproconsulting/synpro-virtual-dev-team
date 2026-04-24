"""Product Manager chat interface for sprint planning agent."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from src.auth.sprint_planning_agent import ApprovalStatus, SprintPlan, SprintPlanningAgent


class ChatCommand(Enum):
    """Available chat commands for PM interaction."""
    PLAN_SPRINT = "plan_sprint"
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    VIEW_PLAN = "view_plan"
    HELP = "help"


@dataclass
class ChatMessage:
    """Chat message structure."""
    user_id: str
    content: str
    timestamp: datetime
    command: Optional[ChatCommand] = None
    metadata: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChatResponse:
    """Response from chat interface."""
    content: str
    sprint_plan: Optional[SprintPlan] = None
    requires_approval: bool = False
    timestamp: datetime = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class PMChatInterface:
    """Interactive chat interface for PM to manage sprint planning."""

    def __init__(self, agent: SprintPlanningAgent, user_id: str) -> None:
        """
        Initialize PM chat interface.

        Args:
            agent: Sprint planning agent instance
            user_id: Authenticated PM user identifier
        """
        self._agent = agent
        self._user_id = user_id
        self._conversation_history: list[ChatMessage] = []
        self._command_handlers: dict[ChatCommand, Callable] = {
            ChatCommand.PLAN_SPRINT: self._handle_plan_sprint,
            ChatCommand.APPROVE: self._handle_approve,
            ChatCommand.REJECT: self._handle_reject,
            ChatCommand.VIEW_PLAN: self._handle_view_plan,
            ChatCommand.HELP: self._handle_help,
        }

    async def process_message(self, message_content: str) -> ChatResponse:
        """
        Process incoming chat message and execute command.

        Args:
            message_content: Raw message text from PM

        Returns:
            Chat response with action results
        """
        message = ChatMessage(
            user_id=self._user_id,
            content=message_content,
            timestamp=datetime.utcnow(),
        )
        
        # Parse command from message
        command, params = self._parse_command(message_content)
        message.command = command
        message.metadata = params
        
        self._conversation_history.append(message)
        
        # Execute command handler
        handler = self._command_handlers.get(command, self._handle_unknown)
        response = await handler(params)
        
        return response

    def _parse_command(self, content: str) -> tuple[Optional[ChatCommand], dict[str, Any]]:
        """Parse command and parameters from message content."""
        content_lower = content.lower().strip()
        params = {}
        
        if "plan sprint" in content_lower or "create sprint" in content_lower:
            return ChatCommand.PLAN_SPRINT, self._extract_sprint_params(content)
        elif "approve" in content_lower:
            return ChatCommand.APPROVE, self._extract_approval_params(content)
        elif "reject" in content_lower:
            return ChatCommand.REJECT, self._extract_rejection_params(content)
        elif "view plan" in content_lower or "show plan" in content_lower:
            return ChatCommand.VIEW_PLAN, self._extract_view_params(content)
        elif "help" in content_lower:
            return ChatCommand.HELP, {}
        
        return None, {}

    def _extract_sprint_params(self, content: str) -> dict[str, Any]:
        """Extract sprint planning parameters from message."""
        # Simple extraction - in production, use NLP
        return {
            "sprint_id": f"sprint_{datetime.utcnow().timestamp()}",
            "capacity": 40,  # Default capacity
        }

    def _extract_approval_params(self, content: str) -> dict[str, Any]:
        """Extract approval parameters from message."""
        return {"notes": content}

    def _extract_rejection_params(self, content: str) -> dict[str, Any]:
        """Extract rejection parameters from message."""
        return {"reason": content}

    def _extract_view_params(self, content: str) -> dict[str, Any]:
        """Extract view parameters from message."""
        return {}

    async def _handle_plan_sprint(self, params: dict[str, Any]) -> ChatResponse:
        """Handle sprint planning command."""
        sprint_id = params.get("sprint_id", "default_sprint")
        capacity = params.get("capacity", 40)
        
        # Mock backlog items
        backlog = [
            {"id": "task1", "title": "Implement authentication", "estimate": 8},
            {"id": "task2", "title": "Add API endpoints", "estimate": 5},
        ]
        
        plan = await self._agent.generate_sprint_plan(sprint_id, backlog, capacity)
        
        return ChatResponse(
            content=f"Created sprint plan '{sprint_id}' with {len(plan.tasks)} tasks. "
                   f"Capacity utilization: {plan.capacity_utilization:.1f}%",
            sprint_plan=plan,
            requires_approval=True,
        )

    async def _handle_approve(self, params: dict[str, Any]) -> ChatResponse:
        """Handle approval command."""
        # Get most recent plan from conversation
        sprint_id = params.get("sprint_id")
        if not sprint_id:
            return ChatResponse(content="Please specify sprint ID to approve.")
        
        plan = await self._agent.approve_plan(
            sprint_id, self._user_id, params.get("notes")
        )
        
        return ChatResponse(
            content=f"Sprint plan '{sprint_id}' approved successfully!",
            sprint_plan=plan,
        )

    async def _handle_reject(self, params: dict[str, Any]) -> ChatResponse:
        """Handle rejection command."""
        sprint_id = params.get("sprint_id")
        reason = params.get("reason", "No reason provided")
        
        if not sprint_id:
            return ChatResponse(content="Please specify sprint ID to reject.")
        
        plan = await self._agent.reject_plan(sprint_id, self._user_id, reason)
        
        return ChatResponse(
            content=f"Sprint plan '{sprint_id}' rejected.",
            sprint_plan=plan,
        )

    async def _handle_view_plan(self, params: dict[str, Any]) -> ChatResponse:
        """Handle view plan command."""
        return ChatResponse(content="View plan functionality coming soon.")

    async def _handle_help(self, params: dict[str, Any]) -> ChatResponse:
        """Handle help command."""
        help_text = (
            "Available commands:\n"
            "- 'plan sprint' - Generate AI sprint plan\n"
            "- 'approve' - Approve pending plan\n"
            "- 'reject' - Reject pending plan\n"
            "- 'view plan' - View sprint details"
        )
        return ChatResponse(content=help_text)

    async def _handle_unknown(self, params: dict[str, Any]) -> ChatResponse:
        """Handle unknown command."""
        return ChatResponse(
            content="I didn't understand that. Type 'help' for available commands."
        )
