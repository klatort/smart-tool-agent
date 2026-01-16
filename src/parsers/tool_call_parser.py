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
            # JSON is incomplete or malformed - show detailed debugging info
            print(f"\n{Colors.RED}{'='*70}{Colors.RESET}")
            print(f"{Colors.RED}[JSON PARSE ERROR] Tool call arguments could not be parsed{Colors.RESET}")
            print(f"{Colors.RED}{'='*70}{Colors.RESET}")
            print(f"{Colors.YELLOW}Function: {self.function_name}{Colors.RESET}")
            print(f"{Colors.YELLOW}Error: {e.msg} at position {e.pos}{Colors.RESET}")
            print(f"{Colors.YELLOW}Line {e.lineno}, Column {e.colno}{Colors.RESET}")
            
            buffer = self.arguments_buffer
            buffer_len = len(buffer)
            
            # DETECT TRUNCATION: If buffer is small and incomplete, it was likely truncated
            is_truncated = (
                buffer_len < 500 and 
                (buffer.count('{') > buffer.count('}') or 
                 buffer.count('[') > buffer.count(']') or
                 buffer.count('"') % 2 != 0)
            )
            
            if is_truncated:
                print(f"\n{Colors.RED}⚠️  TRUNCATION DETECTED: Your content is being cut off by the API!{Colors.RESET}")
                print(f"{Colors.RED}   The 'content' argument is too large for a single tool call.{Colors.RESET}")
                print(f"{Colors.YELLOW}   SOLUTION: Split the content into smaller chunks or use a simpler approach.{Colors.RESET}")
            
            print(f"\n{Colors.CYAN}--- RAW BUFFER ({buffer_len} chars) ---{Colors.RESET}")
            
            # Show the buffer with position marker
            if buffer_len > 2000:
                # Truncate but show around the error position
                start = max(0, e.pos - 500)
                end = min(buffer_len, e.pos + 500)
                print(f"{Colors.YELLOW}[Showing chars {start}-{end} of {buffer_len}]{Colors.RESET}")
                buffer_display = buffer[start:end]
            else:
                buffer_display = buffer
            
            print(buffer_display)
            print(f"{Colors.CYAN}--- END RAW BUFFER ---{Colors.RESET}")
            
            # Detect common issues
            issues = []
            if buffer.count('{') != buffer.count('}'):
                issues.append(f"Unbalanced braces: {buffer.count('{')} open, {buffer.count('}')} close")
            if buffer.count('[') != buffer.count(']'):
                issues.append(f"Unbalanced brackets: {buffer.count('[')} open, {buffer.count(']')} close")
            if buffer.count('"') % 2 != 0:
                issues.append(f"Odd number of quotes: {buffer.count('\"')}")
            
            if issues:
                print(f"{Colors.YELLOW}Detected issues:{Colors.RESET}")
                for issue in issues:
                    print(f"  - {issue}")
            print()
            
            # Store truncation flag for agent recovery
            self._was_truncated = is_truncated
            
            return None
    
    def was_truncated(self) -> bool:
        """Check if last parse failure was due to truncation"""
        return getattr(self, '_was_truncated', False)
    
    def reset(self):
        """Clear the buffer for next tool call"""
        self.tool_call_id = None
        self.function_name = ""
        self.arguments_buffer = ""
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get current parser state for debugging"""
        return {
            "tool_call_id": self.tool_call_id,
            "function_name": self.function_name,
            "arguments_length": len(self.arguments_buffer),
            "arguments_preview": self.arguments_buffer[:200] if self.arguments_buffer else "",
            "is_complete": self.is_complete()
        }
