"""Get current time tool"""
from typing import Dict, Tuple
from datetime import datetime
import time

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "Retrieve the current system date and time in YYYY-MM-DD HH:MM:SS format. Use this when tasks require knowing the current time, like adding timestamps to files, logging events, or scheduling tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_timestamp": {
                    "type": "boolean",
                    "description": "If true, also return Unix timestamp and ISO format. Default: false"
                }
            }
        },
    },
}


def execute(args: Dict[str, object]) -> Tuple[str, bool]:
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    result = f"Current time: {time_str}"
    
    include_timestamp = bool(args.get("include_timestamp", False))
    if include_timestamp:
        unix_timestamp = int(time.time())
        iso_format = now.isoformat()
        result += f"\nUnix timestamp: {unix_timestamp}"
        result += f"\nISO format: {iso_format}"
    
    return result, False
