#!/usr/bin/env python3
"""
Parse commands.yaml and output tab-separated format:
command\tdescription\ttags\texamples
"""
import yaml
import sys
import os

try:
    # Accept file path as command line argument, or use default
    if len(sys.argv) > 1:
        commands_file = sys.argv[1]
    else:
        commands_file = os.path.expanduser("~/.dotfiles/commands.yaml")
    
    with open(commands_file, 'r') as f:
        data = yaml.safe_load(f)
    
    # Determine emoji and special marker based on file path
    if 'tldr-commands.yaml' in commands_file:
        emoji = '📖'  # Book emoji for tldr documentation
        special_marker = '?tldr'  # Special marker for filtering tldr commands
    else:
        emoji = '⭐'  # Star emoji for curated commands
        special_marker = ''
    
    for cmd in data.get('commands', []):
        command = cmd.get('command', '')
        description = cmd.get('description', '')
        # Add emoji if not already present (preserve history emoji 📜)
        if not description.startswith('📜') and not description.startswith('📖') and not description.startswith('⭐'):
            description = f"{emoji} {description}"
        tags = ' '.join(cmd.get('tags', []))
        # Add special marker to tags for tldr commands (searchable by "?")
        if special_marker:
            tags = f"{special_marker} {tags}" if tags else special_marker
        
        # Handle examples - can be simple strings or objects with description/command
        examples_list = cmd.get('examples', [])
        examples_parts = []
        for ex in examples_list:
            if isinstance(ex, dict):
                # Object format: {description: "...", command: "..."}
                desc = ex.get('description', '').strip()
                ex_cmd = ex.get('command', '').strip()
                if desc and ex_cmd:
                    examples_parts.append(f"{desc}: {ex_cmd}")
                elif ex_cmd:
                    examples_parts.append(ex_cmd)
            else:
                # Simple string format
                examples_parts.append(str(ex))
        
        examples = '; '.join(examples_parts) if examples_parts else ''
        print(f"{command}\t{description}\t{tags}\t{examples}")
except Exception:
    sys.exit(1)

