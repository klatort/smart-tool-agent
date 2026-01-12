"""Stream parser for handling Server-Sent Events"""
import json
from typing import Dict, Any, Optional, List
from .tool_call_parser import ToolCallParser


class StreamParser:
    """Handles Server-Sent Events stream parsing"""
    
    def __init__(self):
        self.text_buffer: str = ""
        self.tool_parsers: Dict[int, ToolCallParser] = {}  # Map index to parser
        self.is_tool_call: bool = False
    
    def process_line(self, line: bytes) -> Optional[Dict[str, Any]]:
        """Process a single SSE line and return delta if valid"""
        if not line:
            return None
        
        decoded_line = line.decode('utf-8')
        if not decoded_line.startswith('data: '):
            return None
        
        data_str = decoded_line.replace('data: ', '', 1)
        if data_str.strip() == '[DONE]':
            return {'done': True}
        
        try:
            data_json = json.loads(data_str)
            if "choices" not in data_json or len(data_json["choices"]) == 0:
                return None
            
            choice = data_json["choices"][0]
            delta = choice.get("delta", {})
            return delta
            
        except json.JSONDecodeError:
            return None
    
    def handle_delta(self, delta: Dict[str, Any]) -> Optional[str]:
        """
        Handle a delta from the stream
        Returns text to print, or None
        """
        # Handle text content
        if "content" in delta and delta["content"]:
            content_piece = delta["content"]
            self.text_buffer += content_piece
            return content_piece
        
        # Handle tool calls (can be multiple)
        if "tool_calls" in delta and delta["tool_calls"]:
            self.is_tool_call = True
            for tool_call_delta in delta["tool_calls"]:
                # Get the index from the delta (tool calls are indexed)
                index = tool_call_delta.get("index", 0)
                
                # Create a parser for this index if it doesn't exist
                if index not in self.tool_parsers:
                    self.tool_parsers[index] = ToolCallParser()
                
                # Add the chunk to the appropriate parser
                self.tool_parsers[index].add_chunk(tool_call_delta)
        
        return None
    
    def get_result(self) -> Dict[str, Any]:
        """Get the final parsed result"""
        if self.is_tool_call:
            # Parse all tool calls
            tool_calls = []
            for index in sorted(self.tool_parsers.keys()):
                tool_call = self.tool_parsers[index].validate_and_parse()
                if tool_call:
                    tool_calls.append(tool_call)
            
            return {
                "type": "tool_calls",
                "tool_calls": tool_calls
            }
        else:
            return {
                "type": "text",
                "content": self.text_buffer
            }
    
    def reset(self):
        """Reset for next message"""
        self.text_buffer = ""
        self.tool_parsers.clear()
        self.is_tool_call = False

