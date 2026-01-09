#!/usr/bin/env python3
"""
Limit number of commands from each source (for fast startup during development).

Takes a JSON file and limits commands per source, preserving source priority.
"""

import json
import sys
from typing import Dict, List, Any
from collections import defaultdict

# Source priority (higher number = higher priority)
SOURCE_PRIORITY = {
    "curated": 5,
    "alias": 4,
    "function": 3,
    "history": 2,
    "tldr": 1,
}


def limit_commands(commands: List[Dict[str, Any]], limits: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Limit commands per source while preserving source priority.
    
    Args:
        commands: List of command dictionaries
        limits: Dictionary mapping source names to max counts (e.g., {"curated": 100, "history": 50})
        
    Returns:
        Limited list of commands, sorted by priority
    """
    # Group commands by source
    by_source: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for cmd in commands:
        source = cmd.get("source", "unknown")
        by_source[source].append(cmd)
    
    # Apply limits and collect results
    result = []
    for source in sorted(by_source.keys(), key=lambda s: SOURCE_PRIORITY.get(s, 0), reverse=True):
        source_commands = by_source[source]
        limit = limits.get(source, len(source_commands))  # No limit if not specified
        
        # Take up to limit, preserving order
        limited = source_commands[:limit]
        result.extend(limited)
    
    return result


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: limit_commands.py <input.json> [--limit source:count ...]", file=sys.stderr)
        print("Example: limit_commands.py commands.json --limit curated:100 --limit history:50", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Parse limits from arguments
    limits = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
            limit_arg = sys.argv[i + 1]
            if ":" in limit_arg:
                source, count = limit_arg.split(":", 1)
                try:
                    limits[source] = int(count)
                except ValueError:
                    print(f"Invalid limit count: {count}", file=sys.stderr)
            i += 2
        else:
            i += 1
    
    # Load commands
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            commands = data.get("commands", [])
    except FileNotFoundError:
        print(f"File not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Apply limits
    limited = limit_commands(commands, limits)
    
    # Output as JSON
    output = {"commands": limited}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

