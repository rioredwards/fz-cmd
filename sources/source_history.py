#!/usr/bin/env python3
"""
Process shell history and convert to standardized JSON format.

Reads from zsh history and outputs JSON to stdout or specified file.
Filters noise commands and deduplicates.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import OrderedDict

# Commands to filter out (noise)
NOISE_COMMANDS = {
    "ls", "cd", "pwd", "clear", "exit", "history", "..", "...", "....",
    "ll", "la", "l", "cat", "less", "more", "head", "tail"
}


def get_history_entries(max_entries: int = 500) -> List[str]:
    """
    Get shell history entries using zsh history command.
    
    Args:
        max_entries: Maximum number of entries to retrieve
        
    Returns:
        List of history command strings
    """
    try:
        # Use zsh history command
        result = subprocess.run(
            ["zsh", "-c", f"history {max_entries}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        lines = result.stdout.strip().split("\n")
        commands = []
        
        for line in lines:
            # Remove line numbers and timestamps
            # Format: "  123  command" or "123  command"
            parts = line.strip().split(None, 1)
            if len(parts) >= 2:
                cmd = parts[1].strip()
                if cmd:
                    commands.append(cmd)
        
        return commands
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return []


def filter_noise(commands: List[str]) -> List[str]:
    """Filter out noise commands."""
    filtered = []
    for cmd in commands:
        # Get first word (command name)
        first_word = cmd.split()[0] if cmd.split() else ""
        if first_word and first_word not in NOISE_COMMANDS:
            filtered.append(cmd)
    return filtered


def deduplicate(commands: List[str]) -> List[str]:
    """Deduplicate commands while preserving order."""
    seen: Set[str] = set()
    unique = []
    for cmd in commands:
        if cmd not in seen:
            seen.add(cmd)
            unique.append(cmd)
    return unique


def process_history(max_entries: int = 500) -> List[Dict[str, Any]]:
    """
    Process shell history into command format.
    
    Args:
        max_entries: Maximum number of history entries to process
        
    Returns:
        List of command dictionaries
    """
    raw_commands = get_history_entries(max_entries)
    filtered = filter_noise(raw_commands)
    unique = deduplicate(filtered)
    
    commands = []
    for cmd_str in unique:
        cmd = {
            "command": cmd_str,
            "description": f"History: {cmd_str[:50]}",  # Simple description
            "tags": [],
            "examples": [cmd_str],
            "source": "history",
            "metadata": {}
        }
        commands.append(cmd)
    
    return commands


def main():
    """Main entry point."""
    max_entries = 500
    if len(sys.argv) > 1:
        try:
            max_entries = int(sys.argv[1])
        except ValueError:
            print(f"Invalid max_entries: {sys.argv[1]}", file=sys.stderr)
            sys.exit(1)
    
    # Output file (optional)
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    commands = process_history(max_entries)
    
    output = {"commands": commands}
    json_output = json.dumps(output, indent=2)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()

