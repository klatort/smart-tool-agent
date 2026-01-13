"""Auto-generated tool: reverse_text
Generated at: 2026-01-12T18:59:16.814655
Safety notes: 
"""
from typing import Dict, Tuple, Any

TOOL_DEF = {
  "type": "function",
  "function": {
    "name": "reverse_text",
    "description": "Reverse the characters in a text string",
    "parameters": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string",
          "description": "The text string to reverse"
        }
      },
      "required": [
        "text"
      ]
    }
  }
}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Execute the tool function
    
    Args:
        args: Dictionary of parameters
    
    Returns:
        Tuple of (result_message: str, should_exit: bool)
    """
    def reverse_text(args):
        text = args.get('text', '')
        reversed_text = text[::-1]
        return f'Reversed text: {reversed_text}', False
