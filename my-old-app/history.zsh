# Shell history integration for fz-cmd
# Simple, maintainable implementation

# Enable/disable history integration (set FZ_CMD_ENABLE_HISTORY=0 to disable)
: ${FZ_CMD_ENABLE_HISTORY:=1}

# Max number of history entries to process (default: 100)
: ${FZ_CMD_MAX_HISTORY:=100}

# Get shell history entries
# Returns tab-separated: command\tdescription\ttags\texamples
_fz-cmd-get-history() {
	# Check if history integration is enabled
	if [ "${FZ_CMD_ENABLE_HISTORY:-1}" != "1" ]; then
		return 0
	fi

	local max_history_entries="${FZ_CMD_MAX_HISTORY:-100}"

	# Get history using zsh builtin history command (limit to last N entries for performance)
	local history_commands
	if command -v history >/dev/null 2>&1; then
		history_commands=$(history "$max_history_entries" 2>/dev/null)
	else
		return 0
	fi

	if [ -z "$history_commands" ]; then
		return 0
	fi

	# Process history: strip line numbers, filter noise, deduplicate, format
	local python_script="${HOME}/.dotfiles/zsh/fz-cmd/history.py"
	if command -v python3 >/dev/null 2>&1 && [ -f "$python_script" ]; then
		echo "$history_commands" | python3 "$python_script" "$max_history_entries"
	else
		# Fallback: simple deduplication without Python
		# Use LC_ALL=C to handle any byte sequence (including invalid UTF-8)
		echo "$history_commands" | sed 's/^[0-9]*[ \t]*//' | LC_ALL=C sort -u | head -n "$max_history_entries"
	fi
}
