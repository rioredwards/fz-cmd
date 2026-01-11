_fz-cmd-core() {
	local script_dir="${HOME}/.dotfiles/zsh/fz-cmd"
	local dedupe_script="${script_dir}/utils/deduplicate_with_tldr.py"
	local preview_script="${script_dir}/utils/preview_tldr.py"
	
	# Debug mode: only file logging
	# Set FZ_CMD_DEBUG_LOG=1 to use default location, or FZ_CMD_DEBUG_LOG=/path/to/log for custom path
	local debug_log="${FZ_CMD_DEBUG_LOG:-}"
	if [ "$debug_log" = "1" ]; then
		debug_log="${script_dir}/debug.log"
	fi
	
	# Debug logging function - writes only to log file
	_fz-cmd-debug() {
		local phase="$1"
		local message="$2"
		local log_line="[${phase}] ${message}"
		
		if [ -n "$debug_log" ]; then
			echo "$log_line" >> "$debug_log"
		fi
	}
	
	# Helper to log data samples
	_fz-cmd-log-sample() {
		local phase="$1"
		local label="$2"
		local data="$3"
		local max_lines="${4:-5}"
		
		if [ -z "$debug_log" ]; then
			return
		fi
		
		_fz-cmd-debug "$phase" "=== $label ==="
		# Show first few entries, handling null-delimited data
		local sample=$(echo -n "$data" | tr '\0' '\n' | head -n "$max_lines")
		local line_num=1
		while IFS= read -r line; do
			# Truncate long lines for readability
			local truncated="${line:0:200}"
			if [ ${#line} -gt 200 ]; then
				truncated="${truncated}... (truncated)"
			fi
			_fz-cmd-debug "$phase" "  [$line_num] $truncated"
			line_num=$((line_num + 1))
		done <<< "$sample"
		_fz-cmd-debug "$phase" "=== End $label ==="
	}
	
	# Enable debug logging if requested
	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "INIT" "Starting fz-cmd-core"
		_fz-cmd-debug "INIT" "Script dir: $script_dir"
		_fz-cmd-debug "INIT" "Dedupe script: $dedupe_script"
		_fz-cmd-debug "INIT" "Preview script: $preview_script"
	fi
	
	# Phase 1: Get history from atuin
	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "PHASE1" "Fetching history from atuin..."
	fi
	
	local atuin_output
	atuin_output=$(atuin history list --format "{command}" --reverse=false --print0 2>/dev/null)
	local atuin_exit=$?
	
	if [ -n "$debug_log" ]; then
		if [ $atuin_exit -eq 0 ]; then
			# Count null-delimited entries correctly
			# Count null bytes (subtract 1 if output ends with null, or count all nulls)
			local cmd_count=0
			if [ -n "$atuin_output" ]; then
				# Use Python to reliably count null-delimited entries
				cmd_count=$(echo -n "$atuin_output" | python3 -c "import sys; data = sys.stdin.buffer.read(); print(len([x for x in data.split(b'\0') if x]))")
			fi
			_fz-cmd-debug "PHASE1" "Atuin returned $cmd_count commands (exit code: $atuin_exit)"
			_fz-cmd-debug "PHASE1" "Data format: null-delimited strings"
			_fz-cmd-debug "PHASE1" "Data size: ${#atuin_output} bytes"
			_fz-cmd-log-sample "PHASE1" "Sample atuin output (first 5 commands)" "$atuin_output" 5
		else
			_fz-cmd-debug "PHASE1" "Atuin failed with exit code: $atuin_exit"
		fi
	fi
	
	# Phase 2: Deduplicate and match with tldr
	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "PHASE2" "Processing through deduplicate_with_tldr.py..."
		_fz-cmd-debug "PHASE2" "Input format: null-delimited commands"
		_fz-cmd-debug "PHASE2" "Expected output format: null-delimited, tab-separated <command>\\t<tldr_content>"
	fi
	
	local dedupe_output
	dedupe_output=$(echo -n "$atuin_output" | python3 "$dedupe_script")
	local dedupe_exit=$?
	
	if [ -n "$debug_log" ]; then
		if [ $dedupe_exit -eq 0 ]; then
			# Count null-delimited entries correctly
			# Use Python to reliably count null-delimited entries
			local dedupe_count=0
			if [ -n "$dedupe_output" ]; then
				dedupe_count=$(echo -n "$dedupe_output" | python3 -c "import sys; data = sys.stdin.buffer.read(); print(len([x for x in data.split(b'\0') if x]))")
			fi
			_fz-cmd-debug "PHASE2" "Deduplication returned $dedupe_count entries (exit code: $dedupe_exit)"
			_fz-cmd-debug "PHASE2" "Data size: ${#dedupe_output} bytes"
			_fz-cmd-debug "PHASE2" "Output format: null-delimited, tab-separated entries"
			_fz-cmd-log-sample "PHASE2" "Sample dedupe output (first 3 entries)" "$dedupe_output" 3
			
			# Show structure of first entry in detail
			if [ -n "$dedupe_output" ]; then
				local first_entry=$(echo -n "$dedupe_output" | awk 'BEGIN {RS="\0"} NR==1 {print; exit}')
				if [ -n "$first_entry" ]; then
					_fz-cmd-debug "PHASE2" "First entry structure:"
					local cmd_part=$(echo -n "$first_entry" | cut -f1)
					local tldr_part=$(echo -n "$first_entry" | cut -f2-)
					_fz-cmd-debug "PHASE2" "  Command part: ${cmd_part:0:100}..."
					_fz-cmd-debug "PHASE2" "  TLDR part length: ${#tldr_part} chars"
					if [ ${#tldr_part} -gt 0 ]; then
						_fz-cmd-debug "PHASE2" "  TLDR preview: ${tldr_part:0:150}..."
					else
						_fz-cmd-debug "PHASE2" "  TLDR part: (empty)"
					fi
				fi
			fi
		else
			_fz-cmd-debug "PHASE2" "Deduplication failed with exit code: $dedupe_exit"
		fi
	fi
	
	# Phase 3: fzf selection
	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "PHASE3" "Launching fzf for user selection..."
		_fz-cmd-debug "PHASE3" "fzf config: delimiter=tab, with-nth=1 (show only command), preview=field 2 (tldr content)"
		_fz-cmd-debug "PHASE3" "Preview script: $preview_script"
	fi
	
	local selected
	selected=$(echo -n "$dedupe_output" | fzf \
		--ansi \
		--no-hscroll \
		--height=80% \
		--layout=reverse \
		--border=rounded \
		--border-label=" Command History " \
		--info=inline-right \
		--pointer="▸" \
		--prompt="❯ " \
		--header=" Enter: Select │ Ctrl-/: Preview │ Esc: Cancel " \
		--header-border=bottom \
		--delimiter=$'\t' \
		--with-nth=1 \
		--preview="$preview_script {2}" \
		--preview-window="right,50%,wrap,border-rounded" \
		--bind="ctrl-/:toggle-preview" \
		--color=fg:#DDC7A1,bg:#1D2021,hl:#E78A4E \
		--color=fg+:#DDC7A1,bg+:#3C3836,hl+:#E78A4E:bold \
		--color=info:#928374,prompt:#E78A4E,pointer:#E78A4E \
		--color=marker:#A9B665,spinner:#E78A4E,header:#928374 \
		--color=border:#504945,label:#E78A4E \
		--color=preview-bg:#141617 \
		--read0)
	local fzf_exit=$?
	
	if [ -n "$debug_log" ]; then
		if [ $fzf_exit -eq 0 ] && [ -n "$selected" ]; then
			_fz-cmd-debug "PHASE3" "User selected command (fzf exit code: $fzf_exit)"
			_fz-cmd-debug "PHASE3" "Selected entry structure:"
			local selected_cmd=$(echo -n "$selected" | cut -f1)
			local selected_tldr=$(echo -n "$selected" | cut -f2-)
			_fz-cmd-debug "PHASE3" "  Command: ${selected_cmd:0:150}..."
			_fz-cmd-debug "PHASE3" "  TLDR length: ${#selected_tldr} chars"
			if [ ${#selected_tldr} -gt 0 ]; then
				_fz-cmd-debug "PHASE3" "  TLDR preview: ${selected_tldr:0:200}..."
			else
				_fz-cmd-debug "PHASE3" "  TLDR: (empty)"
			fi
		elif [ $fzf_exit -eq 130 ]; then
			_fz-cmd-debug "PHASE3" "User cancelled (ESC pressed, exit code: $fzf_exit)"
		else
			_fz-cmd-debug "PHASE3" "No selection made (exit code: $fzf_exit)"
		fi
	fi

	if [ -z "$selected" ]; then
		if [ -n "$debug_log" ]; then
			_fz-cmd-debug "PHASE4" "No selection, exiting"
		fi
		return 1
	fi

	# Phase 4: Extract and process command
	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "PHASE4" "Extracting command from selection..."
		_fz-cmd-debug "PHASE4" "Input format: tab-delimited <command>\\t<tldr_content>"
	fi

	# Extract command from tab-delimited format: <command>\t<tldr_content>
	# Field 1 is the command, field 2 is the tldr content (we only need field 1)
	local cmd
	cmd=$(echo -n "$selected" | cut -f1 | tr -d '\0')
	
	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "PHASE4" "Extracted command (before processing): ${cmd:0:150}..."
		_fz-cmd-debug "PHASE4" "Command length: ${#cmd} chars"
	fi

	# Convert multiline commands to single-line by replacing newlines with semicolons
	# This preserves command structure while making it safe for prompt insertion
	if [[ "$cmd" == *$'\n'* ]]; then
		if [ -n "$debug_log" ]; then
			_fz-cmd-debug "PHASE4" "Command contains newlines, converting to single line..."
		fi
		# Replace newlines with semicolons and clean up whitespace
		cmd=$(echo "$cmd" | tr '\n' ';' | sed 's/;;*/;/g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/;$//')
	fi

	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "PHASE4" "Final command: ${cmd:0:150}..."
		_fz-cmd-debug "PHASE4" "Final command length: ${#cmd} chars"
		_fz-cmd-debug "PHASE4" "Copying to clipboard..."
	fi

	echo -n "$cmd" | pbcopy

	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "PHASE4" "Command copied, outputting to stdout"
		_fz-cmd-debug "DONE" "fz-cmd-core completed successfully"
	fi

	echo "$cmd"
}

# Function version - can be called directly
# Type 'fz-cmd' to select a command and insert it into the command line
# SECURITY: This function ONLY inserts text into the command history/buffer.
# It NEVER executes commands. User must press Enter to execute.
fz-cmd() {
	local script_dir="${HOME}/.dotfiles/zsh/fz-cmd"
	
	# Debug mode: only file logging
	# Set FZ_CMD_DEBUG_LOG=1 to use default location, or FZ_CMD_DEBUG_LOG=/path/to/log for custom path
	local debug_log="${FZ_CMD_DEBUG_LOG:-}"
	if [ "$debug_log" = "1" ]; then
		debug_log="${script_dir}/debug.log"
	fi
	
	# Debug logging function (only to file)
	_fz-cmd-debug() {
		local phase="$1"
		local message="$2"
		local log_line="[${phase}] ${message}"
		
		if [ -n "$debug_log" ]; then
			echo "$log_line" >> "$debug_log"
		fi
	}
	
	if [ -n "$debug_log" ]; then
		_fz-cmd-debug "WRAPPER" "fz-cmd function called"
	fi
	
	local cmd
	# Temporarily disable nomatch to prevent glob expansion errors
	# This prevents "no matches found" errors when commands contain square brackets
	setopt localoptions
	setopt +o nomatch

	cmd=$(_fz-cmd-core)
	local exit_code=$?

	if [ -n "$debug_log" ]; then
		if [ $exit_code -eq 0 ] && [ -n "$cmd" ]; then
			_fz-cmd-debug "WRAPPER" "Inserting command into buffer: ${cmd:0:150}..."
		else
			_fz-cmd-debug "WRAPPER" "No command to insert (exit code: $exit_code, cmd empty: $([ -z "$cmd" ] && echo 'yes' || echo 'no'))"
		fi
	fi

	if [ $exit_code -eq 0 ] && [ -n "$cmd" ]; then
		print -z -- "$cmd"
	fi
}
