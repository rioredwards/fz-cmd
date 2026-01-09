#!/usr/bin/env python3
"""
Process shell history for fz-cmd.
Strips line numbers, filters noise, deduplicates, and formats output.
"""

import sys
from collections import OrderedDict

# Set encoding to handle any byte sequence gracefully
if sys.stdin.encoding is None:
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
if sys.stdout.encoding is None:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Noise commands to skip
NOISE_COMMANDS = {'ls', 'cd', 'pwd', 'clear', 'exit', 'history', 'fc', 'echo'}


def process_history(max_entries=100):
    """Process history from stdin and output formatted commands."""
    seen = OrderedDict()  # Preserves insertion order (most recent first)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        # Strip leading line number (fc -l format: "123  command")
        # Find first space after digits
        cmd = line
        for i, char in enumerate(line):
            if char.isdigit():
                continue
            elif char in ' \t':
                cmd = line[i:].strip()
                break
            else:
                # No line number, use whole line
                cmd = line
                break
        
        # Skip empty or very short commands
        if len(cmd) < 3:
            continue
        
        # Skip noise commands (exact match only)
        base_cmd = cmd.split()[0] if cmd.split() else ''
        if base_cmd in NOISE_COMMANDS:
            continue
        
        # Skip fz-cmd itself
        if cmd.startswith('fz-cmd'):
            continue
        
        # Deduplicate - keep most recent occurrence
        # Remove old entry if exists, then add new one at end
        if cmd in seen:
            del seen[cmd]
        seen[cmd] = True
    
    # Output in reverse order (most recent first), limited to max_entries
    commands = list(seen.keys())[-max_entries:]
    commands.reverse()  # Most recent first
    
    for cmd in commands:
        # Extract base command name
        parts = cmd.split()
        base_cmd = parts[0] if parts else cmd
        # Remove path if present
        base_cmd = base_cmd.split('/')[-1]
        
        # Format output: command\tdescription\ttags\texamples
        desc = f"📜 History: {base_cmd}"
        tags = f"history {base_cmd}"
        
        print(f"{cmd}\t{desc}\t{tags}\t")


if __name__ == '__main__':
    max_entries = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    process_history(max_entries)

