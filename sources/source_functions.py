#!/usr/bin/env python3
"""
Extract shell functions and convert to standardized JSON format.

Uses zsh to get functions and outputs JSON to stdout or specified file.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def get_functions() -> List[str]:
    """
    Get function names from zsh shell.
    
    Returns:
        List of function names
    """
    try:
        # Get function names using zsh's functions associative array
        # Use -i for interactive mode to load user's .zshrc
        result = subprocess.run(
            ["zsh", "-i", "-c", "print -l ${(k)functions}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        functions = []
        for line in result.stdout.strip().split("\n"):
            func_name = line.strip()
            if func_name and not func_name.startswith("_"):  # Filter internal functions
                # Additional filter: only valid function name patterns
                if func_name.replace("_", "").replace("-", "").isalnum():
                    functions.append(func_name)
        
        return functions
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return []


def process_functions() -> List[Dict[str, Any]]:
    """
    Process functions into command format.
    
    Returns:
        List of command dictionaries
    """
    function_names = get_functions()
    
    commands = []
    for func_name in function_names:
        cmd = {
            "command": func_name,  # Function name is the command
            "description": f"Function: {func_name}",
            "tags": ["function", func_name],
            "examples": [func_name],
            "source": "function",
            "metadata": {"function_name": func_name}
        }
        commands.append(cmd)
    
    return commands


def main():
    """Main entry point."""
    # Output file (optional)
    output_file = None
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    commands = process_functions()
    
    output = {"commands": commands}
    json_output = json.dumps(output, indent=2)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()

