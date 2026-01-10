#!/usr/bin/env python3
"""
Extract shell aliases and convert to standardized JSON format.

Uses zsh to get aliases and outputs JSON to stdout or specified file.
"""

import json
import sys
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any


def get_aliases() -> List[Dict[str, str]]:
    """
    Get aliases from zsh shell.
    
    Returns:
        List of dictionaries with 'name' and 'value' keys
    """
    try:
        # Get aliases from zsh (interactive mode to load user's .zshrc)
        result = subprocess.run(
            ["zsh", "-i", "-c", "alias"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        aliases = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            
            # Remove "alias " prefix
            line = line.replace("alias ", "", 1).strip()
            
            # Parse: name='value' or name="value" or name=value
            match = re.match(r'^([^=]+)=(.+)$', line)
            if not match:
                continue
            
            name = match.group(1).strip()
            value = match.group(2).strip()
            
            # Remove quotes if present
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]
            
            aliases.append({"name": name, "value": value})
        
        return aliases
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return []


def process_aliases() -> List[Dict[str, Any]]:
    """
    Process aliases into command format.
    
    Returns:
        List of command dictionaries
    """
    raw_aliases = get_aliases()
    
    commands = []
    for alias in raw_aliases:
        name = alias["name"]
        value = alias["value"]
        
        # Skip internal/uninteresting aliases
        if name.startswith("_") or name.startswith("."):
            continue
        
        # Truncate long expansions for description
        desc_value = value if len(value) <= 60 else value[:57] + "..."
        
        cmd = {
            "command": name,  # The alias name (what user types)
            "description": f"→ {desc_value}",
            "tags": ["alias", name],
            "examples": [name],
            "source": "alias",
            "metadata": {"alias_name": name, "expands_to": value}
        }
        commands.append(cmd)
    
    return commands


def main():
    """Main entry point."""
    # Output file (optional)
    output_file = None
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    commands = process_aliases()
    
    output = {"commands": commands}
    json_output = json.dumps(output, indent=2)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()

