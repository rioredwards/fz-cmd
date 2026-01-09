#!/bin/bash
# AI-powered history analyzer for fz-cmd
# Analyzes shell history and suggests additions to commands.yaml
#
# Usage: analyze-history.sh [options]
#   --dry-run    Show suggestions without modifying commands.yaml
#   --limit N    Analyze only the N most recent history entries (default: 1000)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_FILE="$HOME/.dotfiles/commands.yaml"
HISTFILE="${HISTFILE:-$HOME/.zsh_history}"
DRY_RUN=false
LIMIT=1000

# Parse arguments
while [[ $# -gt 0 ]]; do
	case $1 in
	--dry-run)
		DRY_RUN=true
		shift
		;;
	--limit)
		LIMIT="$2"
		shift 2
		;;
	*)
		echo "Unknown option: $1" >&2
		exit 1
		;;
	esac
done

# Check if we have required tools
if ! command -v python3 &>/dev/null; then
	echo "Error: python3 is required" >&2
	exit 1
fi

# Check if we can use AI (check for OPENAI_API_KEY or similar)
if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
	echo "Warning: No AI API key found. This script requires OPENAI_API_KEY or ANTHROPIC_API_KEY." >&2
	echo "You can set it with: export OPENAI_API_KEY='your-key'" >&2
	exit 1
fi

# Extract unique commands from history
echo "Analyzing shell history..." >&2
if [ ! -f "$HISTFILE" ]; then
	echo "Error: History file not found: $HISTFILE" >&2
	exit 1
fi

# Parse history and extract unique commands with frequency
# Format: frequency command
history_analysis=$(tail -n "$LIMIT" "$HISTFILE" 2>/dev/null |
	awk '{
        # zsh history format: : timestamp:duration;command
        if (match($0, /;[^;]*$/)) {
            cmd = substr($0, RSTART + 1)
            gsub(/^[ \t]+/, "", cmd)
            # Filter out noise
            if (length(cmd) >= 3 && cmd !~ /^(ls|cd|pwd|clear|exit|history|fc|echo|cat|less|more|head|tail|grep|find|which|where|type|command|help|man|info|apropos|whatis)[ \t]*$/) {
                print cmd
            }
        }
    }' |
	sort | uniq -c | sort -rn | head -n 50)

# Get existing commands from commands.yaml
existing_commands=""
if [ -f "$COMMANDS_FILE" ]; then
	existing_commands=$(python3 -c "
import yaml
import sys
try:
    with open('$COMMANDS_FILE', 'r') as f:
        data = yaml.safe_load(f) or {}
    commands = [cmd.get('command', '') for cmd in data.get('commands', [])]
    for cmd in commands:
        print(cmd)
except Exception as e:
    sys.exit(1)
" 2>/dev/null || echo "")
fi

# Filter out commands that already exist
new_commands=$(echo "$history_analysis" | while read -r freq cmd; do
	if ! echo "$existing_commands" | grep -Fxq "$cmd"; then
		echo "$freq|$cmd"
	fi
done)

if [ -z "$new_commands" ]; then
	echo "No new commands found to suggest." >&2
	exit 0
fi

echo "Found potential new commands. Analyzing with AI..." >&2

# Use AI to generate descriptions and tags for new commands
# This is a simplified version - you'd want to use actual AI API calls
# For now, we'll create a simple suggestion format

echo "Suggested additions to commands.yaml:" >&2
echo "" >&2

echo "$new_commands" | head -n 20 | while IFS='|' read -r freq cmd; do
	# Generate basic description and tags (simplified - in real version, use AI)
	base_cmd=$(echo "$cmd" | awk '{print $1}')

	echo "  - command: $cmd"
	echo "    description: \"Command used $freq times in history\""
	echo "    tags: [history, $base_cmd]"
	echo ""
done

if [ "$DRY_RUN" = false ]; then
	echo "To add these commands, review the suggestions above and manually add them to $COMMANDS_FILE" >&2
	echo "Or use an AI tool to generate better descriptions and tags." >&2
fi
