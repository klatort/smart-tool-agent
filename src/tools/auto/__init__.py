"""Auto-tools registry and manager"""
import importlib.util
import json
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional, Tuple
from src.tools.synthesis import validate_spec, generate_tool_module, indent_code
from src.tools.sandbox import ToolSandbox


class AutoToolsRegistry:
    """Manages dynamically generated and registered tools"""
    
    def __init__(self, sandbox: ToolSandbox = None):
        self.sandbox = sandbox or ToolSandbox()
        self.auto_tools_dir = Path(__file__).parent / "auto"
        self.auto_tools_dir.mkdir(exist_ok=True)
        self.registered_tools: Dict[str, Dict[str, Any]] = {}  # name -> {def, func, module_path}
        self.load_existing_auto_tools()
    
    def load_existing_auto_tools(self):
        """Load previously generated auto-tools from disk"""
        for tool_file in self.auto_tools_dir.glob("*.py"):
            if tool_file.name == "__init__.py":
                continue
            
            tool_name = tool_file.stem
            try:
                spec = importlib.util.spec_from_file_location(tool_name, tool_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "TOOL_DEF") and hasattr(module, "execute"):
                    tool_def = module.TOOL_DEF
                    self.registered_tools[tool_name] = {
                        "def": tool_def,
                        "func": module.execute,
                        "module_path": str(tool_file),
                        "auto_generated": True
                    }
            except Exception as e:
                print(f"Warning: Failed to load auto-tool {tool_name}: {e}")
    
    def create_tool(self, spec: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create and register a new tool from a spec
        
        Returns:
            (success: bool, message: str)
        """
        # Validate spec
        valid, error = validate_spec(spec)
        if not valid:
            return False, f"Invalid tool spec: {error}"
        
        tool_name = spec["name"]
        
        # Check if tool already exists
        if tool_name in self.registered_tools:
            return False, f"Tool '{tool_name}' already exists"
        
        try:
            # Generate module code
            module_code = generate_tool_module(spec)
            
            # Write to disk
            tool_file = self.auto_tools_dir / f"{tool_name}.py"
            tool_file.write_text(module_code, encoding='utf-8')
            
            # Load the module
            spec_obj = importlib.util.spec_from_file_location(tool_name, tool_file)
            module = importlib.util.module_from_spec(spec_obj)
            spec_obj.loader.exec_module(module)
            
            # Register
            self.registered_tools[tool_name] = {
                "def": module.TOOL_DEF,
                "func": module.execute,
                "module_path": str(tool_file),
                "auto_generated": True
            }
            
            return True, f"Tool '{tool_name}' created and registered successfully"
        
        except Exception as e:
            # Clean up file if it was created
            tool_file = self.auto_tools_dir / f"{tool_name}.py"
            if tool_file.exists():
                tool_file.unlink()
            return False, f"Failed to create tool: {type(e).__name__}: {str(e)}"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all auto-tool definitions"""
        return [info["def"] for info in self.registered_tools.values()]
    
    def get_tool_functions(self) -> Dict[str, Callable]:
        """Get all auto-tool execution functions"""
        return {name: info["func"] for name, info in self.registered_tools.items()}
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, bool]:
        """Execute an auto-tool safely"""
        if tool_name not in self.registered_tools:
            return f"Error: Unknown auto-tool '{tool_name}'", False
        
        tool_func = self.registered_tools[tool_name]["func"]
        return self.sandbox.execute_tool(tool_func, args)
    
    def list_auto_tools(self) -> List[str]:
        """List names of all registered auto-tools"""
        return list(self.registered_tools.keys())
    
    def disable_tool(self, tool_name: str) -> Tuple[bool, str]:
        """Temporarily disable a tool (doesn't delete it)"""
        if tool_name not in self.registered_tools:
            return False, f"Tool '{tool_name}' not found"
        
        del self.registered_tools[tool_name]
        return True, f"Tool '{tool_name}' disabled"
    
    def remove_tool(self, tool_name: str) -> Tuple[bool, str]:
        """Permanently remove an auto-tool"""
        if tool_name not in self.registered_tools:
            return False, f"Tool '{tool_name}' not found"
        
        try:
            module_path = self.registered_tools[tool_name]["module_path"]
            Path(module_path).unlink()
            del self.registered_tools[tool_name]
            return True, f"Tool '{tool_name}' removed"
        except Exception as e:
            return False, f"Failed to remove tool: {e}"
