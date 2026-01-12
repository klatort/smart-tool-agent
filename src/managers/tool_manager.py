"""Tool manager for registration and execution"""
from typing import Dict, List, Any, Callable, Tuple
from src.tools import get_tools, get_tool_functions
from src.tools.auto import AutoToolsRegistry


class ToolManager:
    """Manages tool definitions and execution"""
    
    def __init__(self):
        # Load tools from modular src.tools package
        self.tools: List[Dict[str, Any]] = get_tools()
        self.tool_functions: Dict[str, Callable] = get_tool_functions()
        
        # Initialize auto-tools registry
        self.auto_registry = AutoToolsRegistry()
    
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
        """Get all tool definitions for API request (includes auto-tools)"""
        static_tools = get_tools()
        auto_tools = self.auto_registry.get_tools()
        return static_tools + auto_tools
    
    def execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Execute a tool function
        Routes to auto-tools if not found in static tools
        Returns: (result_message, should_exit)
        """
        # Try static tools first
        if function_name in self.tool_functions:
            try:
                result = self.tool_functions[function_name](arguments)
                # After create_tool, reload all tool definitions
                if function_name == "create_tool":
                    self.reload_tools()
                return result
            except Exception as e:
                return f"Error executing {function_name}: {str(e)}", False
        
        # Try auto-tools
        if function_name in self.auto_registry.registered_tools:
            return self.auto_registry.execute_tool(function_name, arguments)
        
        # Reload and try again (in case tool just created)
        self.reload_tools()
        if function_name in self.tool_functions:
            try:
                return self.tool_functions[function_name](arguments)
            except Exception as e:
                return f"Error executing {function_name}: {str(e)}", False
        
        if function_name in self.auto_registry.registered_tools:
            return self.auto_registry.execute_tool(function_name, arguments)
        
        return f"Error: Unknown tool '{function_name}'", False
    
    # --- Inline tool implementations have been moved to src.tools modules ---
