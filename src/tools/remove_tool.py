"""Remove tool - allows the agent to clean up or delete auto-generated tools"""
from typing import Dict, Any, Tuple
from pathlib import Path

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "remove_tool",
        "description": "Delete an auto-generated tool that is no longer needed or is a duplicate. Use this to clean up tools you've created.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the tool to delete (e.g., 'get_ip_addresses_v2')"
                },
                "reason": {
                    "type": "string",
                    "description": "Optional: Reason for deletion (e.g., 'duplicate', 'broken', 'superseded')"
                }
            },
            "required": ["name"]
        }
    }
}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Remove an auto-generated tool"""
    from src.tools.auto import AutoToolsRegistry
    
    tool_name = str(args.get("name", "")).strip()
    reason = str(args.get("reason", "")).strip()
    
    if not tool_name:
        return "Error: Tool name is required", False
    
    registry = AutoToolsRegistry()
    success, message = registry.remove_tool(tool_name)
    
    if success:
        reason_str = f" ({reason})" if reason else ""
        return f"Tool '{tool_name}' has been successfully deleted{reason_str}.", False
    else:
        return f"Failed to delete tool: {message}", False
