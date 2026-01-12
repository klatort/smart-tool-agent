"""Conversation history manager"""
from typing import Dict, List


class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self, system_prompt: str):
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
    
    def add_user_message(self, content: str):
        """Add a user message to history"""
        self.history.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str):
        """Add an assistant message to history"""
        self.history.append({"role": "assistant", "content": content})
    
    def add_tool_result(self, tool_call_id: str, function_name: str, result: str):
        """Add a tool result to history"""
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": function_name,
            "content": result
        })
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages for API request"""
        return self.history
