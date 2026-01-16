"""Task completion tool - signals the agent has finished the user's request."""
from typing import Dict, Any, Tuple, List

TASK_COMPLETE_DEF = {
    "type": "function",
    "function": {
        "name": "task_complete",
        "description": (
            "Call this IMMEDIATELY when you have successfully finished the user's request. "
            "This signals that you are done and returns control to the user. "
            "DO NOT continue chatting after calling this. DO NOT ask 'anything else?'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what was accomplished (1-2 sentences)"
                },
                "result_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths created or modified (optional)"
                }
            },
            "required": ["summary"]
        }
    }
}


def task_complete(args: Dict[str, Any]) -> Tuple[str, bool]:
    """
    Signal task completion and return control to user.
    
    Returns:
        Tuple of (summary message, should_exit=True to break reasoning loop)
    """
    summary = args.get("summary", "Task completed.")
    result_files = args.get("result_files", [])
    
    # Build completion message
    msg_parts = [f"✅ TASK COMPLETE: {summary}"]
    
    if result_files:
        msg_parts.append("\n📁 Files:")
        for f in result_files:
            msg_parts.append(f"   • {f}")
    
    # Return True for exit_flag to break the reasoning loop
    return "\n".join(msg_parts), True
