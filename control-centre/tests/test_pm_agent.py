import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from control-centre.api.pm_agent_handler import PMAgentHandler


class TestPMAgentHandler:
    """Test suite for PM Agent handler."""

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_handler_initialization(self):
        """Test handler initializes correctly."""
        handler = PMAgentHandler()
        assert handler.api_key == 'test-key'

    def test_handler_initialization_without_key(self):
        """Test handler raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                PMAgentHandler()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_build_system_prompt(self):
        """Test system prompt building."""
        handler = PMAgentHandler()
        
        prompt = handler._build_system_prompt('proj-1', None)
        assert 'Product Manager' in prompt
        assert 'sprint planning' in prompt

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_build_system_prompt_with_context(self):
        """Test system prompt with backlog context."""
        handler = PMAgentHandler()
        backlog_data = {
            'items': [1, 2, 3],
            'unestimated_count': 5,
            'avg_velocity': 25
        }
        
        prompt = handler._build_system_prompt('proj-1', backlog_data)
        assert 'Total backlog items: 3' in prompt
        assert 'Average velocity: 25' in prompt

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_format_conversation_history(self):
        """Test conversation history formatting."""
        handler = PMAgentHandler()
        history = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there'}
        ]
        
        messages = handler._format_conversation_history(history, 'System prompt')
        assert len(messages) == 3
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert messages[2]['role'] == 'assistant'

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_get_sprint_planning_function(self):
        """Test sprint planning function schema."""
        handler = PMAgentHandler()
        function = handler._get_sprint_planning_function()
        
        assert function['name'] == 'create_sprint_plan'
        assert 'parameters' in function
        assert 'name' in function['parameters']['properties']
        assert 'stories' in function['parameters']['properties']

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_generate_sprint_summary(self):
        """Test sprint summary generation."""
        handler = PMAgentHandler()
        sprint_plan = {
            'name': 'Sprint 1',
            'duration': 14,
            'stories': [{'title': 'Story 1', 'points': 5}],
            'total_points': 5
        }
        
        summary = handler._generate_sprint_summary(sprint_plan)
        assert 'Sprint 1' in summary
        assert '14 days' in summary
        assert '5' in summary

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.ChatCompletion.create')
    def test_process_chat_message_simple_response(self, mock_openai):
        """Test processing simple chat message."""
        mock_openai.return_value = Mock(
            choices=[Mock(
                message=Mock(content='Here is my response'),
                finish_reason='stop'
            )]
        )
        
        handler = PMAgentHandler()
        result = handler.process_chat_message(
            project_id='proj-1',
            message='Hello',
            conversation_history=[]
        )
        
        assert result['message'] == 'Here is my response'
        assert result['sprint_plan'] is None
        assert result['requires_approval'] is False

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_create_sprint_from_plan(self):
        """Test sprint creation from plan."""
        handler = PMAgentHandler()
        sprint_plan = {
            'name': 'Sprint 1',
            'duration': 14,
            'stories': [{'title': 'Story 1', 'points': 5}],
            'total_points': 5
        }
        
        sprint = handler.create_sprint_from_plan('proj-1', sprint_plan)
        
        assert sprint['project_id'] == 'proj-1'
        assert sprint['name'] == 'Sprint 1'
        assert sprint['status'] == 'planned'
        assert sprint['created_by'] == 'pm-agent'
        assert len(sprint['stories']) == 1