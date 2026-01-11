#!/usr/bin/env python3
"""
Safe preview script for tldr content, aliases, and functions.
SECURITY: This script safely displays content without executing any commands.
Uses Python's print() which does NOT interpret shell metacharacters.

If field 2 is empty, looks up the command on-demand.
"""

import sys
import subprocess
import re
from typing import Optional

def get_command_info(base_cmd: str) -> Optional[str]:
    """
    Get command info - DISABLED for now due to performance issues.
    zsh -i is too slow and causes hangs.
    TODO: Find a faster way to get aliases/functions without interactive shell.
    """
    # Disabled - causes hangs with zsh -i
    return None

def get_tldr_content(command: str) -> str:
    """Get tldr page content for a command."""
    base_cmd = command.split()[0] if command.split() else command
    base_cmd = base_cmd.strip()
    if not base_cmd:
        return None
    
    try:
        result = subprocess.run(
            ['tldr', base_cmd],
            capture_output=True,
            text=True,
            timeout=0.5  # Very short timeout
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, Exception):
        pass
    return None

def main():
    if len(sys.argv) < 2:
        print("No preview available")
        return
    
    # Get the command from field 1 (we extract it from the tab-delimited input)
    # fzf passes the full line, so we need to extract field 1
    full_line = sys.argv[1]
    parts = full_line.split('\t', 1)
    command = parts[0] if parts else full_line
    preview_content = parts[1] if len(parts) > 1 else ""
    
    # If preview content was pre-computed, use it
    if preview_content and preview_content.strip():
        print(preview_content)
        return
    
    # Otherwise, look it up on-demand using 'which' (much faster!)
    base_cmd = command.split()[0] if command.split() else command
    base_cmd = base_cmd.strip()
    
    if not base_cmd:
        print("No preview available")
        return
    
    # Alias/function lookup disabled - too slow and causes hangs
    # Just try tldr
    try:
        tldr_content = get_tldr_content(command)
        if tldr_content:
            print(tldr_content)
            return
    except Exception:
        pass
    
    print("No preview available for this command")

if __name__ == '__main__':
    main()
