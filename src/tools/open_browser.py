"""Open browser tool"""
from typing import Dict, Tuple
import webbrowser

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "open_browser",
        "description": "Open a URL in the user's default web browser. Use this when the user wants to visit a website or link. The URL must be a complete HTTP or HTTPS link. For search queries, prepend 'https://www.google.com/search?q=' to the query.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The complete URL to open (must start with http:// or https://)"
                },
                "wait_seconds": {
                    "type": "integer",
                    "description": "Optional: Number of seconds to wait before opening (default: 0)"
                }
            },
            "required": ["url"]
        },
    },
}


def execute(args: Dict[str, object]) -> Tuple[str, bool]:
    url = str(args.get("url", ""))
    wait_seconds = int(args.get("wait_seconds", 0) or 0)
    
    if not url.startswith(("http://", "https://")):
        return f"Error: Invalid URL '{url}' (must start with http:// or https://)", False
    
    try:
        # We don't actually delay in the tool (agent loop handles flow)
        webbrowser.open(url)
        return f"Opened {url} in browser", False
    except Exception as e:
        return f"Failed to open browser: {str(e)}", False
