#!/usr/bin/env python3
"""
Deduplicate null-delimited command history and match with tldr pages, aliases, and functions.

Reads null-delimited commands from stdin, deduplicates them (keeping most recent),
matches each command to its alias/function (if available), otherwise tldr page,
and outputs tab-delimited: <command>\t<alias_or_function_or_tldr_content>

Output is null-delimited for fzf --read0.
"""

import sys
import subprocess
import os
import re
from typing import Dict, Optional

# Cache for tldr lookups to avoid repeated subprocess calls
_tldr_cache: Dict[str, Optional[str]] = {}

# Aliases and functions dictionaries
_aliases: Dict[str, str] = {}
_functions: set = set()


def parse_aliases_and_functions():
    """Parse aliases and functions from environment variables."""
    global _aliases, _functions
    
    # Parse aliases from FZ_CMD_ALIASES environment variable
    # Format: name=value, one per line
    aliases_data = os.environ.get('FZ_CMD_ALIASES', '')
    if aliases_data:
        for line in aliases_data.split('\n'):
            line = line.strip()
            if not line:
                continue
            if '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    alias_name = parts[0].strip()
                    alias_value = parts[1].strip()
                    if alias_name and alias_value:
                        _aliases[alias_name] = alias_value
    
    # Parse functions from FZ_CMD_FUNCTIONS environment variable
    # Format: function name, one per line
    functions_data = os.environ.get('FZ_CMD_FUNCTIONS', '')
    if functions_data:
        for line in functions_data.split('\n'):
            func_name = line.strip()
            if func_name:
                _functions.add(func_name)


def get_alias_or_function_info(command: str) -> Optional[str]:
    """
    Get alias or function info for a command.
    
    Args:
        command: The full command string
        
    Returns:
        Alias value if command matches an alias, "Function: name" if matches a function,
        or None if no match
    """
    # Extract base command (first word, before any flags/args)
    base_cmd = command.split()[0] if command.split() else command
    base_cmd = base_cmd.strip()
    
    if not base_cmd:
        return None
    
    # Check if base command exactly matches an alias name
    if base_cmd in _aliases:
        return _aliases[base_cmd]
    
    # Check if base command exactly matches a function name
    if base_cmd in _functions:
        return f"Function: {base_cmd}"
    
    return None


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
    # Parse aliases and functions from environment
    parse_aliases_and_functions()
    
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
            
            # Get alias/function info first (priority over tldr)
            alias_or_func_info = get_alias_or_function_info(cmd)
            
            if alias_or_func_info:
                # Replace tabs with spaces to preserve delimiter
                safe_info = alias_or_func_info.replace('\t', '    ')
                output = f"{cmd}\t{safe_info}"
            else:
                # Fall back to tldr content
                tldr_content = get_tldr_content(cmd)
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
