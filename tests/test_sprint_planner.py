"""Tests for sprint planner module."""

from datetime import datetime
import pytest

from src.auth.sprint_planner import (
    SprintTask,
    SprintPlan,
    SprintPlanApprovalWorkflow,
    ApprovalStatus
)


class TestSprintTask:
    """Tests for SprintTask."""

    def test_create_task(self):
        """Test creating a sprint task."""
        task = SprintTask(
            task_id="TASK-1",
            title="Implement feature",
            description="Add new functionality",
            story_points=5,
            priority=1
        )
        
        assert task.task_id == "TASK-1"
        assert task.story_points == 5
        assert task.assignee is None

    def test_task_to_dict(self):
        """Test converting task to dictionary."""
        task = SprintTask(
            task_id="TASK-2",
            title="Fix bug",
            description="Resolve issue",
            story_points=3,
            priority=2,
            assignee="dev@example.com"
        )
        
        task_dict = task.to_dict()
        assert task_dict["task_id"] == "TASK-2"
        assert task_dict["assignee"] == "dev@example.com"


class TestSprintPlan:
    """Tests for SprintPlan."""

    def test_create_plan(self):
        """Test creating a sprint plan."""
        tasks = [
            SprintTask("T1", "Task 1", "Desc", 3, 1),
            SprintTask("T2", "Task 2", "Desc", 5, 2)
        ]
        
        plan = SprintPlan(
            plan_id="PLAN-1",
            sprint_name="Sprint 1",
            tasks=tasks,
            created_at=datetime.utcnow(),
            created_by="pm@example.com"
        )
        
        assert plan.total_story_points == 8
        assert plan.status == ApprovalStatus.PENDING

    def test_plan_to_dict(self):
        """Test converting plan to dictionary."""
        tasks = [SprintTask("T1", "Task 1", "Desc", 3, 1)]
        plan = SprintPlan(
            plan_id="PLAN-2",
            sprint_name="Sprint 2",
            tasks=tasks,
            created_at=datetime.utcnow(),
            created_by="pm@example.com"
        )
        
        plan_dict = plan.to_dict()
        assert plan_dict["plan_id"] == "PLAN-2"
        assert len(plan_dict["tasks"]) == 1


class TestSprintPlanApprovalWorkflow:
    """Tests for SprintPlanApprovalWorkflow."""

    def test_submit_plan(self):
        """Test submitting a plan for approval."""
        workflow = SprintPlanApprovalWorkflow()
        plan = SprintPlan(
            plan_id="PLAN-1",
            sprint_name="Sprint 1",
            tasks=[],
            created_at=datetime.utcnow(),
            created_by="pm@example.com"
        )
        
        plan_id = workflow.submit_plan(plan)
        assert plan_id == "PLAN-1"
        assert workflow.get_plan(plan_id) is not None

    def test_approve_plan(self):
        """Test approving a plan."""
        workflow = SprintPlanApprovalWorkflow()
        plan = SprintPlan(
            plan_id="PLAN-2",
            sprint_name="Sprint 2",
            tasks=[],
            created_at=datetime.utcnow(),
            created_by="pm@example.com"
        )
        workflow.submit_plan(plan)
        
        success = workflow.approve_plan("PLAN-2", "manager@example.com", "Looks good")
        assert success is True
        
        retrieved_plan = workflow.get_plan("PLAN-2")
        assert retrieved_plan.status == ApprovalStatus.APPROVED
        assert retrieved_plan.approver == "manager@example.com"

    def test_reject_plan(self):
        """Test rejecting a plan."""
        workflow = SprintPlanApprovalWorkflow()
        plan = SprintPlan(
            plan_id="PLAN-3",
            sprint_name="Sprint 3",
            tasks=[],
            created_at=datetime.utcnow(),
            created_by="pm@example.com"
        )
        workflow.submit_plan(plan)
        
        success = workflow.reject_plan("PLAN-3", "manager@example.com", "Too ambitious")
        assert success is True
        
        retrieved_plan = workflow.get_plan("PLAN-3")
        assert retrieved_plan.status == ApprovalStatus.REJECTED

    def test_get_pending_plans(self):
        """Test retrieving pending plans."""
        workflow = SprintPlanApprovalWorkflow()
        plan1 = SprintPlan("P1", "S1", [], datetime.utcnow(), "user")
        plan2 = SprintPlan("P2", "S2", [], datetime.utcnow(), "user")
        
        workflow.submit_plan(plan1)
        workflow.submit_plan(plan2)
        workflow.approve_plan("P1", "approver")
        
        pending = workflow.get_pending_plans()
        assert len(pending) == 1
        assert pending[0].plan_id == "P2"
