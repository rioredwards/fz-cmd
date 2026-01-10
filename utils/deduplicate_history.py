#!/usr/bin/env python3
"""
Deduplicate null-delimited command history, keeping the most recent occurrence.

Reads null-delimited input from stdin and outputs deduplicated null-delimited
commands to stdout. Since input is ordered newest-first, we keep the first
occurrence of each unique command.
"""

import sys

def main():
    seen = set()
    
    # Read null-delimited input
    # sys.stdin.buffer.read() reads bytes, then we split on null bytes
    data = sys.stdin.buffer.read()
    commands = data.split(b'\0')
    
    # Deduplicate while preserving order (first occurrence = most recent)
    for cmd_bytes in commands:
        if not cmd_bytes:
            continue
        
        # Decode to string for comparison
        try:
            cmd = cmd_bytes.decode('utf-8', errors='replace').strip()
        except Exception:
            continue
        
        if not cmd:
            continue
        
        # Keep first occurrence (most recent)
        if cmd not in seen:
            seen.add(cmd)
            # Output as null-delimited bytes
            sys.stdout.buffer.write(cmd_bytes)
            sys.stdout.buffer.write(b'\0')
    
    sys.stdout.buffer.flush()

if __name__ == '__main__':
    main()
