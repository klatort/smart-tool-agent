"""Aggregate tools and provide ToolManager integration"""
from typing import Dict, List, Callable, Any
import os
import importlib.util
from pathlib import Path

from .end_chat import TOOL_DEF as END_CHAT_DEF, execute as end_chat_execute
from .open_browser import TOOL_DEF as OPEN_BROWSER_DEF, execute as open_browser_execute
from .get_current_time import TOOL_DEF as GET_CURRENT_TIME_DEF, execute as get_current_time_execute
from .read_file import TOOL_DEF as READ_FILE_DEF, execute as read_file_execute
from .write_file import TOOL_DEF as WRITE_FILE_DEF, execute as write_file_execute
from .create_tool import TOOL_DEF as CREATE_TOOL_DEF, execute as create_tool_execute
from .update_tool import TOOL_DEF as UPDATE_TOOL_DEF, execute as update_tool_execute
from .install_package import TOOL_DEF as INSTALL_PACKAGE_DEF, execute as install_package_execute
from .remove_tool import TOOL_DEF as REMOVE_TOOL_DEF, execute as remove_tool_execute

TOOLS_DIR = Path(__file__).parent
AUTO_DIR = TOOLS_DIR / "auto"

def _load_auto_tools() -> (List[Dict[str, Any]], Dict[str, Callable]):
    tool_defs: List[Dict[str, Any]] = []
    functions: Dict[str, Callable] = {}
    if not AUTO_DIR.exists():
        return tool_defs, functions
    
    for file in AUTO_DIR.glob("*.py"):
        if file.name == "__init__.py":
            continue
        module_name = f"src.tools.auto.{file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(file))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "TOOL_DEF") and hasattr(module, "execute"):
                tool_defs.append(getattr(module, "TOOL_DEF"))
                functions[getattr(module, "TOOL_DEF")["function"]["name"]] = getattr(module, "execute")
    return tool_defs, functions


def get_tools() -> List[Dict[str, Any]]:
    base = [
        END_CHAT_DEF,
        OPEN_BROWSER_DEF,
        GET_CURRENT_TIME_DEF,
        READ_FILE_DEF,
        WRITE_FILE_DEF,
        CREATE_TOOL_DEF,
        UPDATE_TOOL_DEF,
        INSTALL_PACKAGE_DEF,
        REMOVE_TOOL_DEF,
    ]
    auto_defs, _ = _load_auto_tools()
    return base + auto_defs


def get_tool_functions() -> Dict[str, Callable]:
    base = {
        "end_chat": end_chat_execute,
        "open_browser": open_browser_execute,
        "get_current_time": get_current_time_execute,
        "read_file": read_file_execute,
        "write_file": write_file_execute,
        "create_tool": create_tool_execute,
        "update_tool": update_tool_execute,
        "install_package": install_package_execute,
        "remove_tool": remove_tool_execute,
    }
    _, auto_funcs = _load_auto_tools()
    base.update(auto_funcs)
    return base
