#!/usr/bin/env python3
"""
Format JSON commands for fzf display.

Outputs tab-separated format suitable for fzf:
<formatted_display>\t<command>\t<description>\t<tags>\t<examples>

The formatted_display is a fixed-width table-like string for visual alignment.
The remaining fields contain the original data for preview/extraction.
"""

import json
import sys
from typing import List, Dict, Any, Optional

# Column widths for table-like display
CMD_WIDTH = 35
DESC_WIDTH = 50
TAGS_WIDTH = 40


def truncate_pad(text: str, width: int) -> str:
    """Truncate or pad text to exact width."""
    if len(text) > width:
        return text[:width - 3] + "..."
    return text.ljust(width)


def format_command(cmd: Dict[str, Any]) -> str:
    """
    Format a single command for fzf display.
    
    Args:
        cmd: Command dictionary with command, description, tags, examples
        
    Returns:
        Tab-separated string for fzf:
        formatted_display\tcommand\tdescription\ttags\texamples
    """
    command = cmd.get("command", "").strip()
    description = cmd.get("description", "").strip()
    tags = cmd.get("tags", [])
    examples = cmd.get("examples", [])
    
    # Build formatted display (what user sees in fzf list)
    formatted_cmd = truncate_pad(command, CMD_WIDTH)
    formatted_desc = truncate_pad(description, DESC_WIDTH)
    
    # Format tags as bracketed keywords for display
    tag_display = " ".join(f"[{t}]" for t in tags[:4]) if tags else ""
    formatted_tags = truncate_pad(tag_display, TAGS_WIDTH)
    
    # Combine into formatted display (visible in fzf)
    formatted_display = f"{formatted_cmd}  {formatted_desc}  {formatted_tags}"
    
    # Format tags and examples as strings for data fields
    tags_str = ", ".join(tags) if tags else ""
    examples_str = " | ".join(examples) if examples else ""
    
    # Tab-separated: formatted_display \t command \t description \t tags \t examples
    return f"{formatted_display}\t{command}\t{description}\t{tags_str}\t{examples_str}"


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
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            recent_data = json.load(f)
            recent_commands = [c.get("command", "") for c in recent_data.get("commands", [])]
    
    formatted = format_commands(commands, recent_commands)
    
    # Output formatted lines
    for line in formatted:
        print(line)


if __name__ == "__main__":
    main()
