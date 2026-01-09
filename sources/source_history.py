#!/usr/bin/env python3
"""
Process shell history and convert to standardized JSON format.

Reads from zsh history and outputs JSON to stdout or specified file.
Filters noise commands and deduplicates.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from collections import OrderedDict

# Commands to filter out (noise)
NOISE_COMMANDS = {
    "ls", "cd", "pwd", "clear", "exit", "history", "..", "...", "....",
    "ll", "la", "l", "cat", "less", "more", "head", "tail"
}


def get_history_entries(max_entries: int = 500) -> List[str]:
    """
    Get shell history entries by reading the history file directly.
    
    Handles multiline commands properly by joining continuation lines.
    
    Args:
        max_entries: Maximum number of entries to retrieve
        
    Returns:
        List of history command strings (most recent first)
    """
    # Find history file
    histfile = os.environ.get("HISTFILE", os.path.expanduser("~/.zsh_history"))
    
    if not os.path.exists(histfile):
        return []
    
    try:
        # Read history file with error handling for encoding issues
        with open(histfile, "rb") as f:
            content = f.read()
        
        # Try UTF-8 first, fall back to latin-1
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")
        
        lines = text.split("\n")
        commands = []
        
        # Extended history format: ": timestamp:0;command"
        # Multiline commands have the timestamp on first line, then continuation lines
        extended_pattern = re.compile(r"^: (\d+):(\d+);(.*)$")
        
        current_cmd = None
        
        for line in lines:
            # Don't strip - we need to detect continuation properly
            if not line:
                continue
            
            # Check for extended history format (start of new command)
            match = extended_pattern.match(line)
            if match:
                # Save previous command if any
                if current_cmd is not None:
                    cleaned = _clean_command(current_cmd)
                    if cleaned:
                        commands.append(cleaned)
                # Start new command
                current_cmd = match.group(3)
            elif current_cmd is not None:
                # This is a continuation line of a multiline command
                # Join with the previous line
                current_cmd += "\n" + line
            else:
                # Plain format (no extended history) or orphan line
                if not line.startswith(":"):
                    cleaned = _clean_command(line)
                    if cleaned:
                        commands.append(cleaned)
        
        # Don't forget the last command
        if current_cmd is not None:
            cleaned = _clean_command(current_cmd)
            if cleaned:
                commands.append(cleaned)
        
        # Return most recent entries (last N from file)
        return commands[-max_entries:]
        
    except (OSError, IOError):
        return []


def _clean_command(cmd: str) -> Optional[str]:
    """
    Clean and validate a command string.
    
    - Joins multiline commands with semicolons for single-line display
    - Filters out fragments and noise
    
    Args:
        cmd: Raw command string (may contain newlines)
        
    Returns:
        Cleaned command string, or None if invalid/noise
    """
    if not cmd:
        return None
    
    # Join multiline commands with semicolons for display
    # But preserve the original if it's a meaningful multiline command
    lines = [l.strip() for l in cmd.strip().split("\n") if l.strip()]
    
    if not lines:
        return None
    
    # If it's a single line that's just a backslash or fragment, skip it
    if len(lines) == 1:
        line = lines[0]
        # Skip bare backslashes, single characters, or obvious fragments
        if line in ("\\", "") or (len(line) <= 2 and not line.isalnum()):
            return None
        # Skip lines that are just flags without a command
        if line.startswith("--") and " " not in line:
            return None
        return line
    
    # For multiline commands, join with semicolons
    # This creates a valid single-line representation
    joined = "; ".join(lines)
    
    # But if it's too long or unwieldy, just use the first meaningful line
    if len(joined) > 200:
        return lines[0]
    
    return joined


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

