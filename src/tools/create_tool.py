"""Create tool - allows the agent to synthesize new tools"""
import json
from typing import Dict, Any, Tuple

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "create_tool",
        "description": "Synthesize and register a new tool. Provide a complete JSON specification with name, description, parameters (with types and descriptions), and Python implementation. The agent can use this to extend its capabilities dynamically.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Tool name (lowercase snake_case, 2-50 chars)"
                },
                "description": {
                    "type": "string",
                    "description": "Clear description of what the tool does (10-500 chars)"
                },
                "parameters": {
                    "type": "object",
                    "description": "JSON Schema for parameters: {type: 'object', properties: {...}, required: [...]}"
                },
                "implementation": {
                    "type": "string",
                    "description": "Python function body that receives 'args' dict and returns Tuple[str, bool]. Must return (result_message: str, should_exit: bool)"
                },
                "safety_notes": {
                    "type": "string",
                    "description": "Optional: Any safety or security notes about this tool"
                }
            },
            "required": ["name", "description", "parameters", "implementation"]
        }
    }
}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Create a new tool from a spec provided by the agent"""
    from src.tools.auto import AutoToolsRegistry
    
    registry = AutoToolsRegistry()
    
    spec = {
        "name": str(args.get("name", "")).strip(),
        "description": str(args.get("description", "")).strip(),
        "parameters": args.get("parameters", {}),
        "implementation": str(args.get("implementation", "")).strip(),
        "safety_notes": str(args.get("safety_notes", "")).strip()
    }
    
    success, message = registry.create_tool(spec)
    
    if success:
        return f"Tool '{spec['name']}' created successfully! You can now use it in subsequent tasks.", False
    else:
        return f"Failed to create tool: {message}", False
