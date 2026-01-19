"""Aggregate tools and provide ToolManager integration"""
from typing import Dict, List, Callable, Any
import os
import importlib.util
from pathlib import Path

from .get_current_time import TOOL_DEF as GET_CURRENT_TIME_DEF, execute as get_current_time_execute
from .read_file import TOOL_DEF as READ_FILE_DEF, execute as read_file_execute
from .write_file import TOOL_DEF as WRITE_FILE_DEF, execute as write_file_execute
from .web_search import TOOL_DEF as WEB_SEARCH_DEF, execute as web_search_execute
from .create_tool import TOOL_DEF as CREATE_TOOL_DEF, execute as create_tool_execute
from .update_tool import TOOL_DEF as UPDATE_TOOL_DEF, execute as update_tool_execute
from .install_package import TOOL_DEF as INSTALL_PACKAGE_DEF, execute as install_package_execute
from .remove_tool import TOOL_DEF as REMOVE_TOOL_DEF, execute as remove_tool_execute
from .task_complete import TASK_COMPLETE_DEF, task_complete as task_complete_execute
from .planning import (
    CREATE_PLAN_DEF, create_plan as create_plan_execute,
    UPDATE_PLAN_DEF, update_plan as update_plan_execute,
    MARK_STEP_COMPLETE_DEF, mark_step_complete as mark_step_complete_execute,
    set_agent_state, get_agent_state
)
from .run_command import TOOL_DEF as RUN_COMMAND_DEF, execute as run_command_execute
from .parallel_tasks import TOOL_DEF as PARALLEL_TASKS_DEF, execute as parallel_tasks_execute

TOOLS_DIR = Path(__file__).parent
AUTO_DIR = TOOLS_DIR / "auto"

# Track broken auto-tools so agent can see and fix them
_broken_auto_tools: Dict[str, str] = {}  # filename -> error message

def get_broken_tools() -> Dict[str, str]:
    """Get dict of broken auto-tools: {filename: error_message}"""
    return _broken_auto_tools.copy()

def _load_auto_tools() -> tuple[List[Dict[str, Any]], Dict[str, Callable]]:
    global _broken_auto_tools
    tool_defs: List[Dict[str, Any]] = []
    functions: Dict[str, Callable] = {}
    _broken_auto_tools = {}  # Reset on each load
    
    if not AUTO_DIR.exists():
        return tool_defs, functions
    
    for file in AUTO_DIR.glob("*.py"):
        if file.name == "__init__.py":
            continue
        module_name = f"src.tools.auto.{file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(file))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "TOOL_DEF") and hasattr(module, "execute"):
                    tool_defs.append(getattr(module, "TOOL_DEF"))
                    functions[getattr(module, "TOOL_DEF")["function"]["name"]] = getattr(module, "execute")
        except SyntaxError as e:
            error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
            _broken_auto_tools[file.name] = error_msg
            print(f"[Warning] Skipping broken tool '{file.name}': {error_msg}")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            _broken_auto_tools[file.name] = error_msg
            print(f"[Warning] Skipping broken tool '{file.name}': {error_msg}")
    
    return tool_defs, functions


def get_tools() -> List[Dict[str, Any]]:
    base = [
        GET_CURRENT_TIME_DEF,
        READ_FILE_DEF,
        WRITE_FILE_DEF,
        WEB_SEARCH_DEF,
        CREATE_TOOL_DEF,
        UPDATE_TOOL_DEF,
        INSTALL_PACKAGE_DEF,
        REMOVE_TOOL_DEF,
        TASK_COMPLETE_DEF,
        # Planning tools
        CREATE_PLAN_DEF,
        UPDATE_PLAN_DEF,
        MARK_STEP_COMPLETE_DEF,
        # Execution tools
        RUN_COMMAND_DEF,
        PARALLEL_TASKS_DEF,
    ]
    auto_defs, _ = _load_auto_tools()
    return base + auto_defs


def get_tool_functions() -> Dict[str, Callable]:
    base = {
        "get_current_time": get_current_time_execute,
        "read_file": read_file_execute,
        "write_file": write_file_execute,
        "web_search": web_search_execute,
        "create_tool": create_tool_execute,
        "update_tool": update_tool_execute,
        "install_package": install_package_execute,
        "remove_tool": remove_tool_execute,
        "task_complete": task_complete_execute,
        # Planning tools
        "create_plan": create_plan_execute,
        "update_plan": update_plan_execute,
        "mark_step_complete": mark_step_complete_execute,
        # Execution tools
        "run_command": run_command_execute,
        "parallel_tasks": parallel_tasks_execute,
    }
    _, auto_funcs = _load_auto_tools()
    base.update(auto_funcs)
    return base
