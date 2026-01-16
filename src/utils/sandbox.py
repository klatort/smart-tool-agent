"""Sandbox environment for safely executing auto-generated tools"""
import sys
import os
from pathlib import Path
from typing import Dict, Callable, Any, Optional, Tuple
from functools import wraps
import time
import signal


class TimeoutError(Exception):
    """Raised when a function exceeds timeout"""
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Tool execution timed out")


class ToolSandbox:
    """Safe execution environment for auto-generated tools"""
    
    def __init__(self, 
                 allowed_paths: list[str] = None,
                 timeout_seconds: int = 10,
                 allowed_imports: list[str] = None):
        """
        Initialize sandbox
        
        Args:
            allowed_paths: Whitelist of filesystem paths tools can access
            timeout_seconds: Max execution time per tool
            allowed_imports: Whitelist of allowed module imports
        """
        self.allowed_paths = allowed_paths or [str(Path.home())]
        self.timeout_seconds = timeout_seconds
        self.allowed_imports = allowed_imports or ["json", "re", "datetime", "math", "random"]
    
    def validate_path(self, path: str) -> bool:
        """Check if path is in the allowed list"""
        try:
            abs_path = Path(path).resolve()
            for allowed in self.allowed_paths:
                allowed_path = Path(allowed).resolve()
                # Check if path is inside allowed directory
                if abs_path == allowed_path or allowed_path in abs_path.parents:
                    return True
        except Exception:
            pass
        return False
    
    def execute_tool(self, 
                     tool_func: Callable, 
                     args: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Execute a tool function safely
        
        Args:
            tool_func: The execute() function from an auto-tool
            args: Arguments to pass to the tool
        
        Returns:
            Tuple of (result: str, should_exit: bool) or error message
        """
        try:
            # Set timeout (Unix/Linux only for now)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)
            
            try:
                result = tool_func(args)
                
                # Validate result format
                if not isinstance(result, tuple) or len(result) != 2:
                    return f"Error: Tool must return Tuple[str, bool], got {type(result)}", False
                
                msg, should_exit = result
                if not isinstance(msg, str) or not isinstance(should_exit, bool):
                    return f"Error: Tool returned wrong types: ({type(msg)}, {type(should_exit)})", False
                
                return msg, should_exit
            
            finally:
                # Cancel alarm
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
        
        except TimeoutError:
            return f"Error: Tool execution timed out (>{self.timeout_seconds}s)", False
        except Exception as e:
            return f"Error executing tool: {type(e).__name__}: {str(e)}", False
    
    def create_safe_builtins(self) -> Dict[str, Any]:
        """Create a restricted set of built-in functions for tools"""
        # Start with a minimal set
        safe_builtins = {
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sum": sum,
            "min": min,
            "max": max,
            "sorted": sorted,
            "reversed": reversed,
            "all": all,
            "any": any,
            "abs": abs,
            "round": round,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
            "type": type,
        }
        return safe_builtins
