#!/usr/bin/env python3
"""
Merge multiple JSON command files and deduplicate commands.

Source priority: curated > alias > function > history > tldr
When duplicates are found, the command from the higher priority source is kept.
"""

import json
import sys
from typing import Dict, List, Any

# Source priority (higher number = higher priority)
SOURCE_PRIORITY = {
    "curated": 5,
    "alias": 4,
    "function": 3,
    "history": 2,
    "tldr": 1,
}


def load_commands(filepath: str) -> List[Dict[str, Any]]:
    """Load commands from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("commands", [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)
        return []


def merge_commands(files: List[str]) -> List[Dict[str, Any]]:
    """
    Merge commands from multiple JSON files, deduplicating by command string.
    
    Args:
        files: List of JSON file paths to merge
        
    Returns:
        List of merged commands, deduplicated with priority preserved
    """
    seen_commands: Dict[str, Dict[str, Any]] = {}
    
    # Process files in order (first file has highest priority if same source)
    for filepath in files:
        commands = load_commands(filepath)
        
        for cmd in commands:
            command_str = cmd.get("command", "").strip()
            if not command_str:
                continue
            
            source = cmd.get("source", "unknown")
            priority = SOURCE_PRIORITY.get(source, 0)
            
            # Check if we've seen this command before
            if command_str in seen_commands:
                existing = seen_commands[command_str]
                existing_source = existing.get("source", "unknown")
                existing_priority = SOURCE_PRIORITY.get(existing_source, 0)
                
                # Keep the command with higher priority
                if priority > existing_priority:
                    seen_commands[command_str] = cmd
            else:
                # New command, add it
                seen_commands[command_str] = cmd
    
    # Return as list
    return list(seen_commands.values())


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: merge_commands.py <file1.json> [file2.json ...]", file=sys.stderr)
        sys.exit(1)
    
    files = sys.argv[1:]
    merged = merge_commands(files)
    
    # Output as JSON
    output = {"commands": merged}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

