"""Install package - allows the agent to install Python dependencies"""
import subprocess
import sys
from typing import Dict, Any, Tuple
from pathlib import Path

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "install_package",
        "description": "Install a Python package using pip in the current virtual environment. Use this when you encounter 'ModuleNotFoundError' or 'ImportError'. After installation, the package will be immediately available for use in tools.",
        "parameters": {
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "The package name to install (e.g., 'requests', 'numpy', 'pandas')"
                },
                "version": {
                    "type": "string",
                    "description": "Optional: specific version to install (e.g., '2.28.0'). Leave empty for latest."
                }
            },
            "required": ["package"]
        }
    }
}


def execute(args: Dict[str, Any]) -> Tuple[str, bool]:
    """Install a Python package via pip"""
    package = str(args.get("package", "")).strip()
    version = str(args.get("version", "")).strip()
    
    if not package:
        return "Error: Package name is required", False
    
    # Build pip install command
    if version:
        package_spec = f"{package}=={version}"
    else:
        package_spec = package
    
    try:
        # Install the package
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_spec],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Update requirements.txt if it exists
            req_file = Path("requirements.txt")
            if req_file.exists():
                try:
                    # Get installed version
                    check_result = subprocess.run(
                        [sys.executable, "-m", "pip", "show", package],
                        capture_output=True,
                        text=True
                    )
                    
                    installed_version = None
                    for line in check_result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            installed_version = line.split(':', 1)[1].strip()
                            break
                    
                    if installed_version:
                        # Check if package already in requirements
                        requirements = req_file.read_text()
                        lines = requirements.split('\n')
                        package_found = False
                        
                        for i, line in enumerate(lines):
                            if line.startswith(package + '==') or line == package:
                                lines[i] = f"{package}=={installed_version}"
                                package_found = True
                                break
                        
                        if not package_found:
                            # Add new package
                            if lines and lines[-1].strip():
                                lines.append(f"{package}=={installed_version}")
                            else:
                                lines[-1] = f"{package}=={installed_version}"
                        
                        req_file.write_text('\n'.join(lines))
                        
                        return f"Successfully installed {package}=={installed_version} and updated requirements.txt", False
                except Exception as e:
                    # Installation succeeded but requirements update failed - not critical
                    pass
            
            return f"Successfully installed {package_spec}. Package is now available for import.", False
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return f"Failed to install {package_spec}: {error_msg}", False
    
    except subprocess.TimeoutExpired:
        return f"Installation of {package_spec} timed out (exceeded 120 seconds)", False
    except Exception as e:
        return f"Error installing package: {type(e).__name__}: {str(e)}", False
