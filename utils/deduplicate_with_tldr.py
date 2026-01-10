#!/usr/bin/env python3
"""
Deduplicate null-delimited command history and match with tldr pages.

Reads null-delimited commands from stdin, deduplicates them (keeping most recent),
matches each command to its tldr page (if available), and outputs tab-delimited:
<command>\t<tldr_content>

Output is null-delimited for fzf --read0.
"""

import sys
import subprocess
import re
from typing import Dict, Optional

# Cache for tldr lookups to avoid repeated subprocess calls
_tldr_cache: Dict[str, Optional[str]] = {}


def get_tldr_content(command: str) -> Optional[str]:
    """
    Get tldr page content for a command.
    
    Args:
        command: The command name (first word of the command)
        
    Returns:
        tldr page content as string, or None if not found
    """
    # Extract base command (first word, before any flags/args)
    base_cmd = command.split()[0] if command.split() else command
    base_cmd = base_cmd.strip()
    
    if not base_cmd:
        return None
    
    # Check cache first
    if base_cmd in _tldr_cache:
        return _tldr_cache[base_cmd]
    
    # Try to get tldr page
    try:
        result = subprocess.run(
            ['tldr', base_cmd],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0 and result.stdout.strip():
            content = result.stdout.strip()
            _tldr_cache[base_cmd] = content
            return content
        else:
            _tldr_cache[base_cmd] = None
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        _tldr_cache[base_cmd] = None
        return None


def main():
    seen = set()
    
    # Read null-delimited input
    data = sys.stdin.buffer.read()
    commands = data.split(b'\0')
    
    # Deduplicate while preserving order (first occurrence = most recent)
    for cmd_bytes in commands:
        if not cmd_bytes:
            continue
        
        # Decode to string
        try:
            cmd = cmd_bytes.decode('utf-8', errors='replace').strip()
        except Exception:
            continue
        
        if not cmd:
            continue
        
        # Keep first occurrence (most recent)
        if cmd not in seen:
            seen.add(cmd)
            
            # Get tldr content for this command
            tldr_content = get_tldr_content(cmd)
            
            # Format as: <command>\t<tldr_content>
            # Replace tabs in tldr content with spaces to avoid breaking delimiter
            # (tldr pages shouldn't have tabs, but just in case)
            if tldr_content:
                # Replace tabs with spaces in tldr content to preserve delimiter
                safe_tldr = tldr_content.replace('\t', '    ')
                output = f"{cmd}\t{safe_tldr}"
            else:
                output = f"{cmd}\t"
            
            # Output as null-delimited bytes
            sys.stdout.buffer.write(output.encode('utf-8', errors='replace'))
            sys.stdout.buffer.write(b'\0')
    
    sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
