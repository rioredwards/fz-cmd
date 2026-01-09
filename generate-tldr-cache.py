#!/usr/bin/env python3
"""
Generate cached tldr entries in YAML format matching commands.yaml structure.
Run this script to update the tldr cache: python3 generate-tldr-cache.py
"""

import sys
import subprocess
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    print("  Or: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)

def get_tldr_pages(platform=None):
    """Get list of tldr pages, optionally filtered by platform.
    
    Args:
        platform: Platform to filter by (e.g., 'osx', 'common', 'linux'). 
                  If None, gets all pages.
    """
    try:
        cmd = ['tldr', '--list']
        if platform:
            cmd.extend(['--platform', platform])
        
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        if result.returncode != 0:
            print(f"Error: tldr --list failed with return code {result.returncode}", file=sys.stderr)
            return []
        
        pages = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
        # Filter out ANSI escape codes and invalid entries
        pages = [p for p in pages if not p.startswith('\x1b') and not p.startswith('Pages for')]
        return pages
    except subprocess.TimeoutExpired:
        print("Error: tldr --list timed out", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("Error: tldr command not found. Install with: brew install tldr", file=sys.stderr)
        return []

def extract_command_from_tldr(content, page_name):
    """Extract the command name from tldr content.
    
    RULE: Command Name
    - The command name is the FIRST non-empty line in the content
    - This is the base command (e.g., "head", "lpstat", "reboot")
    """
    lines = content.split('\n')
    
    # Find first non-empty line
    for line in lines:
        line_stripped = line.strip()
        if line_stripped:
            return line_stripped
    
    # Fallback to page name
    return page_name

def extract_description_from_tldr(content):
    """Extract description from tldr content.
    
    RULE: Description
    - Skip the first line (command name)
    - Skip the next line if it's empty
    - The description is the FIRST non-empty line after the command name
    - Stop at lines that start with "See also:", "More information:", or "- " (example descriptions)
    """
    lines = content.split('\n')
    
    # Skip first line (command name)
    skip_first = True
    for line in lines:
        line_stripped = line.strip()
        
        # Skip first non-empty line (command name)
        if skip_first and line_stripped:
            skip_first = False
            continue
        
        # Skip empty lines
        if not line_stripped:
            continue
        
        # Stop at metadata lines
        if line_stripped.startswith('See also:') or line_stripped.startswith('More information:'):
            break
        
        # Stop at example descriptions
        if line_stripped.startswith('- '):
            break
        
        # Found description
        return line_stripped[:200]  # Limit to 200 chars
    
    return None

def extract_examples_from_tldr(content, command_name):
    """Extract example commands with descriptions from tldr content.
    
    RULE: Examples
    - Find all lines that start with "- " (these are example descriptions)
    - For each line starting with "- ":
      - Extract the description text (remove the "- " prefix)
      - Look at the NEXT line
      - If the next line is indented (starts with spaces):
        - Extract the entire indented line (this is the example command)
        - Trim leading/trailing whitespace
        - Create object with description and command
        - Add to examples array
    - If no examples found, use command name as single example with no description
    """
    lines = content.split('\n')
    examples = []
    
    for i, line in enumerate(lines):
        # Find lines starting with "- " (example descriptions)
        desc_match = re.match(r'^\s*-\s+(.+)', line)
        if desc_match:
            description = desc_match.group(1).strip()
            # Look at the next line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Check if next line is indented (starts with spaces)
                if re.match(r'^\s+', next_line):
                    command = next_line.strip()
                    if command:
                        examples.append({
                            'description': description,
                            'command': command
                        })
    
    # Edge case: If no examples found, use command name as single example
    if not examples:
        examples = [{'description': '', 'command': command_name}]
    
    return examples

def process_tldr_pages(pages, max_pages=None):
    """Process tldr pages and return list of command entries."""
    commands = []
    
    if max_pages:
        pages = pages[:max_pages]
    
    print(f"Processing {len(pages)} tldr pages...", file=sys.stderr)
    
    for idx, page in enumerate(pages, 1):
        if idx % 50 == 0:
            print(f"  Processed {idx}/{len(pages)} pages...", file=sys.stderr)
        
        try:
            result = subprocess.run(['tldr', page], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=3)
            if result.returncode != 0:
                continue
            
            content = result.stdout
            if not content:
                continue
            
            # Extract command, description, and examples using the extraction rules
            cmd = extract_command_from_tldr(content, page)
            desc = extract_description_from_tldr(content)
            examples = extract_examples_from_tldr(content, cmd)
            
            # Edge case: If no description found, use default
            if not desc:
                desc = f"Command from tldr: {page}"
            
            # Create entry matching commands.yaml format
            entry = {
                'command': cmd,
                'description': desc,
                'examples': examples
            }
            
            commands.append(entry)
            
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            print(f"  Warning: Error processing {page}: {e}", file=sys.stderr)
            continue
    
    return commands

def main():
    """Generate tldr cache YAML file."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate tldr cache YAML file')
    parser.add_argument('--limit', type=int, default=None, 
                       help='Limit number of pages to process (for faster iteration)')
    parser.add_argument('--platform', type=str, default='osx',
                       help='Platform to filter pages (osx, common, linux, windows, sunos). Default: osx')
    args = parser.parse_args()
    
    # Determine output file path
    script_dir = Path(__file__).parent
    output_file = script_dir / 'tldr-commands.yaml'
    
    print(f"Fetching tldr pages (platform: {args.platform})...", file=sys.stderr)
    pages = get_tldr_pages(platform=args.platform)
    
    if not pages:
        print("No tldr pages found. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    total_pages = len(pages)
    if args.limit:
        pages = pages[:args.limit]
        print(f"Found {total_pages} tldr pages (processing first {len(pages)} due to --limit)", file=sys.stderr)
    else:
        print(f"Found {len(pages)} tldr pages", file=sys.stderr)
    
    # Process pages
    commands = process_tldr_pages(pages)
    
    if not commands:
        print("No commands extracted. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    # Write YAML file
    output_data = {'commands': commands}
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Use block style for everything (more readable, allows for future example descriptions)
            yaml.dump(output_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"\n✓ Generated {len(commands)} tldr commands", file=sys.stderr)
        print(f"✓ Saved to: {output_file}", file=sys.stderr)
        print(f"\nTo refresh cache, run:  scripts/refresh_cache.sh", file=sys.stderr)
        
    except Exception as e:
        print(f"Error writing YAML file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

