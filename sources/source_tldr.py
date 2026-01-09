#!/usr/bin/env python3
"""
Parse tldr cache YAML and convert to standardized JSON format.

Reads from tldr-commands.yaml and outputs JSON to stdout or specified file.
"""

import json
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any


def parse_tldr_yaml(yaml_file: str) -> List[Dict[str, Any]]:
    """
    Parse tldr-commands.yaml and convert to command format.
    
    Args:
        yaml_file: Path to tldr-commands.yaml
        
    Returns:
        List of command dictionaries
    """
    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return []
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        return []
    
    if not data or not isinstance(data, dict):
        return []
    
    commands = []
    
    # tldr-commands.yaml structure: list of command entries
    # Each entry has: command, description, tags, examples
    for entry in data.get("commands", []):
        if not isinstance(entry, dict):
            continue
        
        command_str = entry.get("command", "").strip()
        if not command_str:
            continue
        
        cmd = {
            "command": command_str,
            "description": entry.get("description", "").strip(),
            "tags": entry.get("tags", []),
            "examples": [ex.get("command", "") if isinstance(ex, dict) else str(ex) 
                       for ex in entry.get("examples", [])],
            "source": "tldr",
            "metadata": {}
        }
        
        commands.append(cmd)
    
    return commands


def main():
    """Main entry point."""
    # Default tldr cache location
    default_tldr_file = Path.home() / ".dotfiles" / "zsh" / "fz-cmd" / "tldr-commands.yaml"
    
    if len(sys.argv) > 1:
        tldr_file = sys.argv[1]
    else:
        tldr_file = str(default_tldr_file)
    
    # Output file (optional)
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    commands = parse_tldr_yaml(tldr_file)
    
    output = {"commands": commands}
    json_output = json.dumps(output, indent=2)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()

