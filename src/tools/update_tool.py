"""Update tool - allows the agent to modify existing auto-generated tools"""
import json
from typing import Dict, Any, Tuple

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "update_tool",
        "description": "Update or fix an existing auto-generated tool. Use this when a tool has bugs or needs modifications instead of creating it from scratch again. Provide the tool name and the corrected implementation.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the existing tool to update"
                },
                "implementation": {
                    "type": "string",
                    "description": "Updated Python function body that receives 'args' dict and returns Tuple[str, bool]. CRITICAL: EVERY return statement MUST return exactly 2 values: (result_message: str, should_exit: bool)"
                },
                "description": {
                    "type": "string",
                    "description": "Optional: Updated description if it needs to change"
                },
                "parameters": {
                    "type": "object",
                    "description": "Optional: Updated JSON Schema for parameters if it needs to change"
                },
                "fix_notes": {
                    "type": "string",
                    "description": "Optional: Notes about what was fixed or changed"
                }
            },
            "required": ["name", "implementation"]
        }
    }
}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Update an existing auto-generated tool"""
    from src.tools.auto import AutoToolsRegistry
    from pathlib import Path
    import importlib.util
    
    registry = AutoToolsRegistry()
    tool_name = str(args.get("name", "")).strip()
    
    if not tool_name:
        return "Error: Tool name is required", False
    
    # Check if tool exists
    if tool_name not in registry.registered_tools:
        return f"Error: Tool '{tool_name}' not found. Use create_tool to create a new tool.", False
    
    # Get existing tool info
    existing_tool = registry.registered_tools[tool_name]
    tool_file = Path(existing_tool["module_path"])
    
    # Read existing module to extract current TOOL_DEF
    try:
        spec_obj = importlib.util.spec_from_file_location(tool_name, tool_file)
        module = importlib.util.module_from_spec(spec_obj)
        spec_obj.loader.exec_module(module)
        current_def = module.TOOL_DEF
    except Exception as e:
        return f"Error reading existing tool: {e}", False
    
    # Build updated spec
    spec = {
        "name": tool_name,
        "description": args.get("description", current_def["function"]["description"]),
        "parameters": args.get("parameters", current_def["function"]["parameters"]),
        "implementation": str(args.get("implementation", "")).strip(),
        "safety_notes": args.get("fix_notes", "Tool updated by agent")
    }
    
    # Validate and regenerate
    from src.tools.synthesis import validate_spec, generate_tool_module
    
    valid, error = validate_spec(spec)
    if not valid:
        return f"Error: Invalid tool spec: {error}", False
    
    try:
        # Generate updated module code
        module_code = generate_tool_module(spec)
        
        # Write to disk (overwrite)
        tool_file.write_text(module_code, encoding='utf-8')
        
        # Reload the module
        spec_obj = importlib.util.spec_from_file_location(tool_name, tool_file)
        module = importlib.util.module_from_spec(spec_obj)
        spec_obj.loader.exec_module(module)
        
        # Update registry
        registry.registered_tools[tool_name] = {
            "def": module.TOOL_DEF,
            "func": module.execute,
            "module_path": str(tool_file),
            "auto_generated": True
        }
        
        return f"Tool '{tool_name}' successfully updated! You can now use the fixed version.", False
        
    except Exception as e:
        return f"Failed to update tool: {type(e).__name__}: {str(e)}", False
