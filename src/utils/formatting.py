"""Utilities for formatting output"""
from src.config import Colors


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length and add ellipsis if needed"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... (truncated, {len(text) - max_length} more characters)"


def format_tool_result(result: str, tool_name: str) -> str:
    """Format a tool result for display"""
    # Truncate very long results
    truncated = truncate_text(result, max_length=800)
    return truncated


def format_step_header(step: int, total_steps: int = None, action: str = None) -> str:
    """Format a step header"""
    if total_steps:
        header = f"[Step {step}/{total_steps}]"
    else:
        header = f"[Step {step}]"
    
    if action:
        header += f" {action}"
    
    return f"{Colors.CYAN}{header}{Colors.RESET}"
