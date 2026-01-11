#!/usr/bin/env python3
"""
Deduplicate null-delimited command history and match with tldr pages, functions, and aliases.

Reads null-delimited commands from stdin, deduplicates them (keeping most recent),
matches each command to its tldr page, function definition, or alias definition (if available),
and outputs tab-delimited: <command>\t<preview_content>

Output is null-delimited for fzf --read0.

Uses the same patterns as sources/source_aliases.py and sources/source_functions.py
to get all aliases and functions upfront, then does fast dictionary lookups.
"""

import sys
import subprocess
import re
from typing import Dict, Optional, Tuple

# Cache for tldr lookups (done on-demand)
_tldr_cache: Dict[str, Optional[str]] = {}

# Aliases and functions loaded upfront (following source_aliases.py and source_functions.py patterns)
_aliases: Dict[str, str] = {}  # name -> "Alias: name\nExpands to: value"
_functions: Dict[str, str] = {}  # name -> "Function: name\n\n<definition>"


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


def load_aliases() -> Dict[str, str]:
    """
    Load all aliases upfront (following source_aliases.py pattern).
    
    Returns:
        Dictionary mapping alias name -> preview string
    """
    try:
        # Use same pattern as source_aliases.py
        result = subprocess.run(
            ["zsh", "-i", "-c", "alias"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {}
        
        aliases = {}
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            
            # Remove "alias " prefix
            line = line.replace("alias ", "", 1).strip()
            
            # Parse: name='value' or name="value" or name=value
            match = re.match(r'^([^=]+)=(.+)$', line)
            if not match:
                continue
            
            name = match.group(1).strip()
            value = match.group(2).strip()
            
            # Skip internal aliases (same as source_aliases.py)
            if name.startswith("_") or name.startswith("."):
                continue
            
            # Remove quotes if present
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]
            
            aliases[name] = f"Alias: {name}\nExpands to: {value}"
        
        return aliases
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return {}


def load_functions() -> Dict[str, str]:
    """
    Load all functions upfront (following source_functions.py pattern).
    
    Returns:
        Dictionary mapping function name -> preview string with definition
    """
    try:
        # First get function names (same pattern as source_functions.py)
        result = subprocess.run(
            ["zsh", "-i", "-c", "print -l ${(k)functions}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {}
        
        # Prefixes for internal/framework functions to skip (same as source_functions.py)
        skip_prefixes = (
            "_", "nvm_", "prompt_", "compdef", "compadd", "zle-", "async_"
        )
        
        function_names = []
        for line in result.stdout.strip().split("\n"):
            func_name = line.strip()
            if not func_name:
                continue
            # Skip internal/framework functions
            if func_name.startswith(skip_prefixes):
                continue
            # Only valid function name patterns
            if func_name.replace("_", "").replace("-", "").isalnum():
                function_names.append(func_name)
        
        # Now get definitions for each function
        # Get them individually but cache results
        functions = {}
        for func_name in function_names:
            try:
                def_result = subprocess.run(
                    ["zsh", "-i", "-c", f"functions {func_name}"],
                    capture_output=True,
                    text=True,
                    timeout=1  # Short timeout per function
                )
                if def_result.returncode == 0 and def_result.stdout.strip():
                    functions[func_name] = f"Function: {func_name}\n\n{def_result.stdout.strip()}"
            except Exception:
                continue  # Skip this function if it times out or errors
        
        return functions
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return {}


def get_preview_content(command: str, aliases: Dict[str, str], functions: Dict[str, str]) -> Optional[str]:
    """
    Get preview content for a command using pre-loaded aliases and functions.
    
    Args:
        command: The command string
        aliases: Pre-loaded aliases dictionary
        functions: Pre-loaded functions dictionary
        
    Returns:
        Preview content string, or None if not found
    """
    base_cmd = command.split()[0] if command.split() else command
    base_cmd = base_cmd.strip()
    
    if not base_cmd:
        return None
    
    # Fast dictionary lookup for alias (O(1))
    if base_cmd in aliases:
        return aliases[base_cmd]
    
    # Fast dictionary lookup for function (O(1))
    if base_cmd in functions:
        return functions[base_cmd]
    
    # Check tldr as fallback (cached, so still fast)
    tldr_content = get_tldr_content(command)
    if tldr_content:
        return tldr_content
    
    return None


def main():
    seen = set()
    
    # Don't load aliases/functions upfront - it's too slow and causes hangs
    # Instead, let the preview script use 'which' for on-demand lookups (much faster!)
    
    # Read null-delimited input (history commands)
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
            
            # Just output command with empty preview - preview script will use 'which' on-demand
            # This is much faster and avoids hangs
            output = f"{cmd}\t"
            
            # Output as null-delimited bytes
            sys.stdout.buffer.write(output.encode('utf-8', errors='replace'))
            sys.stdout.buffer.write(b'\0')
    
    sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
