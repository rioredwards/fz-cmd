#!/usr/bin/env python3
"""
Format JSON commands for fzf display.

Outputs tab-separated format:
<display>\t<command>\t<description>\t<tags>\t<examples>

Field 1: command + padding + invisible searchable text (description/tags)
         The padding pushes searchable text behind the preview window
Field 2: Raw command for extraction after selection
Fields 3-5: Raw data for preview script

Use with: fzf --ansi --delimiter='\\t' --with-nth=1 --preview-window=right:60%
"""

import json
import sys
from typing import List, Dict, Any, Optional

# ANSI color codes
DIM = "\033[38;2;29;32;33m"  # RGB(29,32,33) = #1D2021 - matches fzf bg
RESET = "\033[0m"


def format_command(cmd: Dict[str, Any]) -> str:
    """
    Format a single command for fzf display.
    
    Args:
        cmd: Command dictionary with command, description, tags, examples
        
    Returns:
        Tab-separated: <display>\\t<command>\\t<description>\\t<tags>\\t<examples>
        
    Display format: command + huge padding + invisible searchable text
    The padding pushes searchable text behind the preview window.
    """
    command = cmd.get("command", "").strip()
    description = cmd.get("description", "").strip()
    tags = cmd.get("tags", [])
    examples = cmd.get("examples", [])
    
    tags_str = ", ".join(tags) if tags else ""
    examples_str = " | ".join(examples) if examples else ""
    
    # Build searchable suffix (invisible but contributes to search)
    search_parts = []
    if description:
        search_parts.append(description)
    if tags_str:
        search_parts.append(tags_str)
    
    search_text = " ".join(search_parts)
    
    # Huge padding pushes invisible text behind preview window
    PADDING = " " * 300
    
    # Field 1: command (visible) + padding + invisible searchable text
    if search_text:
        display = f"{command}{PADDING}{DIM}{search_text}{RESET}"
    else:
        display = command
    
    # All 5 fields for compatibility with preview script
    return f"{display}\t{command}\t{description}\t{tags_str}\t{examples_str}"


def format_commands(commands: List[Dict[str, Any]], sort_by_recent: Optional[List[str]] = None) -> List[str]:
    """
    Format multiple commands for fzf.
    
    Args:
        commands: List of command dictionaries
        sort_by_recent: Optional list of command strings in recent order
        
    Returns:
        List of formatted tab-separated strings
    """
    # Create a map for recent ordering
    recent_map = {}
    if sort_by_recent:
        for idx, cmd_str in enumerate(sort_by_recent):
            recent_map[cmd_str] = idx
    
    # Sort commands: recent first, then alphabetically
    def sort_key(cmd: Dict[str, Any]) -> tuple:
        cmd_str = cmd.get("command", "")
        recent_idx = recent_map.get(cmd_str, 999999)
        return (recent_idx, cmd_str.lower())
    
    sorted_commands = sorted(commands, key=sort_key)
    
    # Format each command
    return [format_command(cmd) for cmd in sorted_commands]


def main():
    """Main entry point."""
    # Read JSON from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    commands = data.get("commands", [])
    
    # Optional: read recent commands from second argument
    recent_commands = None
    if len(sys.argv) > 2:
        try:
            with open(sys.argv[2], "r", encoding="utf-8") as f:
                recent_data = json.load(f)
                raw_commands = recent_data.get("commands", [])
                # Handle both formats: list of strings or list of dicts
                if raw_commands:
                    if isinstance(raw_commands[0], str):
                        recent_commands = raw_commands
                    elif isinstance(raw_commands[0], dict):
                        recent_commands = [c.get("command", "") for c in raw_commands]
        except (json.JSONDecodeError, IOError, KeyError, IndexError, TypeError):
            # If anything goes wrong with recent file, just skip sorting by recent
            recent_commands = None
    
    formatted = format_commands(commands, recent_commands)
    
    # Output formatted lines
    for line in formatted:
        print(line)
    
    # Write sample to file for debugging (DELETE LATER)
    with open("/Users/rioredwards/.dotfiles/zsh/fz-cmd/formatted_sample.txt", "w") as f:
        f.write("# Formatted output sample - tab-separated:\n")
        f.write("# <ansi_display>\\t<command>\\t<description>\\t<tags>\\t<examples>\n\n")
        for line in formatted[:50]:  # First 50 entries
            f.write(line + "\n")


if __name__ == "__main__":
    main()
