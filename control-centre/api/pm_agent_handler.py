import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import openai


class PMAgentHandler:
    """Handles PM Agent chat interactions and sprint planning."""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        openai.api_key = self.api_key

    def process_chat_message(
        self,
        project_id: str,
        message: str,
        conversation_history: List[Dict],
        backlog_data: Optional[Dict] = None
    ) -> Dict:
        """Process a chat message and generate PM Agent response."""
        
        system_prompt = self._build_system_prompt(project_id, backlog_data)
        messages = self._format_conversation_history(conversation_history, system_prompt)
        messages.append({"role": "user", "content": message})

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                functions=[self._get_sprint_planning_function()],
                function_call="auto"
            )

            choice = response.choices[0]
            
            if choice.get("finish_reason") == "function_call":
                function_call = choice.message.get("function_call")
                if function_call and function_call.name == "create_sprint_plan":
                    sprint_plan = json.loads(function_call.arguments)
                    return {
                        "message": self._generate_sprint_summary(sprint_plan),
                        "sprint_plan": sprint_plan,
                        "requires_approval": True
                    }
            
            return {
                "message": choice.message.content,
                "sprint_plan": None,
                "requires_approval": False
            }

        except Exception as e:
            return {
                "message": f"I encountered an error: {str(e)}",
                "sprint_plan": None,
                "requires_approval": False
            }

    def _build_system_prompt(self, project_id: str, backlog_data: Optional[Dict]) -> str:
        """Build system prompt with context."""
        base_prompt = (
            "You are an expert Product Manager AI assistant. You help with sprint planning, "
            "story estimation, backlog analysis, and team capacity planning. "
            "You provide actionable insights and create detailed sprint plans when requested. "
            "Always consider team velocity, story complexity, and dependencies."
        )

        if backlog_data:
            context = f"\n\nProject context:\n"
            context += f"- Total backlog items: {len(backlog_data.get('items', []))}\n"
            context += f"- Unestimated stories: {backlog_data.get('unestimated_count', 0)}\n"
            context += f"- Average velocity: {backlog_data.get('avg_velocity', 'N/A')} points/sprint\n"
            base_prompt += context

        return base_prompt

    def _format_conversation_history(
        self, 
        history: List[Dict], 
        system_prompt: str
    ) -> List[Dict]:
        """Format conversation history for OpenAI API."""
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in history:
            if msg.get('role') in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        return messages

    def _get_sprint_planning_function(self) -> Dict:
        """Define the sprint planning function schema."""
        return {
            "name": "create_sprint_plan",
            "description": "Create a detailed sprint plan with stories and estimates",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Sprint name"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Sprint duration in days"
                    },
                    "stories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "points": {"type": "integer"},
                                "priority": {"type": "string"}
                            },
                            "required": ["title", "points"]
                        }
                    },
                    "total_points": {"type": "integer"}
                },
                "required": ["name", "duration", "stories", "total_points"]
            }
        }

    def _generate_sprint_summary(self, sprint_plan: Dict) -> str:
        """Generate a human-readable sprint summary."""
        summary = f"I've created a sprint plan called '{sprint_plan['name']}' with:\n\n"
        summary += f"• Duration: {sprint_plan['duration']} days\n"
        summary += f"• Total stories: {len(sprint_plan['stories'])}\n"
        summary += f"• Total story points: {sprint_plan['total_points']}\n\n"
        summary += "The plan includes high-priority items balanced with team capacity. "
        summary += "Would you like to approve this sprint plan?"
        return summary

    def create_sprint_from_plan(self, project_id: str, sprint_plan: Dict) -> Dict:
        """Create sprint in project management system."""
        # This would integrate with your actual sprint management system
        start_date = datetime.now()
        end_date = start_date + timedelta(days=sprint_plan['duration'])

        sprint = {
            "id": f"sprint-{int(start_date.timestamp())}",
            "project_id": project_id,
            "name": sprint_plan['name'],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "stories": sprint_plan['stories'],
            "total_points": sprint_plan['total_points'],
            "status": "planned",
            "created_at": datetime.now().isoformat(),
            "created_by": "pm-agent"
        }

        return sprint