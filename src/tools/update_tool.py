"""Update tool - reloads an existing auto-generated tool after file modification"""
import json
import traceback
from typing import Dict, Any, Tuple
from pathlib import Path
import importlib.util

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "update_tool",
        "description": "Reload an existing auto-generated tool after modifying its file. WORKFLOW: 1) Use read_file to see current code, 2) Use write_file to modify the .py file, 3) Call update_tool to reload it.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the existing tool to reload"
                },
                "file_path": {
                    "type": "string",
                    "description": "Optional: Path to a new Python file to replace the tool. If not provided, reloads from existing file path."
                },
                "fix_notes": {
                    "type": "string",
                    "description": "Optional: Notes about what was fixed or changed"
                }
            },
            "required": ["name"]
        }
    }
}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """
    Reload an existing auto-generated tool (Write-First approach).
    
    Workflow:
    1. Use read_file to see the current implementation
    2. Use write_file to modify the tool's .py file
    3. Call update_tool to reload and re-register it
    """
    from src.tools.auto import AutoToolsRegistry
    
    registry = AutoToolsRegistry()
    tool_name = str(args.get("name", "")).strip()
    file_path_str = str(args.get("file_path", "")).strip() if args.get("file_path") else None
    fix_notes = str(args.get("fix_notes", "")).strip() if args.get("fix_notes") else "Tool updated"
    
    if not tool_name:
        return "Error: Tool name is required", False
    
    # Check if tool exists
    if tool_name not in registry.registered_tools:
        return (
            f"Error: Tool '{tool_name}' not found.\n"
            f"Available tools: {', '.join(registry.registered_tools.keys())}\n"
            f"Use create_tool to create a new tool."
        ), False
    
    # Get existing tool info
    existing_tool = registry.registered_tools[tool_name]
    existing_path = Path(existing_tool["module_path"])
    
    # Determine which file to load from
    if file_path_str:
        tool_file = Path(file_path_str)
        if not tool_file.exists():
            return (
                f"Error: File '{file_path_str}' does not exist.\n"
                f"First write the updated code using write_file, then call update_tool."
            ), False
    else:
        tool_file = existing_path
        if not tool_file.exists():
            return (
                f"Error: Tool file '{existing_path}' no longer exists.\n"
                f"Use create_tool to recreate it."
            ), False
    
    # Read file content for validation
    try:
        file_content = tool_file.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error reading file '{tool_file}': {type(e).__name__}: {str(e)}", False
    
    # Basic validation
    if "TOOL_DEF" not in file_content:
        return f"Error: File '{tool_file}' is missing TOOL_DEF dictionary.", False
    
    if "def execute" not in file_content:
        return f"Error: File '{tool_file}' is missing execute() function.", False
    
    # Try to load the updated module
    try:
        module_name = f"auto_tool_{tool_name}"
        spec_obj = importlib.util.spec_from_file_location(module_name, tool_file)
        if spec_obj is None or spec_obj.loader is None:
            return f"Error: Could not create module spec for '{tool_file}'", False
        
        module = importlib.util.module_from_spec(spec_obj)
        spec_obj.loader.exec_module(module)
        
    except SyntaxError as e:
        return (
            f"SYNTAX ERROR in '{tool_file}':\n"
            f"  Line {e.lineno}: {e.msg}\n"
            f"  Code: {e.text}\n"
            f"Full traceback:\n{traceback.format_exc()}\n"
            f"Fix the error using write_file, then call update_tool again."
        ), False
        
    except Exception as e:
        return (
            f"ERROR loading '{tool_file}':\n"
            f"  {type(e).__name__}: {str(e)}\n"
            f"Full traceback:\n{traceback.format_exc()}\n"
            f"Fix the error using write_file, then call update_tool again."
        ), False
    
    # Validate module attributes
    if not hasattr(module, 'TOOL_DEF') or not hasattr(module, 'execute'):
        return "Error: Module loaded but missing TOOL_DEF or execute().", False
    
    # If using a different file, copy to the correct location
    auto_dir = Path(__file__).parent / "auto"
    final_path = auto_dir / f"{tool_name}.py"
    
    if tool_file.resolve() != final_path.resolve():
        try:
            final_path.write_text(file_content, encoding='utf-8')
            spec_obj = importlib.util.spec_from_file_location(module_name, final_path)
            module = importlib.util.module_from_spec(spec_obj)
            spec_obj.loader.exec_module(module)
        except Exception as e:
            return f"Error copying tool: {type(e).__name__}: {str(e)}", False
    
    # Update registry
    registry.registered_tools[tool_name] = {
        "def": module.TOOL_DEF,
        "func": module.execute,
        "module_path": str(final_path),
        "auto_generated": True
    }
    
    return f"Tool '{tool_name}' reloaded! {fix_notes}", False
