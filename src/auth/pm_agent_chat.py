"""PM Agent chat interface for AI sprint planning."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol
import uuid

from src.auth.sprint_planner import (
    SprintPlan,
    SprintTask,
    SprintPlanApprovalWorkflow,
    ApprovalStatus
)


class AIProvider(Protocol):
    """Protocol for AI provider integration."""
    
    def generate_sprint_plan(self, context: str, requirements: List[str]) -> List[SprintTask]:
        """Generate sprint tasks from requirements."""
        ...


@dataclass
class ChatMessage:
    """Represents a chat message in the PM agent interface."""
    message_id: str
    user_id: str
    content: str
    timestamp: datetime
    message_type: str = "user"  # user, agent, system


class PMAgentChat:
    """PM Agent chat interface for AI-assisted sprint planning."""

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        """Initialize PM agent chat interface."""
        self._ai_provider = ai_provider
        self._workflow = SprintPlanApprovalWorkflow()
        self._chat_history: List[ChatMessage] = []

    def send_message(self, user_id: str, content: str) -> ChatMessage:
        """Send a message to the PM agent."""
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            user_id=user_id,
            content=content,
            timestamp=datetime.utcnow(),
            message_type="user"
        )
        self._chat_history.append(message)
        return message

    def generate_plan_from_chat(
        self,
        user_id: str,
        sprint_name: str,
        requirements: List[str]
    ) -> SprintPlan:
        """Generate a sprint plan from chat requirements."""
        tasks = []
        
        if self._ai_provider:
            context = "\n".join([msg.content for msg in self._chat_history[-10:]])
            tasks = self._ai_provider.generate_sprint_plan(context, requirements)
        else:
            # Fallback: create basic tasks from requirements
            for idx, req in enumerate(requirements, 1):
                task = SprintTask(
                    task_id=f"TASK-{idx}",
                    title=req[:50],
                    description=req,
                    story_points=3,
                    priority=idx
                )
                tasks.append(task)
        
        plan = SprintPlan(
            plan_id=str(uuid.uuid4()),
            sprint_name=sprint_name,
            tasks=tasks,
            created_at=datetime.utcnow(),
            created_by=user_id
        )
        
        self._workflow.submit_plan(plan)
        
        # Add system message
        self._add_system_message(
            f"Sprint plan '{sprint_name}' created with {len(tasks)} tasks "
            f"({plan.total_story_points} story points). Status: {plan.status.value}"
        )
        
        return plan

    def approve_plan(self, plan_id: str, approver_id: str, notes: Optional[str] = None) -> bool:
        """Approve a sprint plan through the chat interface."""
        success = self._workflow.approve_plan(plan_id, approver_id, notes)
        
        if success:
            self._add_system_message(
                f"Sprint plan {plan_id} approved by {approver_id}"
            )
        
        return success

    def reject_plan(self, plan_id: str, approver_id: str, notes: str) -> bool:
        """Reject a sprint plan through the chat interface."""
        success = self._workflow.reject_plan(plan_id, approver_id, notes)
        
        if success:
            self._add_system_message(
                f"Sprint plan {plan_id} rejected by {approver_id}. Reason: {notes}"
            )
        
        return success

    def get_plan_status(self, plan_id: str) -> Optional[dict]:
        """Get the status of a sprint plan."""
        plan = self._workflow.get_plan(plan_id)
        return plan.to_dict() if plan else None

    def get_chat_history(self) -> List[ChatMessage]:
        """Retrieve chat history."""
        return self._chat_history.copy()

    def _add_system_message(self, content: str) -> None:
        """Add a system message to chat history."""
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            user_id="system",
            content=content,
            timestamp=datetime.utcnow(),
            message_type="system"
        )
        self._chat_history.append(message)
