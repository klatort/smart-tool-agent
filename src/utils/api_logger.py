"""API Request/Response Logger - Captures full API communication for debugging"""
import json
import os
from datetime import datetime

# File to store raw API communications
RAW_LOG_FILE = "api_raw.log"

def log_request(step: int, payload: dict):
    """Log the full API request payload."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "request",
        "step": step,
        "payload": {
            "model": payload.get("model"),
            "temperature": payload.get("temperature"),
            "top_p": payload.get("top_p"),
            "max_tokens": payload.get("max_tokens"),
            "message_count": len(payload.get("messages", [])),
            "tools_count": len(payload.get("tools", [])),
            "messages": payload.get("messages", [])  # Full messages for debugging
        }
    }
    
    with open(RAW_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def log_response(step: int, response_text: str, response_type: str):
    """Log the full API response."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "response",
        "step": step,
        "response_type": response_type,
        "content": response_text,
        "content_length": len(response_text)
    }
    
    with open(RAW_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def analyze_last_session():
    """Analyze the last session's API communications."""
    if not os.path.exists(RAW_LOG_FILE):
        return "No API log file found. Run the agent first."
    
    with open(RAW_LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if not lines:
        return "API log is empty."
    
    # Find the last session (from last request with step=1)
    session_start_idx = 0
    for i in range(len(lines) - 1, -1, -1):
        try:
            entry = json.loads(lines[i])
            if entry.get("type") == "request" and entry.get("step") == 1:
                session_start_idx = i
                break
        except:
            pass
    
    session_entries = []
    for line in lines[session_start_idx:]:
        try:
            session_entries.append(json.loads(line))
        except:
            pass
    
    # Analyze
    report = ["=== API COMMUNICATION ANALYSIS ===\n"]
    
    for entry in session_entries:
        if entry.get("type") == "request":
            report.append(f"\n--- REQUEST (Step {entry.get('step')}) ---")
            payload = entry.get("payload", {})
            report.append(f"Model: {payload.get('model')}")
            report.append(f"Temperature: {payload.get('temperature')}")
            report.append(f"Top-P: {payload.get('top_p')}")
            report.append(f"Messages: {payload.get('message_count')}")
            
            # Show last few messages
            messages = payload.get("messages", [])[-3:]
            for msg in messages:
                role = msg.get("role")
                content = str(msg.get("content", ""))[:200]
                has_tools = "tool_calls" in msg
                report.append(f"  [{role}] {content}{'...' if len(str(msg.get('content',''))) > 200 else ''} {'(has tool_calls)' if has_tools else ''}")
        
        elif entry.get("type") == "response":
            report.append(f"\n--- RESPONSE (Step {entry.get('step')}) ---")
            report.append(f"Type: {entry.get('response_type')}")
            content = entry.get("content", "")[:500]
            report.append(f"Content ({entry.get('content_length')} chars): {content}{'...' if entry.get('content_length', 0) > 500 else ''}")
    
    return "\n".join(report)

def clear_log():
    """Clear the API log file."""
    if os.path.exists(RAW_LOG_FILE):
        os.remove(RAW_LOG_FILE)
        return "API log cleared."
    return "No log file to clear."
