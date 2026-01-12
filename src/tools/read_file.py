"""Read file tool"""
from typing import Dict, Tuple
from pathlib import Path

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read and retrieve the full contents of a text file. Maximum file size is 1MB. Works with any text-based file (Python, JSON, TXT, etc). Returns the exact file contents which you can analyze and use in subsequent tool calls.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read (can be relative or absolute path)"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Optional: Start reading from this line number (1-indexed). If omitted, starts from line 1."
                },
                "end_line": {
                    "type": "integer",
                    "description": "Optional: Stop reading at this line number (inclusive, 1-indexed). If omitted, reads to end of file."
                }
            },
            "required": ["file_path"]
        },
    },
}


def execute(args: Dict[str, object]) -> Tuple[str, bool]:
    file_path = str(args.get("file_path", ""))
    start_line = int(args.get("start_line", 1) or 1)
    end_line = args.get("end_line", None)
    end_line = int(end_line) if end_line is not None else None
    
    try:
        path = Path(file_path)
        
        if not path.exists():
            return f"Error: File '{file_path}' does not exist", False
        if not path.is_file():
            return f"Error: '{file_path}' is not a file", False
        
        file_size = path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB
            return f"Error: File '{file_path}' is too large ({file_size} bytes). Max 1MB.", False
        
        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        if start_line < 1:
            start_line = 1
        if end_line is None or end_line > len(lines):
            end_line = len(lines)
        
        requested_lines = lines[start_line - 1:end_line]
        requested_content = '\n'.join(requested_lines)
        
        if start_line == 1 and end_line == len(lines):
            return f"File content of '{file_path}':\n{requested_content}", False
        else:
            return f"File content of '{file_path}' (lines {start_line}-{end_line}):\n{requested_content}", False
    
    except UnicodeDecodeError:
        return f"Error: File '{file_path}' is not a text file (encoding issue)", False
    except Exception as e:
        return f"Error reading file: {str(e)}", False
