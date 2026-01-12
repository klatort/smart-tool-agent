"""Create new tool scaffold"""
from typing import Dict, Tuple
import os
from pathlib import Path
import json

TOOLS_DIR = Path(__file__).parent
AUTO_DIR = TOOLS_DIR / "auto"

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "create_tool",
        "description": "Create and register a new tool by providing a JSON spec (name, description, parameters). Generates a module under src/tools/auto and registers it for immediate use.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "New tool name (snake_case)"},
                "description": {"type": "string", "description": "Human-readable description of the tool"},
                "parameters": {"type": "object", "description": "JSON Schema for the tool's parameters"}
            },
            "required": ["name", "description", "parameters"]
        },
    },
}

TEMPLATE = '''"""Auto-generated tool: {name} """\nfrom typing import Dict, Tuple\n\nTOOL_DEF = {{\n    "type": "function",\n    "function": {{\n        "name": "{name}",\n        "description": "{description}",\n        "parameters": {parameters}\n    }},\n}}\n\n\n# NOTE: Implement safe logic here. Avoid network, OS-wide writes, or long runtimes.\n# Return a tuple (result: str, should_exit: bool)\ndef execute(args: Dict[str, object]) -> Tuple[str, bool]:\n    # TODO: Implement the actual tool behavior\n    return f"Tool '{name}' executed with args: {{args}}", False\n'''


def execute(args: Dict[str, object]) -> Tuple[str, bool]:
    name = str(args.get("name", "")).strip()
    description = str(args.get("description", "")).strip()
    parameters = args.get("parameters", {})
    
    # Basic validation
    if not name or not name.replace("_", "").isalnum():
        return "Error: Invalid tool name. Use snake_case alphanumerics.", False
    if not description:
        return "Error: Description is required.", False
    if not isinstance(parameters, dict):
        return "Error: parameters must be a JSON object (dict).", False
    
    AUTO_DIR.mkdir(parents=True, exist_ok=True)
    file_path = AUTO_DIR / f"{name}.py"
    if file_path.exists():
        return f"Error: Tool '{name}' already exists.", False
    
    # Serialize parameters JSON nicely
    params_json = json.dumps(parameters, indent=4)
    content = TEMPLATE.format(name=name, description=description.replace('"', '\\"'), parameters=params_json)
    
    file_path.write_text(content, encoding="utf-8")
    
    return f"Created tool '{name}' at {file_path}. Tool definitions reloaded.", False
