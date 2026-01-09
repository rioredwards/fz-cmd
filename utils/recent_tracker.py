#!/usr/bin/env python3
"""
Track recently used commands for fz-cmd.

Maintains a file of recently selected commands to sort by recency.
Most recently used commands appear first.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

DEFAULT_RECENT_FILE = os.path.expanduser("~/.dotfiles/zsh/fz-cmd/cache/recent.json")
MAX_RECENT = 100


def get_recent_file() -> str:
    """Get path to recent commands file."""
    return os.environ.get("FZ_CMD_RECENT_FILE", DEFAULT_RECENT_FILE)


def load_recent() -> List[str]:
    """
    Load recent commands from file.
    
    Returns:
        List of command strings, most recent first
    """
    recent_file = get_recent_file()
    
    if not os.path.exists(recent_file):
        return []
    
    try:
        with open(recent_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("commands", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_recent(commands: List[str]) -> None:
    """
    Save recent commands to file.
    
    Args:
        commands: List of command strings, most recent first
    """
    recent_file = get_recent_file()
    
    # Ensure directory exists
    Path(recent_file).parent.mkdir(parents=True, exist_ok=True)
    
    data = {"commands": commands[:MAX_RECENT]}
    
    try:
        with open(recent_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save recent commands: {e}", file=sys.stderr)


def record_usage(command: str) -> None:
    """
    Record a command as recently used.
    
    Moves command to front of list (most recent).
    Deduplicates and limits to MAX_RECENT entries.
    
    Args:
        command: The command string that was selected
    """
    if not command or not command.strip():
        return
    
    command = command.strip()
    recent = load_recent()
    
    # Remove if already exists (to move to front)
    if command in recent:
        recent.remove(command)
    
    # Prepend (most recent first)
    recent.insert(0, command)
    
    # Limit size
    recent = recent[:MAX_RECENT]
    
    save_recent(recent)


def get_recent_order() -> List[str]:
    """
    Get commands in recent order for sorting.
    
    Returns:
        List of command strings, most recent first
    """
    return load_recent()


def main():
    """CLI interface for recent tracker."""
    if len(sys.argv) < 2:
        print("Usage: recent_tracker.py <command>", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  record <command>  - Record a command as recently used", file=sys.stderr)
        print("  list              - List recent commands (JSON)", file=sys.stderr)
        print("  clear             - Clear recent commands", file=sys.stderr)
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "record":
        if len(sys.argv) < 3:
            # Read from stdin if no command provided
            command = sys.stdin.read().strip()
        else:
            command = " ".join(sys.argv[2:])
        record_usage(command)
        
    elif action == "list":
        recent = get_recent_order()
        print(json.dumps({"commands": recent}, indent=2))
        
    elif action == "clear":
        save_recent([])
        print("Recent commands cleared.")
        
    else:
        print(f"Unknown command: {action}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

