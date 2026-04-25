"""AI-powered sprint planning with approval workflow."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import json


class ApprovalStatus(Enum):
    """Sprint plan approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"


@dataclass
class SprintTask:
    """Represents a task in a sprint plan."""
    task_id: str
    title: str
    description: str
    story_points: int
    priority: int
    assignee: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "story_points": self.story_points,
            "priority": self.priority,
            "assignee": self.assignee,
            "dependencies": self.dependencies
        }


@dataclass
class SprintPlan:
    """Represents an AI-generated sprint plan."""
    plan_id: str
    sprint_name: str
    tasks: List[SprintTask]
    created_at: datetime
    created_by: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: Optional[str] = None
    approval_notes: Optional[str] = None
    total_story_points: int = 0

    def __post_init__(self):
        """Calculate total story points."""
        self.total_story_points = sum(task.story_points for task in self.tasks)

    def to_dict(self) -> dict:
        """Convert plan to dictionary."""
        return {
            "plan_id": self.plan_id,
            "sprint_name": self.sprint_name,
            "tasks": [task.to_dict() for task in self.tasks],
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "status": self.status.value,
            "approver": self.approver,
            "approval_notes": self.approval_notes,
            "total_story_points": self.total_story_points
        }


class SprintPlanApprovalWorkflow:
    """Manages approval workflow for AI-generated sprint plans."""

    def __init__(self):
        """Initialize the approval workflow."""
        self._plans: dict[str, SprintPlan] = {}

    def submit_plan(self, plan: SprintPlan) -> str:
        """Submit a sprint plan for approval."""
        self._plans[plan.plan_id] = plan
        return plan.plan_id

    def approve_plan(self, plan_id: str, approver: str, notes: Optional[str] = None) -> bool:
        """Approve a sprint plan."""
        if plan_id not in self._plans:
            return False
        
        plan = self._plans[plan_id]
        plan.status = ApprovalStatus.APPROVED
        plan.approver = approver
        plan.approval_notes = notes
        return True

    def reject_plan(self, plan_id: str, approver: str, notes: str) -> bool:
        """Reject a sprint plan."""
        if plan_id not in self._plans:
            return False
        
        plan = self._plans[plan_id]
        plan.status = ApprovalStatus.REJECTED
        plan.approver = approver
        plan.approval_notes = notes
        return True

    def revise_plan(self, plan_id: str, revised_tasks: List[SprintTask]) -> bool:
        """Revise a sprint plan with updated tasks."""
        if plan_id not in self._plans:
            return False
        
        plan = self._plans[plan_id]
        plan.tasks = revised_tasks
        plan.status = ApprovalStatus.REVISED
        plan.total_story_points = sum(task.story_points for task in revised_tasks)
        return True

    def get_plan(self, plan_id: str) -> Optional[SprintPlan]:
        """Retrieve a sprint plan by ID."""
        return self._plans.get(plan_id)

    def get_pending_plans(self) -> List[SprintPlan]:
        """Get all pending sprint plans."""
        return [p for p in self._plans.values() if p.status == ApprovalStatus.PENDING]

    def get_approved_plans(self) -> List[SprintPlan]:
        """Get all approved sprint plans."""
        return [p for p in self._plans.values() if p.status == ApprovalStatus.APPROVED]
