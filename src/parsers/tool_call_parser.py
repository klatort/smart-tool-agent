"""Tool call parser for handling streaming JSON chunks"""
import json
from typing import Dict, Any, Optional
from src.config import Colors


class ToolCallParser:
    """Handles partial JSON chunks and validates complete JSON before parsing"""
    
    def __init__(self):
        self.tool_call_id: Optional[str] = None
        self.function_name: str = ""
        self.arguments_buffer: str = ""
        
    def add_chunk(self, tool_call_delta: Dict[str, Any]) -> None:
        """Add a streaming chunk to the buffer"""
        if "id" in tool_call_delta:
            self.tool_call_id = tool_call_delta["id"]
        
        if "function" in tool_call_delta:
            func = tool_call_delta["function"]
            if "name" in func:
                self.function_name += func["name"]
            if "arguments" in func:
                self.arguments_buffer += func["arguments"]
    
    def is_complete(self) -> bool:
        """Check if we have accumulated a complete tool call"""
        return bool(self.tool_call_id and self.function_name and self.arguments_buffer)
    
    def validate_and_parse(self) -> Optional[Dict[str, Any]]:
        """Validate JSON completeness and parse arguments"""
        if not self.is_complete():
            return None
        
        # Try to parse the accumulated JSON
        try:
            args = json.loads(self.arguments_buffer)
            return {
                "id": self.tool_call_id,
                "function_name": self.function_name,
                "arguments": args
            }
        except json.JSONDecodeError as e:
            # JSON is incomplete or malformed
            print(f"\n{Colors.RED}[JSON Parse Error]: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}[Raw Arguments]: {self.arguments_buffer}{Colors.RESET}")
            return None
    
    def reset(self):
        """Clear the buffer for next tool call"""
        self.tool_call_id = None
        self.function_name = ""
        self.arguments_buffer = ""
