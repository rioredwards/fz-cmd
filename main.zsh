# Command search with tags
# Main entry point for fz-cmd functionality
# Refactored to use cached JSON data and Python utilities
#
# SECURITY MODEL:
# ==============
# This script NEVER executes commands automatically. It only:
# 1. Displays commands in fzf for selection
# 2. Inserts selected commands into the command line buffer (LBUFFER or print -z)
# 3. Requires explicit user confirmation (Enter key) to execute
#
# Commands are NEVER executed by:
# - eval, exec, sh -c, or command substitution
# - Direct execution or background processes
# - Preview commands (only display text)
#
# User must ALWAYS press Enter to execute any command.

FZ_CMD_DIR="$HOME/.dotfiles/zsh/fz-cmd"
CACHE_DIR="$FZ_CMD_DIR/cache"
UTILS_DIR="$FZ_CMD_DIR/utils"
SOURCES_DIR="$FZ_CMD_DIR/sources"

# Core function that orchestrates the command search
_fz-cmd-core() {
	local start_time
	if [ "${FZ_CMD_DEBUG:-0}" = "1" ]; then
		start_time=$(date +%s.%N)
	fi

	# Data limits for fast startup (can be overridden via env vars)
	local limit_curated="${FZ_CMD_LIMIT_CURATED:-1000}"
	local limit_alias="${FZ_CMD_LIMIT_ALIAS:-100}"
	local limit_function="${FZ_CMD_LIMIT_FUNCTION:-100}"
	local limit_history="${FZ_CMD_LIMIT_HISTORY:-200}"
	local limit_tldr="${FZ_CMD_LIMIT_TLDR:-500}"

	# Check if cache directory exists
	if [ ! -d "$CACHE_DIR" ]; then
		echo "Error: Cache directory not found. Run: $FZ_CMD_DIR/scripts/refresh_cache.sh" >&2
		return 1
	fi

	# Load and merge cached data
	local merged_file
	merged_file=$(mktemp)

	# Collect cache files that exist
	local cache_files=()
	[ -f "$CACHE_DIR/commands.json" ] && cache_files+=("$CACHE_DIR/commands.json")
	[ -f "$CACHE_DIR/aliases.json" ] && cache_files+=("$CACHE_DIR/aliases.json")
	[ -f "$CACHE_DIR/functions.json" ] && cache_files+=("$CACHE_DIR/functions.json")
	[ -f "$CACHE_DIR/history.json" ] && cache_files+=("$CACHE_DIR/history.json")

	# Check if we should include tldr (default: no, for speed)
	local include_tldr="${FZ_CMD_INCLUDE_TLDR:-0}"
	if [ "$include_tldr" = "1" ] && [ -f "$CACHE_DIR/tldr.json" ]; then
		cache_files+=("$CACHE_DIR/tldr.json")
	fi

	if [ ${#cache_files[@]} -eq 0 ]; then
		echo "Error: No cache files found. Run: $FZ_CMD_DIR/scripts/refresh_cache.sh" >&2
		return 1
	fi

	# Merge cache files
	if [ "${FZ_CMD_DEBUG:-0}" = "1" ]; then
		echo "[DEBUG] Merging ${#cache_files[@]} cache files..." >&2
	fi

	python3 "$UTILS_DIR/merge_commands.py" "${cache_files[@]}" >"$merged_file"

	# TEMP_DEBUG: Print the merged file
	# echo "[🔥 TEMP_DEBUG] $(cat "$merged_file")" >&2

	if [ $? -ne 0 ]; then
		echo "Error: Failed to merge cache files" >&2
		rm -f "$merged_file"
		return 1
	fi

	# Apply limits if specified
	local limited_file
	limited_file=$(mktemp)

	local limit_args=()
	[ "$limit_curated" != "0" ] && limit_args+=("--limit" "curated:$limit_curated")
	[ "$limit_alias" != "0" ] && limit_args+=("--limit" "alias:$limit_alias")
	[ "$limit_function" != "0" ] && limit_args+=("--limit" "function:$limit_function")
	[ "$limit_history" != "0" ] && limit_args+=("--limit" "history:$limit_history")
	[ "$limit_tldr" != "0" ] && limit_args+=("--limit" "tldr:$limit_tldr")

	if [ ${#limit_args[@]} -gt 0 ]; then
		python3 "$UTILS_DIR/limit_commands.py" "$merged_file" "${limit_args[@]}" >"$limited_file"
		mv "$limited_file" "$merged_file"
	else
		rm -f "$limited_file"
	fi

	# TEMP_DEBUG: Print the limited file
	# echo "[🔥 TEMP_DEBUG] $(cat "$merged_file")" >&2

	# Format for fzf (without recent sorting for now - simpler and more reliable)
	local formatted_file
	formatted_file=$(mktemp)

	python3 "$UTILS_DIR/format_for_fzf.py" "$merged_file" >"$formatted_file" 2>&1

	if [ $? -ne 0 ] || [ ! -s "$formatted_file" ]; then
		echo "Error: Failed to format commands" >&2
		cat "$formatted_file" >&2 # Show what went wrong
		rm -f "$merged_file" "$formatted_file"
		return 1
	fi

	if [ "${FZ_CMD_DEBUG:-0}" = "1" ]; then
		local end_time
		end_time=$(date +%s.%N)
		local elapsed
		elapsed=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "?")
		echo "[DEBUG] Total time: ${elapsed}s" >&2
	fi

	# Build preview command
	# Pipe the entire selected line to build_preview.py via stdin
	# This avoids shell quoting issues with special characters in field values
	# The preview script parses the tab-separated line internally
	local preview_script
	preview_script="$UTILS_DIR/build_preview.py"
	# Convert to absolute path if relative
	if [[ "$preview_script" != /* ]]; then
		preview_script="$(cd "$FZ_CMD_DIR" && pwd)/utils/build_preview.py"
	fi

	# Preview command: echo the line and pipe to python
	# Using double-escaped quotes for the fzf preview context
	local preview_cmd
	preview_cmd="echo {} | python3 '$preview_script'"

	# Use fzf to select command
	# Format: <display> \t <command> \t <description> \t <tags> \t <examples>
	# Field 1: Display (command + invisible searchable text)
	# Field 2: Raw command for extraction
	local selected
	selected=$(cat "$formatted_file" | fzf \
		--ansi \
		--no-hscroll \
		--height=80% \
		--layout=reverse \
		--border=rounded \
		--border-label=" Search All Fields " \
		--info=inline-right \
		--pointer="▸" \
		--prompt="❯❯ " \
		--header=" Enter: Select │ Ctrl-Y: Copy │ Ctrl-/: Preview │ Esc: Cancel " \
		--header-border=bottom \
		--delimiter=$'\t' \
		--with-nth=1 \
		--preview "$preview_cmd" \
		--preview-window="right,50%,wrap,border-rounded,<50(bottom,40%,wrap,border-rounded)" \
		--bind=ctrl-/:toggle-preview \
		--bind="ctrl-y:execute-silent(echo {} | cut -f2 | pbcopy)+bell" \
		--color=fg:#DDC7A1,bg:#1D2021,hl:#E78A4E \
		--color=fg+:#DDC7A1,bg+:#3C3836,hl+:#E78A4E:bold \
		--color=info:#928374,prompt:#E78A4E,pointer:#E78A4E \
		--color=marker:#A9B665,spinner:#E78A4E,header:#928374 \
		--color=border:#504945,label:#E78A4E \
		--color=preview-bg:#141617)

	# Cleanup
	rm -f "$merged_file" "$formatted_file"

	if [ -z "$selected" ]; then
		return 1
	fi

	# Extract the raw command (field 2 after tab delimiter)
	local cmd
	cmd=$(echo "$selected" | awk -F'\t' '{print $2}')

	if [ -z "$cmd" ]; then
		return 1
	fi

	# SECURITY: Validate that we extracted a command, not something dangerous
	# Ensure the command doesn't contain embedded newlines that could cause execution
	if [[ "$cmd" == *$'\n'* ]]; then
		echo "Error: Command contains newlines (potential security issue)" >&2
		return 1
	fi

	# CRITICAL SAFETY: This function ONLY returns the command string
	# It NEVER executes anything. Commands are only inserted into the buffer
	# and require explicit user confirmation (Enter key) to execute.

	# Copy to clipboard (macOS) - this is safe, just copies text
	echo -n "$cmd" | pbcopy

	# Return command (will be used by fz-cmd function to INSERT, not execute)
	echo "$cmd"
}

# Widget version - inserts command into command line
# SECURITY: This function ONLY inserts text into the command buffer.
# It NEVER executes commands. User must press Enter to execute.
fz-cmd-widget() {
	local cmd
	# Use localoptions to scope the nomatch setting
	setopt localoptions
	# Disable nomatch to prevent glob expansion errors when inserting commands
	setopt +o nomatch

	cmd=$(_fz-cmd-core)

	if [ $? -eq 0 ] && [ -n "$cmd" ]; then
		# SAFETY: LBUFFER only modifies the command line buffer
		# This does NOT execute anything. User must explicitly press Enter.
		# The command is inserted into the buffer for user review before execution.
		LBUFFER+="$cmd"
		# Position cursor at the end
		CURSOR=${#LBUFFER}
	else
		# If cancelled or error, reset the prompt
		zle reset-prompt
	fi
}
zle -N fz-cmd-widget

# Function version - can be called directly
# Type 'fz-cmd' to select a command and insert it into the command line
# SECURITY: This function ONLY inserts text into the command history/buffer.
# It NEVER executes commands. User must press Enter to execute.
fz-cmd() {
	local cmd
	# Temporarily disable nomatch to prevent glob expansion errors
	# This prevents "no matches found" errors when commands contain square brackets
	setopt localoptions
	setopt +o nomatch

	cmd=$(_fz-cmd-core)

	if [ $? -eq 0 ] && [ -n "$cmd" ]; then
		# SAFETY: print -z only adds the command to history and command line buffer
		# This does NOT execute anything. The command will appear on the next prompt
		# and requires explicit user confirmation (Enter key) to execute.
		# The -- prevents option parsing, and nomatch is disabled to prevent glob expansion
		print -z -- "$cmd"
	fi
}

# Debug/status function to see what's happening
fz-cmd-status() {
	echo "fz-cmd Configuration (refactored version):"
	echo "  Cache directory: $CACHE_DIR"
	echo "  Data limits:"
	echo "    Curated: ${FZ_CMD_LIMIT_CURATED:-1000}"
	echo "    Aliases: ${FZ_CMD_LIMIT_ALIAS:-100}"
	echo "    Functions: ${FZ_CMD_LIMIT_FUNCTION:-100}"
	echo "    History: ${FZ_CMD_LIMIT_HISTORY:-200}"
	echo "    tldr: ${FZ_CMD_LIMIT_TLDR:-500}"
	echo ""
	echo "To refresh caches: $FZ_CMD_DIR/scripts/refresh_cache.sh"
	echo "To include tldr: export FZ_CMD_INCLUDE_TLDR=1"
	echo "To set limits: export FZ_CMD_LIMIT_HISTORY=50"
}
