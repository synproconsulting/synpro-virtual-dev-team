"""Tests for PM agent chat interface."""

from datetime import datetime
import pytest

from src.auth.pm_agent_chat import PMAgentChat, ChatMessage
from src.auth.sprint_planner import SprintTask, ApprovalStatus


class MockAIProvider:
    """Mock AI provider for testing."""
    
    def generate_sprint_plan(self, context: str, requirements: list[str]) -> list[SprintTask]:
        """Generate mock sprint tasks."""
        return [
            SprintTask(
                task_id=f"AI-{idx}",
                title=f"AI Task {idx}",
                description=req,
                story_points=5,
                priority=idx
            )
            for idx, req in enumerate(requirements, 1)
        ]


class TestPMAgentChat:
    """Tests for PMAgentChat."""

    def test_send_message(self):
        """Test sending a message."""
        chat = PMAgentChat()
        message = chat.send_message("user@example.com", "Hello, PM Agent")
        
        assert message.user_id == "user@example.com"
        assert message.content == "Hello, PM Agent"
        assert message.message_type == "user"
        assert len(chat.get_chat_history()) == 1

    def test_generate_plan_without_ai(self):
        """Test generating a plan without AI provider."""
        chat = PMAgentChat()
        requirements = ["Implement login", "Add dashboard", "Create API"]
        
        plan = chat.generate_plan_from_chat(
            user_id="pm@example.com",
            sprint_name="Sprint Alpha",
            requirements=requirements
        )
        
        assert plan.sprint_name == "Sprint Alpha"
        assert len(plan.tasks) == 3
        assert plan.created_by == "pm@example.com"
        assert plan.status == ApprovalStatus.PENDING

    def test_generate_plan_with_ai(self):
        """Test generating a plan with AI provider."""
        ai_provider = MockAIProvider()
        chat = PMAgentChat(ai_provider=ai_provider)
        requirements = ["Feature A", "Feature B"]
        
        plan = chat.generate_plan_from_chat(
            user_id="pm@example.com",
            sprint_name="AI Sprint",
            requirements=requirements
        )
        
        assert len(plan.tasks) == 2
        assert plan.tasks[0].task_id.startswith("AI-")
        assert plan.total_story_points == 10

    def test_approve_plan(self):
        """Test approving a plan through chat."""
        chat = PMAgentChat()
        plan = chat.generate_plan_from_chat(
            "user@example.com",
            "Test Sprint",
            ["Task 1"]
        )
        
        success = chat.approve_plan(plan.plan_id, "manager@example.com", "Approved!")
        assert success is True
        
        status = chat.get_plan_status(plan.plan_id)
        assert status["status"] == "approved"
        assert status["approver"] == "manager@example.com"

    def test_reject_plan(self):
        """Test rejecting a plan through chat."""
        chat = PMAgentChat()
        plan = chat.generate_plan_from_chat(
            "user@example.com",
            "Test Sprint",
            ["Task 1"]
        )
        
        success = chat.reject_plan(plan.plan_id, "manager@example.com", "Need revision")
        assert success is True
        
        status = chat.get_plan_status(plan.plan_id)
        assert status["status"] == "rejected"
        assert status["approval_notes"] == "Need revision"

    def test_get_plan_status(self):
        """Test getting plan status."""
        chat = PMAgentChat()
        plan = chat.generate_plan_from_chat(
            "user@example.com",
            "Status Test",
            ["Task 1", "Task 2"]
        )
        
        status = chat.get_plan_status(plan.plan_id)
        assert status is not None
        assert status["sprint_name"] == "Status Test"
        assert len(status["tasks"]) == 2

    def test_chat_history_with_system_messages(self):
        """Test that system messages are added to chat history."""
        chat = PMAgentChat()
        chat.send_message("user@example.com", "Create a sprint")
        
        plan = chat.generate_plan_from_chat(
            "user@example.com",
            "Sprint 1",
            ["Task 1"]
        )
        
        history = chat.get_chat_history()
        system_messages = [msg for msg in history if msg.message_type == "system"]
        
        assert len(system_messages) > 0
        assert "Sprint plan" in system_messages[0].content
