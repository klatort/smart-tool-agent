"""End chat tool"""
from typing import Dict, Tuple
from src.config import Colors

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "end_chat",
        "description": "End the conversation. Use only if the conversation is naturally complete or if the user explicitly asks to exit.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "A brief reason for ending the conversation"
                }
            },
            "required": ["reason"]
        },
    },
}


def execute(args: Dict[str, str]) -> Tuple[str, bool]:
    reason = args.get("reason", "No reason provided")
    print(f"\n{Colors.YELLOW}[SYSTEM]: The AI has decided to leave the chat.{Colors.RESET}")
    print(f"{Colors.YELLOW}[REASON]: {reason}{Colors.RESET}")
    return f"Chat ended: {reason}", True
