"""Tool synthesis engine for auto-generating tools from specs"""
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime


TOOL_SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "Tool name (snake_case, alphanumeric + underscore only)"
        },
        "description": {
            "type": "string",
            "description": "Clear description of what the tool does"
        },
        "parameters": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["object"]},
                "properties": {
                    "type": "object",
                    "description": "Parameter definitions (name -> {type, description})"
                },
                "required": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of required parameter names"
                }
            },
            "required": ["type", "properties"]
        },
        "implementation": {
            "type": "string",
            "description": "Python function body (receives args dict, returns Tuple[str, bool])"
        },
        "safety_notes": {
            "type": "string",
            "description": "Security/safety notes for reviewers"
        }
    },
    "required": ["name", "description", "parameters", "implementation"]
}


def validate_spec(spec: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a tool spec against the schema. Returns (valid, error_msg)"""
    # Check required fields
    required = ["name", "description", "parameters", "implementation"]
    for field in required:
        if field not in spec:
            return False, f"Missing required field: {field}"
    
    # Validate name format
    name = spec.get("name", "")
    if not name.isidentifier() or not name.islower():
        return False, f"Tool name '{name}' must be lowercase snake_case"
    
    if len(name) < 2 or len(name) > 50:
        return False, "Tool name must be 2-50 characters"
    
    # Validate description
    desc = spec.get("description", "")
    if not desc or len(desc) < 10 or len(desc) > 500:
        return False, "Description must be 10-500 characters"
    
    # Validate parameters
    params = spec.get("parameters", {})
    if not isinstance(params, dict):
        return False, "Parameters must be a dict"
    
    if params.get("type") != "object":
        return False, "Parameters type must be 'object'"
    
    props = params.get("properties", {})
    if not isinstance(props, dict):
        return False, "Parameters.properties must be a dict"
    
    # Validate each parameter
    for pname, pdef in props.items():
        if not isinstance(pdef, dict):
            return False, f"Parameter '{pname}' definition must be a dict"
        if "type" not in pdef:
            return False, f"Parameter '{pname}' missing 'type'"
        if "description" not in pdef:
            return False, f"Parameter '{pname}' missing 'description'"
    
    # Validate implementation
    impl = spec.get("implementation", "")
    if not impl or len(impl) < 20:
        return False, "Implementation must be at least 20 characters"
    
    # Check for dangerous patterns
    dangerous = ["__import__", "eval", "exec", "compile", "open", "file", "input", "raw_input"]
    for pattern in dangerous:
        if pattern in impl:
            return False, f"Implementation contains dangerous pattern: {pattern}"
    
    return True, None


def generate_tool_module(spec: Dict[str, Any], timestamp: str = None) -> str:
    """Generate a complete Python tool module from a spec"""
    if not timestamp:
        timestamp = datetime.now().isoformat()
    
    name = spec["name"]
    description = spec["description"]
    params = spec["parameters"]
    implementation = spec["implementation"]
    safety_notes = spec.get("safety_notes", "No safety notes provided")
    
    # Generate TOOL_DEF
    tool_def = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": params
        }
    }
    
    tool_def_str = json.dumps(tool_def, indent=2)
    
    # Indent the implementation code
    indented_impl = indent_code(implementation, 4)
    
    # Generate module code
    module_code = f'''"""Auto-generated tool: {name}
Generated at: {timestamp}
Safety notes: {safety_notes}
"""
from typing import Dict, Tuple, Any

TOOL_DEF = {tool_def_str}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Execute the tool function
    
    Args:
        args: Dictionary of parameters
    
    Returns:
        Tuple of (result_message: str, should_exit: bool)
    """
{indented_impl}
'''
    
    return module_code


def _indent_code(code: str, spaces: int) -> str:
    """Indent code block by N spaces"""
    indent = " " * spaces
    lines = code.split("\n")
    indented = [indent + line if line.strip() else line for line in lines]
    return "\n".join(indented)


# Export for patching in module generation
_indent_code_func = _indent_code


# Make indent accessible at module level
def indent_code(code: str, spaces: int) -> str:
    return _indent_code(code, spaces)
