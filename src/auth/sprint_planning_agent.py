"""Sprint planning agent with AI-powered task estimation and approval workflow."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ApprovalStatus(Enum):
    """Status of sprint planning approval."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


@dataclass
class TaskEstimate:
    """AI-generated task estimate."""
    task_id: str
    title: str
    story_points: int
    confidence: float
    reasoning: str
    dependencies: list[str] = field(default_factory=list)
    suggested_assignee: Optional[str] = None


@dataclass
class SprintPlan:
    """Complete sprint plan with tasks and metadata."""
    sprint_id: str
    tasks: list[TaskEstimate]
    total_capacity: int
    total_estimated: int
    created_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: Optional[str] = None
    approval_notes: Optional[str] = None
    modified_at: Optional[datetime] = None

    @property
    def capacity_utilization(self) -> float:
        """Calculate capacity utilization percentage."""
        if self.total_capacity == 0:
            return 0.0
        return (self.total_estimated / self.total_capacity) * 100


class SprintPlanningAgent:
    """AI agent for automated sprint planning with approval workflow."""

    def __init__(self, ai_client: Any, approval_threshold: float = 0.8) -> None:
        """
        Initialize sprint planning agent.

        Args:
            ai_client: Client for AI inference (e.g., OpenAI, Anthropic)
            approval_threshold: Confidence threshold for auto-approval
        """
        self._ai_client = ai_client
        self._approval_threshold = approval_threshold
        self._pending_plans: dict[str, SprintPlan] = {}

    async def generate_sprint_plan(
        self,
        sprint_id: str,
        backlog_items: list[dict[str, Any]],
        team_capacity: int,
        team_velocity: Optional[int] = None,
    ) -> SprintPlan:
        """Generate AI-powered sprint plan from backlog.

        Args:
            sprint_id: Unique identifier for sprint
            backlog_items: List of backlog tasks with descriptions
            team_capacity: Available story points for sprint
            team_velocity: Historical team velocity for calibration

        Returns:
            Generated sprint plan with task estimates
        """
        estimates = await self._estimate_tasks(backlog_items, team_velocity)
        
        # Select tasks that fit capacity
        selected_tasks = self._select_tasks_for_capacity(estimates, team_capacity)
        
        total_estimated = sum(task.story_points for task in selected_tasks)
        
        plan = SprintPlan(
            sprint_id=sprint_id,
            tasks=selected_tasks,
            total_capacity=team_capacity,
            total_estimated=total_estimated,
            created_at=datetime.utcnow(),
        )
        
        self._pending_plans[sprint_id] = plan
        return plan

    async def _estimate_tasks(
        self, backlog_items: list[dict[str, Any]], velocity: Optional[int]
    ) -> list[TaskEstimate]:
        """Use AI to estimate story points for tasks."""
        estimates = []
        for item in backlog_items:
            # Simulate AI estimation (in production, call actual AI service)
            estimate = TaskEstimate(
                task_id=item["id"],
                title=item["title"],
                story_points=item.get("estimate", 5),
                confidence=item.get("confidence", 0.85),
                reasoning=f"Estimated based on task complexity and historical data",
                dependencies=item.get("dependencies", []),
                suggested_assignee=item.get("assignee"),
            )
            estimates.append(estimate)
        return estimates

    def _select_tasks_for_capacity(
        self, estimates: list[TaskEstimate], capacity: int
    ) -> list[TaskEstimate]:
        """Select tasks that fit within team capacity."""
        # Sort by confidence and priority
        sorted_estimates = sorted(estimates, key=lambda x: x.confidence, reverse=True)
        
        selected = []
        current_capacity = 0
        
        for estimate in sorted_estimates:
            if current_capacity + estimate.story_points <= capacity:
                selected.append(estimate)
                current_capacity += estimate.story_points
        
        return selected

    async def approve_plan(
        self, sprint_id: str, approver: str, notes: Optional[str] = None
    ) -> SprintPlan:
        """Approve a pending sprint plan."""
        plan = self._pending_plans.get(sprint_id)
        if not plan:
            raise ValueError(f"Sprint plan {sprint_id} not found")
        
        plan.status = ApprovalStatus.APPROVED
        plan.approver = approver
        plan.approval_notes = notes
        plan.modified_at = datetime.utcnow()
        
        return plan

    async def reject_plan(
        self, sprint_id: str, approver: str, reason: str
    ) -> SprintPlan:
        """Reject a pending sprint plan."""
        plan = self._pending_plans.get(sprint_id)
        if not plan:
            raise ValueError(f"Sprint plan {sprint_id} not found")
        
        plan.status = ApprovalStatus.REJECTED
        plan.approver = approver
        plan.approval_notes = reason
        plan.modified_at = datetime.utcnow()
        
        return plan

    def get_plan(self, sprint_id: str) -> Optional[SprintPlan]:
        """Retrieve sprint plan by ID."""
        return self._pending_plans.get(sprint_id)
