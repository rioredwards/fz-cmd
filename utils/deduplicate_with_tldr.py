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
import time
import json
from pathlib import Path
from typing import Dict, Optional

# Cache for tldr lookups to avoid repeated subprocess calls
_tldr_cache: Dict[str, Optional[str]] = {}
_tldr_cache_file: Optional[Path] = None

# Aliases and functions dictionaries
_aliases: Dict[str, str] = {}
_functions: Dict[str, str] = {}  # Changed to dict to store function bodies

# Debug logging
_debug_log_path = os.environ.get('FZ_CMD_DEBUG_LOG', '')


def _load_tldr_cache():
    """Load persistent tldr cache from file."""
    global _tldr_cache, _tldr_cache_file
    
    # Determine cache file path
    script_dir = Path(__file__).parent.parent
    _tldr_cache_file = script_dir / 'cache' / 'tldr_cache.json'
    
    if not _tldr_cache_file.exists():
        # if _debug_log_path:
        #     try:
        #         with open(_debug_log_path, 'a') as f:
        #             f.write(f"[TIMING] python.load_cache: cache file not found, starting fresh\n")
        #             f.flush()
        #     except Exception:
        #         pass
        return
    
    load_start = time.time()
    try:
        with open(_tldr_cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _tldr_cache = data.get('cache', {})
            # Convert None strings back to None
            _tldr_cache = {k: (None if v == '__None__' else v) for k, v in _tldr_cache.items()}
        _debug_timing("load_cache", load_start)
        # if _debug_log_path:
        #     try:
        #         with open(_debug_log_path, 'a') as f:
        #             f.write(f"[TIMING] python.load_cache.entries: {len(_tldr_cache)}\n")
        #             f.flush()
        #     except Exception:
        #         pass
    except Exception as e:
        # if _debug_log_path:
        #     try:
        #         with open(_debug_log_path, 'a') as f:
        #             f.write(f"[TIMING] python.load_cache.error: {str(e)}\n")
        #             f.flush()
        #     except Exception:
        #         pass
        _tldr_cache = {}


def _save_tldr_cache():
    """Save tldr cache to file (only new entries to avoid full rewrite)."""
    global _tldr_cache, _tldr_cache_file
    
    if not _tldr_cache_file:
        return
    
    save_start = time.time()
    try:
        # Convert None to string for JSON serialization
        cache_data = {k: ('__None__' if v is None else v) for k, v in _tldr_cache.items()}
        data = {'cache': cache_data}
        
        # Create cache directory if it doesn't exist
        _tldr_cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(_tldr_cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _debug_timing("save_cache", save_start)
    except Exception as e:
        # if _debug_log_path:
        #     try:
        #         with open(_debug_log_path, 'a') as f:
        #             f.write(f"[TIMING] python.save_cache.error: {str(e)}\n")
        #             f.flush()
        #     except Exception:
        #         pass
        pass  # Silently fail if cache save fails


def _debug_timing(label: str, start_time: float, end_time: float = None):
    """Write timing information to debug log if enabled."""
    if not _debug_log_path:
        return
    if end_time is None:
        end_time = time.time()
    duration = end_time - start_time
    try:
        with open(_debug_log_path, 'a') as f:
            f.write(f"[TIMING] python.{label}: {duration:.6f}s\n")
            f.flush()
    except Exception:
        pass  # Silently fail if we can't write to debug log


def parse_aliases_and_functions():
    """Parse aliases and functions from environment variables."""
    global _aliases, _functions
    
    start_time = time.time()
    
    # Parse aliases from FZ_CMD_ALIASES environment variable
    # Format: name=value, one per line
    aliases_data = os.environ.get('FZ_CMD_ALIASES', '')
    alias_start = time.time()
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
    _debug_timing("parse_aliases", alias_start)
    
    # Parse functions from FZ_CMD_FUNCTIONS environment variable
    # Format: name=body, one per line
    functions_data = os.environ.get('FZ_CMD_FUNCTIONS', '')
    func_start = time.time()
    if functions_data:
        for line in functions_data.split('\n'):
            line = line.strip()
            if not line:
                continue
            if '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    func_name = parts[0].strip()
                    func_body = parts[1].strip()
                    if func_name and func_body:
                        _functions[func_name] = func_body
    _debug_timing("parse_functions", func_start)
    _debug_timing("parse_aliases_and_functions", start_time)


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
    
    # Check aliases first (priority over functions)
    if base_cmd in _aliases:
        return _aliases[base_cmd]
    
    # Check if base command exactly matches a function name
    if base_cmd in _functions:
        return _functions[base_cmd]
    
    return None


def get_tldr_content(command: str) -> Optional[str]:
    """
    Get tldr page content for a command.
    
    Args:
        command: The command name (first word of the command)
        
    Returns:
        tldr page content as string, or None if not found
    """
    start_time = time.time()
    
    # Extract base command (first word, before any flags/args)
    base_cmd = command.split()[0] if command.split() else command
    base_cmd = base_cmd.strip()
    
    if not base_cmd:
        return None
    
    # Check cache first (persistent cache loaded at startup)
    if base_cmd in _tldr_cache:
        # _debug_timing("get_tldr_content.cached", start_time)  # Removed: repeats hundreds of times
        return _tldr_cache[base_cmd]
    
    # Try to get tldr page (only if not in cache)
    subprocess_start = time.time()
    try:
        result = subprocess.run(
            ['tldr', base_cmd],
            capture_output=True,
            text=True,
            timeout=2
        )
        # _debug_timing("get_tldr_content.subprocess", subprocess_start)  # Removed: repeats hundreds of times
        
        if result.returncode == 0 and result.stdout.strip():
            content = result.stdout.strip()
            _tldr_cache[base_cmd] = content
            # _debug_timing("get_tldr_content.total", start_time)  # Removed: repeats hundreds of times
            return content
        else:
            _tldr_cache[base_cmd] = None
            # _debug_timing("get_tldr_content.total", start_time)  # Removed: repeats hundreds of times
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        _tldr_cache[base_cmd] = None
        # _debug_timing("get_tldr_content.total", start_time)  # Removed: repeats hundreds of times
        return None


def main():
    main_start = time.time()
    
    # Log that Python processing started (for debugging)
    # if _debug_log_path:
    #     try:
    #         with open(_debug_log_path, 'a') as f:
    #             f.write(f"[TIMING] python.main: started\n")
    #             f.flush()
    #     except Exception:
    #         pass
    
    # Load persistent tldr cache
    _load_tldr_cache()
    
    # Parse aliases and functions from environment
    parse_aliases_and_functions()
    
    seen = set()
    
    # Read null-delimited input
    read_start = time.time()
    data = sys.stdin.buffer.read()
    _debug_timing("read_stdin", read_start)
    
    split_start = time.time()
    commands = data.split(b'\0')
    _debug_timing("split_commands", split_start)
    
    # Deduplicate while preserving order (first occurrence = most recent)
    dedupe_start = time.time()
    alias_func_time = 0.0
    tldr_time = 0.0
    output_time = 0.0
    processed_count = 0
    
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
            processed_count += 1
            
            # Get alias/function info first (priority over tldr)
            alias_func_start = time.time()
            alias_or_func_info = get_alias_or_function_info(cmd)
            alias_func_time += time.time() - alias_func_start
            
            if alias_or_func_info:
                # Replace tabs with spaces to preserve delimiter
                safe_info = alias_or_func_info.replace('\t', '    ')
                output = f"{cmd}\t{safe_info}"
            else:
                # Fall back to tldr content
                tldr_start = time.time()
                tldr_content = get_tldr_content(cmd)
                tldr_time += time.time() - tldr_start
                if tldr_content:
                    # Replace tabs with spaces in tldr content to preserve delimiter
                    safe_tldr = tldr_content.replace('\t', '    ')
                    output = f"{cmd}\t{safe_tldr}"
                else:
                    output = f"{cmd}\t"
            
            # Output as null-delimited bytes
            output_start = time.time()
            sys.stdout.buffer.write(output.encode('utf-8', errors='replace'))
            sys.stdout.buffer.write(b'\0')
            output_time += time.time() - output_start
    
    _debug_timing("dedupe_loop", dedupe_start)
    if _debug_log_path:
        try:
            with open(_debug_log_path, 'a') as f:
                f.write(f"[TIMING] python.dedupe_loop.alias_func_total: {alias_func_time:.6f}s\n")
                f.write(f"[TIMING] python.dedupe_loop.tldr_total: {tldr_time:.6f}s\n")
                f.write(f"[TIMING] python.dedupe_loop.output_total: {output_time:.6f}s\n")
                # f.write(f"[TIMING] python.processed_commands: {processed_count}\n")  # Commented: not performance-related
                f.flush()
        except Exception:
            pass
    
    flush_start = time.time()
    sys.stdout.buffer.flush()
    _debug_timing("flush_output", flush_start)
    
    # Save cache with any new entries discovered during this run
    _save_tldr_cache()
    
    _debug_timing("main_total", main_start)


if __name__ == '__main__':
    main()
