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
        self.discarded_text: str = ""  # Track text discarded due to mixed output
    
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
        Handle a delta from the stream.
        Returns text to print, or None.
        
        IMPORTANT: If tool_calls are detected, we IGNORE any text content
        to prevent "gibberish" mixed output from cluttering the UI.
        """
        # Check for tool calls FIRST - if present, this is a tool-call response
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
        
        # Handle text content
        if "content" in delta and delta["content"]:
            content_piece = delta["content"]
            
            # ROBUST HANDLING: If we've detected tool calls, DISCARD text content
            # This prevents mixed output from creating gibberish
            if self.is_tool_call:
                self.discarded_text += content_piece
                # Don't return the text - it would create confusing output
                return None
            
            # Normal text response - accumulate and return
            self.text_buffer += content_piece
            return content_piece
        
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
            
            result = {
                "type": "tool_calls",
                "tool_calls": tool_calls
            }
            
            # Include discarded text for logging/debugging if any
            if self.discarded_text.strip():
                result["discarded_text"] = self.discarded_text.strip()
            
            return result
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
        self.discarded_text = ""
    
    def had_mixed_output(self) -> bool:
        """Check if this response had mixed text+tool_calls (indicates agent confusion)"""
        return self.is_tool_call and bool(self.discarded_text.strip())
    
    def get_discarded_text(self) -> str:
        """Get any text that was discarded due to mixed output"""
        return self.discarded_text.strip()

