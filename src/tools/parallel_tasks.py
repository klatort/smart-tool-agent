"""Parallel tasks tool - execute multiple independent operations concurrently"""
import concurrent.futures
import threading
import time
from typing import Dict, Tuple, Any, List
from pathlib import Path

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "parallel_tasks",
        "description": (
            "Execute multiple INDEPENDENT tasks in parallel to speed up work. "
            "Each task is a dict with 'tool' (tool name) and 'args' (arguments). "
            "Only use for tasks that don't depend on each other's results. "
            "Example: reading multiple files, making multiple searches, processing multiple items."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "List of tasks to execute in parallel",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Identifier for this task (for tracking results)"
                            },
                            "tool": {
                                "type": "string",
                                "description": "Name of the tool to execute"
                            },
                            "args": {
                                "type": "object",
                                "description": "Arguments to pass to the tool"
                            }
                        },
                        "required": ["id", "tool", "args"]
                    }
                },
                "max_workers": {
                    "type": "integer",
                    "description": "Maximum parallel workers (default: 4, max: 8)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout per task in seconds (default: 60)"
                }
            },
            "required": ["tasks"]
        }
    }
}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Execute multiple tasks in parallel."""
    from src.managers import ToolManager
    
    tasks = args.get("tasks", [])
    max_workers = min(int(args.get("max_workers", 4)), 8)  # Cap at 8
    timeout_per_task = int(args.get("timeout", 60))
    
    if not tasks:
        return "Error: tasks list is required and cannot be empty", False
    
    if len(tasks) > 20:
        return "Error: Maximum 20 tasks per parallel execution", False
    
    # Validate tasks structure
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            return f"Error: Task {i} must be a dict with 'id', 'tool', 'args'", False
        if "id" not in task or "tool" not in task or "args" not in task:
            return f"Error: Task {i} missing required fields (id, tool, args)", False
    
    # Tools that should NOT run in parallel (state-modifying, risky)
    dangerous_parallel_tools = {
        "write_file", "create_tool", "update_tool", "remove_tool",
        "install_package", "run_command", "create_plan", "update_plan",
        "mark_step_complete", "task_complete"
    }
    
    # Check for dangerous tools
    for task in tasks:
        if task["tool"] in dangerous_parallel_tools:
            return (
                f"Error: Tool '{task['tool']}' cannot be run in parallel (state-modifying).\n"
                f"Safe parallel tools: read_file, web_search, get_current_time, etc.\n"
                f"For write operations, execute sequentially."
            ), False
    
    # Create tool manager for execution
    tool_manager = ToolManager()
    
    results = {}
    errors = {}
    start_time = time.time()
    
    def execute_single_task(task: Dict) -> Tuple[str, str, bool]:
        """Execute a single task and return (id, result, success)."""
        task_id = task["id"]
        tool_name = task["tool"]
        tool_args = task["args"]
        
        try:
            result, should_exit = tool_manager.execute_tool(tool_name, tool_args)
            return (task_id, result, True)
        except Exception as e:
            return (task_id, f"Error: {str(e)}", False)
    
    # Execute tasks in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(execute_single_task, task): task
            for task in tasks
        }
        
        # Collect results with timeout
        for future in concurrent.futures.as_completed(future_to_task, timeout=timeout_per_task * len(tasks)):
            task = future_to_task[future]
            try:
                task_id, result, success = future.result(timeout=timeout_per_task)
                if success:
                    results[task_id] = result
                else:
                    errors[task_id] = result
            except concurrent.futures.TimeoutError:
                errors[task["id"]] = f"Task timed out after {timeout_per_task}s"
            except Exception as e:
                errors[task["id"]] = f"Execution error: {str(e)}"
    
    elapsed = time.time() - start_time
    
    # Format output
    output_lines = [
        f"═══ PARALLEL EXECUTION COMPLETE ═══",
        f"Tasks: {len(tasks)} | Success: {len(results)} | Failed: {len(errors)} | Time: {elapsed:.2f}s",
        ""
    ]
    
    if results:
        output_lines.append("─── RESULTS ───")
        for task_id, result in results.items():
            # Truncate long results
            result_preview = result[:1000] + "..." if len(result) > 1000 else result
            output_lines.append(f"\n[{task_id}]:\n{result_preview}")
    
    if errors:
        output_lines.append("\n─── ERRORS ───")
        for task_id, error in errors.items():
            output_lines.append(f"\n[{task_id}]: {error}")
    
    return "\n".join(output_lines), False
