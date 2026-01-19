"""Run command tool with timeout, server detection, and background process support"""
import subprocess
import threading
import time
import os
import signal
from typing import Dict, Tuple, Any, Optional
from pathlib import Path

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "run_command",
        "description": (
            "Execute a shell command with timeout protection. "
            "For long-running servers, use background=true. "
            "If a command times out, try breaking it into smaller parts or use a different approach."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30, max: 300)"
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for the command"
                },
                "background": {
                    "type": "boolean",
                    "description": "Run as background process (for servers). Returns immediately with PID."
                }
            },
            "required": ["command"]
        }
    }
}

# Track background processes
_background_processes: Dict[int, subprocess.Popen] = {}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Execute a shell command with timeout and server detection."""
    command = str(args.get("command", "")).strip()
    timeout = min(int(args.get("timeout", 30)), 300)  # Cap at 5 minutes
    cwd = str(args.get("cwd", ".")) if args.get("cwd") else "."
    background = bool(args.get("background", False))
    
    if not command:
        return "Error: command is required", False
    
    # Validate working directory
    cwd_path = Path(cwd)
    if not cwd_path.exists():
        return f"Error: Working directory '{cwd}' does not exist", False
    
    # Detect potentially long-running commands (servers, watches, etc.)
    server_indicators = [
        'flask run', 'python -m http.server', 'npm start', 'npm run dev',
        'node server', 'uvicorn', 'gunicorn', 'django', 'runserver',
        'watch', 'nodemon', 'live-server', 'serve', 'http-server'
    ]
    
    is_likely_server = any(ind in command.lower() for ind in server_indicators)
    
    if is_likely_server and not background:
        return (
            f"⚠️ POTENTIAL SERVER DETECTED: '{command}' looks like a long-running server.\n"
            f"This command may run forever and block the agent.\n\n"
            f"Options:\n"
            f"1. Run with background=true to start in background: "
            f"run_command(command='{command}', background=true)\n"
            f"2. If you just want to test, add a timeout\n"
            f"3. Consider if you really need to start a server"
        ), False
    
    # Background process handling
    if background:
        try:
            # Start process without waiting
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                start_new_session=True  # Detach from parent
            )
            
            pid = process.pid
            _background_processes[pid] = process
            
            # Give it a moment to see if it fails immediately
            time.sleep(0.5)
            
            if process.poll() is not None:
                # Process already exited
                stdout, stderr = process.communicate()
                return (
                    f"Background process exited immediately (code: {process.returncode})\n"
                    f"STDOUT: {stdout.decode('utf-8', errors='replace')[:500]}\n"
                    f"STDERR: {stderr.decode('utf-8', errors='replace')[:500]}"
                ), False
            
            return (
                f"✓ Background process started (PID: {pid})\n"
                f"Command: {command}\n"
                f"Use stop_background(pid={pid}) to stop it later."
            ), False
            
        except Exception as e:
            return f"Error starting background process: {str(e)}", False
    
    # Regular foreground execution with timeout
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            
            result_parts = [f"Command: {command}", f"Exit code: {process.returncode}"]
            
            if stdout:
                # Truncate very long output
                stdout_display = stdout[:5000] + "\n... (truncated)" if len(stdout) > 5000 else stdout
                result_parts.append(f"\n--- STDOUT ---\n{stdout_display}")
            
            if stderr:
                stderr_display = stderr[:2000] + "\n... (truncated)" if len(stderr) > 2000 else stderr
                result_parts.append(f"\n--- STDERR ---\n{stderr_display}")
            
            return "\n".join(result_parts), False
            
        except subprocess.TimeoutExpired:
            # Kill the process
            process.kill()
            try:
                process.wait(timeout=2)
            except:
                pass
            
            return (
                f"⏱️ TIMEOUT: Command exceeded {timeout} seconds and was terminated.\n"
                f"Command: {command}\n\n"
                f"SUGGESTIONS:\n"
                f"1. Break this task into smaller parts (divide and conquer)\n"
                f"2. If this is a server, use background=true\n"
                f"3. Increase timeout if the task genuinely needs more time\n"
                f"4. Try a more efficient approach or algorithm"
            ), False
            
    except Exception as e:
        return f"Error executing command: {str(e)}", False


def stop_background_process(pid: int) -> str:
    """Stop a background process by PID."""
    if pid in _background_processes:
        process = _background_processes[pid]
        try:
            process.terminate()
            process.wait(timeout=5)
            del _background_processes[pid]
            return f"✓ Process {pid} terminated"
        except:
            process.kill()
            del _background_processes[pid]
            return f"✓ Process {pid} killed (force)"
    return f"Process {pid} not found in tracked processes"


def list_background_processes() -> str:
    """List all tracked background processes."""
    if not _background_processes:
        return "No background processes running"
    
    lines = ["Background processes:"]
    for pid, proc in _background_processes.items():
        status = "running" if proc.poll() is None else f"exited ({proc.returncode})"
        lines.append(f"  PID {pid}: {status}")
    return "\n".join(lines)
