#!/usr/bin/env python3
"""
AI-powered history analyzer for fz-cmd.

Analyzes shell history to find frequently used commands that aren't
in commands.yaml, and optionally uses AI to generate descriptions and tags.

Usage:
    python3 analyze_history.py [options]
    
Options:
    --dry-run       Show suggestions without modifying commands.yaml
    --limit N       Analyze only the N most recent history entries (default: 1000)
    --min-freq N    Minimum frequency to consider (default: 3)
    --no-ai         Skip AI enhancement, just show raw suggestions
    --output FILE   Write YAML suggestions to file instead of stdout
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
sys.path.insert(0, str(Path(__file__).parent.parent / "sources"))

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Noise commands to filter out
NOISE_COMMANDS = {
    "ls", "cd", "pwd", "clear", "exit", "history", "fc", "echo", "cat",
    "less", "more", "head", "tail", "grep", "find", "which", "where",
    "type", "command", "help", "man", "info", "apropos", "whatis",
    "..", "...", "....", "ll", "la", "l", "z", "zz"
}


def get_history_commands(limit: int = 1000) -> List[str]:
    """
    Get commands from shell history file.
    
    Args:
        limit: Maximum number of entries to read
        
    Returns:
        List of command strings
    """
    histfile = os.environ.get("HISTFILE", os.path.expanduser("~/.zsh_history"))
    
    if not os.path.exists(histfile):
        print(f"Error: History file not found: {histfile}", file=sys.stderr)
        return []
    
    try:
        with open(histfile, "rb") as f:
            content = f.read()
        
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")
        
        lines = text.strip().split("\n")
        commands = []
        
        # Extended history format: ": timestamp:0;command"
        extended_pattern = re.compile(r"^: \d+:\d+;(.*)$")
        
        for line in lines[-limit:]:
            match = extended_pattern.match(line)
            if match:
                cmd = match.group(1).strip()
                if cmd:
                    commands.append(cmd)
            elif not line.startswith(":") and line.strip():
                commands.append(line.strip())
        
        return commands
        
    except (OSError, IOError) as e:
        print(f"Error reading history: {e}", file=sys.stderr)
        return []


def get_existing_commands(commands_file: str) -> Set[str]:
    """
    Get existing commands from commands.yaml.
    
    Args:
        commands_file: Path to commands.yaml
        
    Returns:
        Set of existing command strings
    """
    if not os.path.exists(commands_file):
        return set()
    
    if not HAS_YAML:
        print("Warning: PyYAML not installed, can't check existing commands", file=sys.stderr)
        return set()
    
    try:
        with open(commands_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        existing = set()
        for cmd in data.get("commands", []):
            if "command" in cmd:
                existing.add(cmd["command"])
        
        return existing
        
    except Exception as e:
        print(f"Warning: Could not parse {commands_file}: {e}", file=sys.stderr)
        return set()


def filter_noise(cmd: str) -> bool:
    """
    Check if a command should be filtered out.
    
    Args:
        cmd: Command string
        
    Returns:
        True if command should be kept, False if noise
    """
    if len(cmd) < 3:
        return False
    
    # Filter out multiline fragments (lines ending with backslash)
    if cmd.endswith("\\"):
        return False
    
    # Filter out lines that look like variable assignments without commands
    if cmd.startswith("local ") or cmd.startswith("export "):
        if "=" in cmd and not ";" in cmd:
            return False
    
    # Filter out lines starting with special chars (likely fragments)
    if cmd[0] in ")}]|&;":
        return False
    
    # Get base command
    base_cmd = cmd.split()[0] if cmd.split() else ""
    
    if base_cmd in NOISE_COMMANDS:
        return False
    
    # Filter out very short or obvious noise
    if base_cmd.startswith(".") and len(base_cmd) <= 4:
        return False
    
    return True


def analyze_history(
    limit: int = 1000,
    min_freq: int = 3,
    commands_file: Optional[str] = None
) -> List[Dict]:
    """
    Analyze history and find frequently used commands.
    
    Args:
        limit: Number of history entries to analyze
        min_freq: Minimum frequency to include
        commands_file: Path to commands.yaml (to filter existing)
        
    Returns:
        List of command suggestions with frequency
    """
    commands = get_history_commands(limit)
    
    # Filter noise
    filtered = [cmd for cmd in commands if filter_noise(cmd)]
    
    # Count frequencies
    freq = Counter(filtered)
    
    # Get existing commands to exclude
    if commands_file:
        existing = get_existing_commands(commands_file)
    else:
        existing = set()
    
    # Build suggestions
    suggestions = []
    for cmd, count in freq.most_common():
        if count < min_freq:
            break
        if cmd in existing:
            continue
        
        base_cmd = cmd.split()[0] if cmd.split() else cmd
        
        suggestions.append({
            "command": cmd,
            "frequency": count,
            "base_command": base_cmd,
        })
    
    return suggestions


def enhance_with_ai(suggestions: List[Dict]) -> List[Dict]:
    """
    Use AI to generate descriptions and tags for suggestions.
    
    Args:
        suggestions: List of command suggestions
        
    Returns:
        Enhanced suggestions with descriptions and tags
    """
    # Check for API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        print("Note: No AI API key found (OPENAI_API_KEY or ANTHROPIC_API_KEY)", file=sys.stderr)
        print("Suggestions will have basic auto-generated descriptions.", file=sys.stderr)
        
        # Generate basic descriptions without AI
        for s in suggestions:
            base = s["base_command"]
            s["description"] = f"Frequently used: {s['command'][:50]}"
            s["tags"] = ["history", base]
        
        return suggestions
    
    # TODO: Implement actual AI enhancement
    # For now, just use basic descriptions
    print("AI enhancement not yet implemented, using basic descriptions.", file=sys.stderr)
    
    for s in suggestions:
        base = s["base_command"]
        s["description"] = f"Frequently used: {s['command'][:50]}"
        s["tags"] = ["history", base]
    
    return suggestions


def format_yaml_output(suggestions: List[Dict]) -> str:
    """
    Format suggestions as YAML for commands.yaml.
    
    Args:
        suggestions: List of command suggestions
        
    Returns:
        YAML-formatted string
    """
    lines = ["# Suggested additions from history analysis", "# Review and edit before adding to commands.yaml", ""]
    
    for s in suggestions:
        lines.append(f"  - command: {s['command']}")
        lines.append(f"    description: \"{s.get('description', '')}\"")
        tags = s.get("tags", [])
        if tags:
            tags_str = ", ".join(tags)
            lines.append(f"    tags: [{tags_str}]")
        lines.append(f"    # frequency: {s['frequency']}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze shell history and suggest commands for commands.yaml"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show suggestions without any file modifications"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Number of history entries to analyze (default: 1000)"
    )
    parser.add_argument(
        "--min-freq",
        type=int,
        default=3,
        help="Minimum frequency to consider (default: 3)"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI enhancement"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write YAML to file instead of stdout"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Show only top N suggestions (default: 20)"
    )
    
    args = parser.parse_args()
    
    # Find commands.yaml
    fz_cmd_dir = Path(__file__).parent.parent
    commands_file = fz_cmd_dir / "tldr-commands.yaml"
    
    print(f"Analyzing last {args.limit} history entries...", file=sys.stderr)
    
    suggestions = analyze_history(
        limit=args.limit,
        min_freq=args.min_freq,
        commands_file=str(commands_file) if commands_file.exists() else None
    )
    
    if not suggestions:
        print("No new command suggestions found.", file=sys.stderr)
        return
    
    print(f"Found {len(suggestions)} potential commands (min frequency: {args.min_freq})", file=sys.stderr)
    
    # Limit to top N
    suggestions = suggestions[:args.top]
    
    # Enhance with AI (if enabled)
    if not args.no_ai:
        suggestions = enhance_with_ai(suggestions)
    else:
        # Basic tags
        for s in suggestions:
            s["description"] = f"Used {s['frequency']} times in history"
            s["tags"] = ["history", s["base_command"]]
    
    # Format output
    yaml_output = format_yaml_output(suggestions)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(yaml_output)
        print(f"Suggestions written to {args.output}", file=sys.stderr)
    else:
        print("\n" + yaml_output)
    
    if args.dry_run:
        print("\n[Dry run - no files modified]", file=sys.stderr)


if __name__ == "__main__":
    main()

