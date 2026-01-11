#!/usr/bin/env python3
"""
Safe preview script for tldr content.
SECURITY: This script safely displays tldr content without executing any commands.
Uses Python's print() which does NOT interpret shell metacharacters.
"""

import sys

def main():
    if len(sys.argv) < 2:
        print("No tldr page available for this command")
        return
    
    # Get the tldr content from the first argument
    # sys.argv[1] contains the content, and it's already safely passed as a string
    # Python's print() will output it literally without any shell interpretation
    tldr_content = sys.argv[1]
    
    if not tldr_content or not tldr_content.strip():
        print("No tldr page available for this command")
    else:
        # Print the content - this is completely safe, no shell interpretation
        print(tldr_content)

if __name__ == '__main__':
    main()
