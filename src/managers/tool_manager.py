"""Tool manager for registration and execution"""
from typing import Dict, List, Any, Callable, Tuple
from src.tools import get_tools, get_tool_functions


class ToolManager:
    """Manages tool definitions and execution"""
    
    def __init__(self):
        # Load tools from modular src.tools package
        self.tools: List[Dict[str, Any]] = get_tools()
        self.tool_functions: Dict[str, Callable] = get_tool_functions()
    
    def reload_tools(self):
        """Reload tool definitions and functions (after auto tool creation)."""
        self.tools = get_tools()
        self.tool_functions = get_tool_functions()
    
    def _register_default_tools(self):
        """Deprecated: tools are loaded from src.tools"""
        return
    
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], function: Callable):
        """Register a new tool"""
        tool_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
        self.tools.append(tool_def)
        self.tool_functions[name] = function
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for API request"""
        return self.tools
    
    def execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Execute a tool function
        Returns: (result_message, should_exit)
        """
        if function_name not in self.tool_functions:
            # Try reloading in case a new auto tool was just created
            self.reload_tools()
            if function_name not in self.tool_functions:
                return f"Error: Unknown tool '{function_name}'", False
        
        try:
            result = self.tool_functions[function_name](arguments)
            # If we just created a tool, refresh tool registry
            if function_name == "create_tool":
                self.reload_tools()
            return result
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}", False
    
    # --- Inline tool implementations have been moved to src.tools modules ---
