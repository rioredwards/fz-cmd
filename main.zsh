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
	
	# Timing helper - just log directly
	_fz-cmd-timing() {
		local label="$1"
		local start_time="$2"
		local debug_log="$3"
		if [ -z "$debug_log" ]; then
			echo "$(date +%s.%N)"
			return
		fi
		local end_time=$(date +%s.%N)
		local duration=$(python3 -c "print($end_time - $start_time)" 2>/dev/null)
		if [ -n "$duration" ]; then
			echo "[TIMING] ${label}: ${duration}s" >> "$debug_log"
		fi
		echo "$end_time"
	}
	
	# Simple function to filter log to top 4 timings
	_filter_top_timings() {
		local debug_log="$1"
		if [ -z "$debug_log" ] || [ ! -f "$debug_log" ]; then
			return
		fi
		# Extract all timing lines, sort by duration, keep top 4, replace in file
		python3 <<EOF
import re

try:
    with open("$debug_log", "r") as f:
        lines = f.readlines()
    
    timings = []
    other_lines = []
    
    for line in lines:
        match = re.match(r'\[TIMING\]\s+([^:]+):\s+([\d.]+)s', line)
        if match:
            label = match.group(1).strip()
            duration = float(match.group(2))
            timings.append((duration, label))
        else:
            other_lines.append(line)
    
    # Sort by duration descending, take top 4
    timings.sort(reverse=True)
    top_timings = timings[:4]
    
    # Rewrite file
    with open("$debug_log", "w") as f:
        for line in other_lines:
            f.write(line)
        for duration, label in top_timings:
            f.write(f"[TIMING] {label}: {duration:.9f}s\n")
except:
    pass
EOF
	}
	
	local start_total=$(date +%s.%N)
	
	# if [ -n "$debug_log" ]; then
	# 	echo "[TIMING] Starting performance measurement" >> "$debug_log"
	# 	echo "[TIMING] debug_log path: $debug_log" >> "$debug_log"
	# fi
	
	local start_atuin=$(date +%s.%N)
	local atuin_output
	atuin_output=$(atuin history list --format "{command}" --reverse=false --print0 2>/dev/null)
	local atuin_exit=$?
	local start_atuin_end=$(_fz-cmd-timing "atuin_history" "$start_atuin" "$debug_log")
	
	# if [ -n "$debug_log" ]; then
	# 	echo "=== atuin_output (first 10 entries) ===" >> "$debug_log"
	# 	if [ -n "$atuin_output" ]; then
	# 		echo -n "$atuin_output" | python3 -c "import sys; data = sys.stdin.buffer.read(); entries = [x for x in data.split(b'\0') if x][:10]; [print(x.decode('utf-8', errors='replace')) for x in entries]" >> "$debug_log"
	# 	fi
	# 	echo "" >> "$debug_log"
	# fi
	
	local start_aliases=$(date +%s.%N)
	# TEMPORARILY DISABLED: Collect aliases: format as name=value, one per line
	local aliases_data=""
	# if command -v alias >/dev/null 2>&1; then
	# 	aliases_data=$(alias 2>/dev/null | sed -E "s/^alias //" | while IFS= read -r alias_line; do
	# 		if [ -z "$alias_line" ]; then
	# 			continue
	# 		fi
	# 		# Extract name and value
	# 		local alias_name alias_value
	# 		if echo "$alias_line" | grep -qE "^[^=]+='.*'$"; then
	# 			alias_name=$(echo "$alias_line" | sed -E "s/='.*'$//")
	# 			alias_value=$(echo "$alias_line" | sed -E "s/^[^=]+='(.*)'$/\1/")
	# 		elif echo "$alias_line" | grep -qE '^[^=]+=".*"$'; then
	# 			alias_name=$(echo "$alias_line" | sed -E 's/=".*"$//')
	# 			alias_value=$(echo "$alias_line" | sed -E 's/^[^=]+="(.*)"$/\1/')
	# 		else
	# 			alias_name=$(echo "$alias_line" | sed -E 's/=[^=]*$//')
	# 			alias_value=$(echo "$alias_line" | sed -E 's/^[^=]+=//')
	# 		fi
	# 		if [ -n "$alias_name" ] && [ -n "$alias_value" ]; then
	# 			echo "${alias_name}=${alias_value}"
	# 		fi
	# 	done)
	# fi
	local start_aliases_end=$(_fz-cmd-timing "alias_collection" "$start_aliases" "$debug_log")
	
	local start_functions=$(date +%s.%N)
	# TEMPORARILY DISABLED: Collect functions: name=body, one per line
	local functions_data=""
	# functions_data=$(print -l ${(k)functions} 2>/dev/null | grep -E '^[a-zA-Z_][a-zA-Z0-9_-]*$' | sort -u | while IFS= read -r func_name; do
	# 	if [ -z "$func_name" ]; then
	# 		continue
	# 	fi
	# 	# Get function body using 'functions' associative array
	# 	local func_body="${functions[$func_name]}"
	# 	if [ -n "$func_body" ]; then
	# 		# Replace newlines with semicolons for single-line output
	# 		func_body=$(echo "$func_body" | tr '\n' ';' | sed 's/;;*/;/g' | sed 's/;$//')
	# 		echo "${func_name}=${func_body}"
	# 	fi
	# done)
	local start_functions_end=$(_fz-cmd-timing "function_collection" "$start_functions" "$debug_log")
	
	local start_python=$(date +%s.%N)
	local dedupe_output
	if [ -n "$debug_log" ]; then
		dedupe_output=$(echo -n "$atuin_output" | FZ_CMD_ALIASES="$aliases_data" FZ_CMD_FUNCTIONS="$functions_data" FZ_CMD_DEBUG_LOG="$debug_log" python3 "$dedupe_script" 2>>"$debug_log")
	else
		dedupe_output=$(echo -n "$atuin_output" | FZ_CMD_ALIASES="$aliases_data" FZ_CMD_FUNCTIONS="$functions_data" python3 "$dedupe_script")
	fi
	local dedupe_exit=$?
	local start_python_end=$(_fz-cmd-timing "python_processing" "$start_python" "$debug_log")
	
	# if [ -n "$debug_log" ]; then
	# 	echo "=== dedupe_output (first 10 entries) ===" >> "$debug_log"
	# 	if [ -n "$dedupe_output" ]; then
	# 		echo -n "$dedupe_output" | python3 -c "import sys; data = sys.stdin.buffer.read(); entries = [x for x in data.split(b'\0') if x][:10]; [print(x.decode('utf-8', errors='replace')) for x in entries]" >> "$debug_log"
	# 	fi
	# 	echo "" >> "$debug_log"
	# fi

	# Filter to top 4 timings before fzf (which is interactive)
	_filter_top_timings "$debug_log"

		# Log total time and separator
	_fz-cmd-timing "total" "$start_total" "$debug_log" >/dev/null
	if [ -n "$debug_log" ]; then
		echo "--------------------------------" >> "$debug_log"
	fi
	
	local start_fzf=$(date +%s.%N)
	local cmd
	cmd=$(echo -n "$dedupe_output" | fzf \
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
		--accept-nth=1 \
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
	# local start_fzf_end=$(_fz-cmd-timing "fzf_launch" "$start_fzf" "$debug_log")

	
	if [ -z "$cmd" ]; then
		return 1
	fi

	# Convert multiline commands to single-line by replacing newlines with semicolons
	# This preserves command structure while making it safe for prompt insertion
	if [[ "$cmd" == *$'\n'* ]]; then
		# Replace newlines with semicolons and clean up whitespace
		cmd=$(echo "$cmd" | tr '\n' ';' | sed 's/;;*/;/g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/;$//')
	fi

	echo -n "$cmd" | pbcopy

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
	
	local cmd
	# Temporarily disable nomatch to prevent glob expansion errors
	# This prevents "no matches found" errors when commands contain square brackets
	setopt localoptions
	setopt +o nomatch

	cmd=$(_fz-cmd-core)
	local exit_code=$?

	if [ $exit_code -eq 0 ] && [ -n "$cmd" ]; then
		print -z -- "$cmd"
	fi
}
