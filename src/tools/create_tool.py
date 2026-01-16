"""Create tool - registers a pre-written Python tool file"""
import json
import traceback
from typing import Dict, Any, Tuple
from pathlib import Path
import importlib.util

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "create_tool",
        "description": "Register a new tool from an existing Python file in src/tools/auto/. IMPORTANT: 1) Write tool code to src/tools/auto/toolname.py using write_file, 2) Call create_tool(name='toolname'). Tools MUST be in the auto folder.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the tool (file will be at src/tools/auto/<name>.py)"
                }
            },
            "required": ["name"]
        }
    }
}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """
    Register a tool from an existing Python file in src/tools/auto/.
    
    The file must contain:
    - TOOL_DEF: A dict with the tool's JSON schema
    - execute(args: Dict[str, Any]) -> Tuple[str, bool]: The tool function
    """
    from src.tools.auto import AutoToolsRegistry
    
    tool_name = str(args.get("name", "")).strip()
    
    if not tool_name:
        return "Error: name is required. Example: create_tool(name='my_calculator')", False
    
    # Sanitize tool name (alphanumeric and underscores only)
    sanitized_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in tool_name)
    if sanitized_name != tool_name:
        return f"Error: Tool name '{tool_name}' contains invalid characters. Use only letters, numbers, and underscores.", False
    
    # Reject naming patterns that suggest "fixing" another tool instead of updating it
    name_lower = tool_name.lower()
    bad_prefixes = ('fixed_', 'fix_', 'new_', 'improved_', 'better_', 'working_', 'correct_', 'updated_')
    bad_suffixes = ('_fixed', '_fix', '_new', '_improved', '_better', '_working', '_correct', '_updated', '_v2', '_v3', '_v4', '_final', '_2', '_3')
    
    if any(name_lower.startswith(p) for p in bad_prefixes):
        # Extract the likely original tool name
        for prefix in bad_prefixes:
            if name_lower.startswith(prefix):
                original = tool_name[len(prefix):]
                break
        return (
            f"Error: Tool name '{tool_name}' looks like a 'fixed' version of '{original}'.\n"
            f"DON'T create new tools to fix broken ones. Instead:\n"
            f"  1. read_file('src/tools/auto/{original}.py') - see current code\n"
            f"  2. write_file('src/tools/auto/{original}.py', fixed_code) - fix it\n"
            f"  3. update_tool(name='{original}') - reload it\n"
            f"If '{original}' doesn't exist, use create_tool(name='{original}') instead."
        ), False
    
    if any(name_lower.endswith(s) for s in bad_suffixes):
        # Extract the likely original tool name
        for suffix in bad_suffixes:
            if name_lower.endswith(suffix):
                original = tool_name[:-len(suffix)]
                break
        return (
            f"Error: Tool name '{tool_name}' looks like a variant of '{original}'.\n"
            f"DON'T create new tools to fix broken ones. Instead:\n"
            f"  1. read_file('src/tools/auto/{original}.py') - see current code\n"
            f"  2. write_file('src/tools/auto/{original}.py', fixed_code) - fix it\n"
            f"  3. update_tool(name='{original}') - reload it\n"
            f"If '{original}' doesn't exist, use create_tool(name='{original}') instead."
        ), False
    
    # Tools MUST be in src/tools/auto/
    auto_dir = Path(__file__).parent / "auto"
    auto_dir.mkdir(parents=True, exist_ok=True)
    tool_file = auto_dir / f"{tool_name}.py"
    
    # Check if file exists in auto folder
    if not tool_file.exists():
        return (
            f"Error: Tool file not found at '{tool_file}'.\n"
            f"You must FIRST write the tool code, THEN call create_tool.\n"
            f"Correct workflow:\n"
            f"  1. write_file(file_path='src/tools/auto/{tool_name}.py', content='...code...')\n"
            f"  2. create_tool(name='{tool_name}')"
        ), False
    
    if not tool_file.is_file():
        return f"Error: '{tool_file}' is not a file.", False
    
    # Read the file content for error reporting
    try:
        file_content = tool_file.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error reading file '{tool_file}': {type(e).__name__}: {str(e)}", False
    
    # Validate file has minimum required content
    if "TOOL_DEF" not in file_content:
        return (
            f"Error: File '{tool_file}' is missing TOOL_DEF dictionary.\n"
            f"The file must contain TOOL_DEF and execute() function."
        ), False
    
    if "def execute" not in file_content:
        return (
            f"Error: File '{tool_file}' is missing execute() function.\n"
            f"The file must contain: def execute(args: Dict[str, Any]) -> Tuple[str, bool]:"
        ), False
    
    # Try to load the module
    try:
        module_name = tool_file.stem
        spec_obj = importlib.util.spec_from_file_location(module_name, tool_file)
        if spec_obj is None or spec_obj.loader is None:
            return f"Error: Could not create module spec for '{tool_file}'", False
        
        module = importlib.util.module_from_spec(spec_obj)
        spec_obj.loader.exec_module(module)
        
    except SyntaxError as e:
        return (
            f"SYNTAX ERROR in 'src/tools/auto/{tool_name}.py':\n"
            f"  Line {e.lineno}: {e.msg}\n"
            f"  Code: {e.text}\n"
            f"Full traceback:\n{traceback.format_exc()}\n"
            f"Fix the syntax error using write_file and call create_tool(name='{tool_name}') again."
        ), False
        
    except Exception as e:
        return (
            f"ERROR loading 'src/tools/auto/{tool_name}.py':\n"
            f"  {type(e).__name__}: {str(e)}\n"
            f"Full traceback:\n{traceback.format_exc()}\n"
            f"Fix the error using write_file and call create_tool(name='{tool_name}') again."
        ), False
    
    # Validate the module has required attributes
    if not hasattr(module, 'TOOL_DEF'):
        return "Error: Module loaded but TOOL_DEF not found at module level.", False
    
    if not hasattr(module, 'execute'):
        return "Error: Module loaded but execute() function not found.", False
    
    # Validate TOOL_DEF structure
    tool_def = module.TOOL_DEF
    if not isinstance(tool_def, dict):
        return f"Error: TOOL_DEF must be a dict, got {type(tool_def).__name__}", False
    
    if "function" not in tool_def or "name" not in tool_def.get("function", {}):
        return "Error: TOOL_DEF has invalid structure. Needs 'function' with 'name' key.", False
    
    # Verify tool name in TOOL_DEF matches
    def_name = tool_def["function"]["name"]
    if def_name != tool_name:
        return (
            f"Error: Tool name mismatch. File name is '{tool_name}' but TOOL_DEF name is '{def_name}'.\n"
            f"Update the TOOL_DEF in the file to use name='{tool_name}', or rename the file."
        ), False
    
    # Initialize registry and check for duplicates
    registry = AutoToolsRegistry()
    
    if tool_name in registry.registered_tools:
        return f"Error: Tool '{tool_name}' already exists. Use update_tool(name='{tool_name}') to modify it.", False
    
    # Validate execute function
    if not callable(module.execute):
        return f"Error: execute is not callable in 'src/tools/auto/{tool_name}.py'", False
    
    # Register the tool (file is already in auto directory)
    registry.registered_tools[tool_name] = {
        "def": module.TOOL_DEF,
        "func": module.execute,
        "module_path": str(tool_file),
        "auto_generated": True
    }
    
    return f"Tool '{tool_name}' successfully registered from src/tools/auto/{tool_name}.py!", False
