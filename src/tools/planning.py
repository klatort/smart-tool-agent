"""Planning tools for Plan-and-Execute Architecture"""
from typing import Dict, Any, Tuple, List

# Global agent state - shared across all planning tools
# This will be set by the Agent class on startup
_agent_state = None

def set_agent_state(state: Dict[str, Any]):
    """Called by Agent to inject the state reference"""
    global _agent_state
    _agent_state = state

def get_agent_state() -> Dict[str, Any]:
    """Get the current agent state"""
    global _agent_state
    if _agent_state is None:
        _agent_state = {
            "plan": [],
            "current_step": 0,
            "status": "idle"
        }
    return _agent_state


# ═══════════════════════════════════════════════════════════════════
# TOOL: create_plan
# ═══════════════════════════════════════════════════════════════════
CREATE_PLAN_DEF = {
    "type": "function",
    "function": {
        "name": "create_plan",
        "description": (
            "Create a new execution plan. Call this FIRST before doing any work. "
            "Break down the user's request into clear, sequential steps. "
            "Each step should be a single, actionable task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of steps to execute in order. Each step should be specific and actionable."
                }
            },
            "required": ["steps"]
        }
    }
}

def create_plan(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Create a new plan, overwriting any existing one"""
    state = get_agent_state()
    steps = args.get("steps", [])
    
    if not steps:
        return "Error: Plan must have at least one step.", False
    
    state["plan"] = steps
    state["current_step"] = 0
    state["status"] = "executing"
    
    # Format plan for display
    plan_display = "\n".join([f"  {i+1}. {step}" for i, step in enumerate(steps)])
    
    return f"✅ Plan created with {len(steps)} steps:\n{plan_display}\n\nNow executing Step 1: {steps[0]}", False


# ═══════════════════════════════════════════════════════════════════
# TOOL: update_plan
# ═══════════════════════════════════════════════════════════════════
UPDATE_PLAN_DEF = {
    "type": "function",
    "function": {
        "name": "update_plan",
        "description": (
            "Update the current plan dynamically. Use this when a step fails and you need to "
            "insert troubleshooting steps, or when you discover the plan needs adjustment. "
            "You can insert new steps, modify existing ones, or reorganize the plan."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "new_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The complete new list of steps (replaces existing plan)"
                },
                "current_step_index": {
                    "type": "integer",
                    "description": "Which step index to resume from (0-based). Usually the step that was being worked on."
                }
            },
            "required": ["new_steps", "current_step_index"]
        }
    }
}

def update_plan(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Update the plan with new steps"""
    state = get_agent_state()
    new_steps = args.get("new_steps", [])
    new_index = args.get("current_step_index", 0)
    
    if not new_steps:
        return "Error: New plan must have at least one step.", False
    
    if new_index < 0 or new_index >= len(new_steps):
        new_index = 0
    
    old_plan_len = len(state["plan"])
    state["plan"] = new_steps
    state["current_step"] = new_index
    state["status"] = "executing"
    
    # Format plan for display with current step marked
    plan_lines = []
    for i, step in enumerate(new_steps):
        if i < new_index:
            plan_lines.append(f"  {i+1}. ✓ {step}")
        elif i == new_index:
            plan_lines.append(f"  {i+1}. → {step} [CURRENT]")
        else:
            plan_lines.append(f"  {i+1}. ○ {step}")
    
    plan_display = "\n".join(plan_lines)
    
    return f"✅ Plan updated ({old_plan_len} → {len(new_steps)} steps):\n{plan_display}\n\nNow executing Step {new_index + 1}: {new_steps[new_index]}", False


# ═══════════════════════════════════════════════════════════════════
# TOOL: mark_step_complete
# ═══════════════════════════════════════════════════════════════════
MARK_STEP_COMPLETE_DEF = {
    "type": "function",
    "function": {
        "name": "mark_step_complete",
        "description": (
            "Mark the current step as complete and move to the next step. "
            "Call this after successfully completing a step's task. "
            "Include a brief summary of what was accomplished."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what was accomplished in this step"
                }
            },
            "required": ["summary"]
        }
    }
}

def mark_step_complete(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Mark current step as done and advance to next"""
    state = get_agent_state()
    summary = args.get("summary", "Step completed.")
    
    if not state["plan"]:
        return "Error: No plan exists. Call create_plan first.", False
    
    current = state["current_step"]
    total = len(state["plan"])
    
    if current >= total:
        return "Error: All steps already completed.", False
    
    completed_step = state["plan"][current]
    state["current_step"] = current + 1
    
    # Check if this was the last step
    if state["current_step"] >= total:
        state["status"] = "completed"
        return (
            f"✅ Step {current + 1}/{total} COMPLETE: {completed_step}\n"
            f"   Summary: {summary}\n\n"
            f"🎉 ALL STEPS COMPLETE! Call task_complete to finish."
        ), False
    else:
        next_step = state["plan"][state["current_step"]]
        return (
            f"✅ Step {current + 1}/{total} COMPLETE: {completed_step}\n"
            f"   Summary: {summary}\n\n"
            f"→ Next Step {state['current_step'] + 1}/{total}: {next_step}"
        ), False
