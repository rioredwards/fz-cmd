#!/bin/sh
# Safe preview script for tldr content
# SECURITY: This script safely displays tldr content without executing any commands
# Uses printf which does NOT interpret shell metacharacters or escape sequences

if [ -z "$1" ]; then
    # If no argument, show message
    printf 'No tldr page available for this command\n'
else
    # Print the content safely using printf
    # printf '%s' prints the argument literally without any interpretation
    # This prevents any shell metacharacters from being executed
    printf '%s\n' "$1"
fi
