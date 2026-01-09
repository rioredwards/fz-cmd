#!/usr/bin/env python3
"""
Generate preview text from command fields for fzf preview window.

Takes 5 arguments from fzf field placeholders:
  {1} display - formatted display text (not used in preview)
  {2} command - the actual command
  {3} description - command description
  {4} tags - comma-separated tags
  {5} examples - pipe-separated examples

ANSI color codes for terminal output:
  - Bold Cyan: labels (Command:, Description:, etc.)
  - White: values
  - Yellow: example descriptions (if present)
  - Green: example commands
"""

import sys

# ANSI color codes
LABEL = "\033[1;36m"      # Bold cyan for labels
RESET = "\033[0m"         # Reset
VALUE = "\033[0;37m"      # White for values
EXAMPLE_DESC = "\033[33m" # Yellow for example descriptions
EXAMPLE_CMD = "\033[32m"  # Green for example commands


def build_preview(display: str, command: str, description: str, tags: str, examples: str) -> str:
    """
    Build colored preview text for fzf preview window.
    
    Args:
        display: Formatted display text (ignored - we use raw fields)
        command: The actual command
        description: Command description
        tags: Comma-separated tags string
        examples: Pipe-separated examples string
        
    Returns:
        Formatted preview text with ANSI colors
    """
    lines = []
    
    # Command section
    lines.append(f"{LABEL}Command:{RESET}")
    lines.append(f"{VALUE}  {command}{RESET}")
    lines.append("")
    
    # Description section
    if description:
        lines.append(f"{LABEL}Description:{RESET}")
        lines.append(f"{VALUE}  {description}{RESET}")
        lines.append("")
    
    # Tags section
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            lines.append(f"{LABEL}Tags:{RESET}")
            lines.append(f"{VALUE}  {', '.join(tag_list)}{RESET}")
            lines.append("")
    
    # Examples section
    if examples:
        example_list = [e.strip() for e in examples.split("|") if e.strip()]
        if example_list:
            lines.append(f"{LABEL}Examples:{RESET}")
            for example in example_list:
                # Check if example has description (contains ": ")
                if ": " in example:
                    desc, cmd = example.split(": ", 1)
                    lines.append(f"  {EXAMPLE_DESC}{desc}{RESET}")
                    lines.append(f"    {EXAMPLE_CMD}$ {cmd}{RESET}")
                else:
                    lines.append(f"  {EXAMPLE_CMD}$ {example}{RESET}")
    
    return "\n".join(lines)


def main():
    """Main entry point - reads from arguments or stdin."""
    display = ""
    command = ""
    description = ""
    tags = ""
    examples = ""
    
    # Priority 1: Check for 5 arguments (direct call mode - for testing)
    if len(sys.argv) >= 6:
        display = sys.argv[1]
        command = sys.argv[2]
        description = sys.argv[3]
        tags = sys.argv[4]
        examples = sys.argv[5]
    # Priority 2: Check for single tab-separated argument
    elif len(sys.argv) == 2:
        parts = sys.argv[1].split("\t")
        display = parts[0] if len(parts) > 0 else ""
        command = parts[1] if len(parts) > 1 else ""
        description = parts[2] if len(parts) > 2 else ""
        tags = parts[3] if len(parts) > 3 else ""
        examples = parts[4] if len(parts) > 4 else ""
    # Priority 3: Read from stdin (piped input from fzf)
    elif not sys.stdin.isatty():
        line = sys.stdin.read().strip()
        if line:
            parts = line.split("\t")
            display = parts[0] if len(parts) > 0 else ""
            command = parts[1] if len(parts) > 1 else ""
            description = parts[2] if len(parts) > 2 else ""
            tags = parts[3] if len(parts) > 3 else ""
            examples = parts[4] if len(parts) > 4 else ""
    else:
        print("Usage: build_preview.py <display> <command> <description> <tags> <examples>", file=sys.stderr)
        print("  Or pipe a tab-separated line to stdin", file=sys.stderr)
        sys.exit(1)
    
    preview = build_preview(display, command, description, tags, examples)
    print(preview)


if __name__ == "__main__":
    main()
