"""Write file tool with multiple modes"""
from typing import Dict, Tuple
from pathlib import Path

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write, append, or modify a file efficiently. Supports: write (overwrite), append (end), prepend (start), insert_after_line (after N), replace_lines (replace N lines). Automatically creates file and parent dirs. Cannot write to system directories.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path where the file should be written"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write, append, prepend, insert, or use for replacement"
                },
                "mode": {
                    "type": "string",
                    "enum": ["write", "append", "prepend", "insert_after_line", "replace_lines"],
                    "description": "Mode of operation"
                },
                "line_number": {
                    "type": "integer",
                    "description": "For insert_after_line: line after which to insert. For replace_lines: starting line number."
                },
                "num_lines": {
                    "type": "integer",
                    "description": "For replace_lines: how many lines to replace (starting from line_number)"
                }
            },
            "required": ["file_path", "content", "mode"]
        },
    },
}


def execute(args: Dict[str, object]) -> Tuple[str, bool]:
    file_path = str(args.get("file_path", ""))
    content = str(args.get("content", ""))
    mode = str(args.get("mode", "write"))
    line_number = int(args.get("line_number", 1) or 1)
    num_lines = int(args.get("num_lines", 1) or 1)
    
    try:
        path = Path(file_path)
        
        # Check for "fixed_*" style naming that suggests avoiding fixing the original file
        stem = path.stem.lower()
        bad_prefixes = ('fixed_', 'fix_', 'new_', 'improved_', 'better_', 'working_', 'correct_', 'updated_')
        bad_suffixes = ('_fixed', '_fix', '_new', '_improved', '_better', '_working', '_correct', '_updated', '_v2', '_v3', '_v4', '_final', '_2', '_3')
        
        warning = ""
        original_name = None
        
        for prefix in bad_prefixes:
            if stem.startswith(prefix):
                original_name = stem[len(prefix):]
                break
        
        if not original_name:
            for suffix in bad_suffixes:
                if stem.endswith(suffix):
                    original_name = stem[:-len(suffix)]
                    break
        
        if original_name and mode == "write":
            original_path = path.parent / f"{original_name}{path.suffix}"
            warning = (
                f"\n⚠️ WARNING: Filename '{path.name}' looks like a 'fixed' version of '{original_name}{path.suffix}'.\n"
                f"If '{original_path}' has errors, you should FIX IT directly instead of creating variants.\n"
                f"Use: write_file('{original_path}', fixed_content)\n"
            )
        
        abs_path = path.resolve()
        dangerous_dirs = [Path("/etc"), Path("/sys"), Path("/proc"), Path("C:\\Windows")]
        for danger in dangerous_dirs:
            try:
                if danger in abs_path.parents:
                    return f"Error: Cannot write to system directory '{file_path}'", False
            except Exception:
                pass
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if mode == "write":
            path.write_text(content, encoding='utf-8')
            return f"Successfully wrote {len(content)} characters to '{file_path}'{warning}", False
        
        if mode == "append":
            current = path.read_text(encoding='utf-8') if path.exists() else ""
            if current and not current.endswith('\n'):
                current += '\n'
            new_content = current + content
            path.write_text(new_content, encoding='utf-8')
            return f"Successfully appended {len(content)} characters to '{file_path}'{warning}", False
        
        if mode == "prepend":
            current = path.read_text(encoding='utf-8') if path.exists() else ""
            if content and not content.endswith('\n'):
                content += '\n'
            new_content = content + current
            path.write_text(new_content, encoding='utf-8')
            return f"Successfully prepended {len(content)} characters to '{file_path}'{warning}", False
        
        if mode == "insert_after_line":
            if not path.exists():
                return f"Error: File '{file_path}' does not exist for insert_after_line mode", False
            lines = path.read_text(encoding='utf-8').split('\n')
            if line_number < 0 or line_number > len(lines):
                return f"Error: Line number {line_number} out of range (file has {len(lines)} lines)", False
            content_lines = content.split('\n')
            lines = lines[:line_number] + content_lines + lines[line_number:]
            path.write_text('\n'.join(lines), encoding='utf-8')
            return f"Successfully inserted {len(content_lines)} line(s) after line {line_number} in '{file_path}'{warning}", False
        
        if mode == "replace_lines":
            if not path.exists():
                return f"Error: File '{file_path}' does not exist for replace_lines mode", False
            lines = path.read_text(encoding='utf-8').split('\n')
            if line_number < 1 or line_number > len(lines):
                return f"Error: Start line {line_number} out of range (file has {len(lines)} lines)", False
            end_line = min(line_number + num_lines - 1, len(lines))
            content_lines = content.split('\n')
            lines = lines[:line_number - 1] + content_lines + lines[end_line:]
            path.write_text('\n'.join(lines), encoding='utf-8')
            return f"Successfully replaced {num_lines} line(s) starting at line {line_number} in '{file_path}'{warning}", False
        
        return f"Error: Unknown write mode '{mode}'", False
    
    except Exception as e:
        return f"Error writing file: {str(e)}", False
