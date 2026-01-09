#!/usr/bin/env python3
"""
Parse commands.yaml and convert to standardized JSON format.

Reads from commands.yaml and outputs JSON to stdout or specified file.
"""

import json
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any


def parse_commands_yaml(yaml_file: str) -> List[Dict[str, Any]]:
    """
    Parse commands.yaml and convert to command format.
    
    Args:
        yaml_file: Path to commands.yaml
        
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
    
    # commands.yaml structure: commands is a list
    for entry in data.get("commands", []):
        if not isinstance(entry, dict):
            continue
        
        command_str = entry.get("command", "").strip()
        if not command_str:
            continue
        
        # Extract examples (can be list of strings or list of dicts with command field)
        examples = []
        for ex in entry.get("examples", []):
            if isinstance(ex, dict):
                examples.append(ex.get("command", ""))
            else:
                examples.append(str(ex))
        
        cmd = {
            "command": command_str,
            "description": entry.get("description", "").strip(),
            "tags": entry.get("tags", []),
            "examples": examples,
            "source": "curated",
            "metadata": {}
        }
        
        commands.append(cmd)
    
    return commands


def main():
    """Main entry point."""
    # Default commands.yaml location
    default_yaml_file = Path.home() / ".dotfiles" / "commands.yaml"
    
    if len(sys.argv) > 1:
        yaml_file = sys.argv[1]
    else:
        yaml_file = str(default_yaml_file)
    
    # Output file (optional)
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    commands = parse_commands_yaml(yaml_file)
    
    output = {"commands": commands}
    json_output = json.dumps(output, indent=2)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()

