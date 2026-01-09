# Shell functions and aliases integration for fz-cmd

# Enable/disable functions/aliases integration (set FZ_CMD_ENABLE_FUNCTIONS_ALIASES=0 to disable)
: ${FZ_CMD_ENABLE_FUNCTIONS_ALIASES:=1}

# Get shell functions and aliases
# Returns tab-separated: command\tdescription\ttags\texamples
_fz-cmd-get-functions-aliases() {
	# Check if integration is enabled
	if [ "${FZ_CMD_ENABLE_FUNCTIONS_ALIASES:-1}" != "1" ]; then
		return 0
	fi

	# Collect functions: use zsh's functions associative array keys
	local functions_list
	# In zsh, ${(k)functions} gets all function names (keys of the functions array)
	functions_list=$(print -l ${(k)functions} 2>/dev/null | grep -E '^[a-zA-Z_][a-zA-Z0-9_]*$' | sort -u)

	# Collect aliases: use alias | sed -E "s/alias //" as requested
	# This gives us lines like: name='value' or name="value" or name=value
	local aliases_list
	if command -v alias >/dev/null 2>&1; then
		aliases_list=$(alias 2>/dev/null | sed -E "s/alias //" | sort -u)
	fi

	# Process functions
	if [ -n "$functions_list" ]; then
		while IFS= read -r func_name; do
			if [ -z "$func_name" ]; then
				continue
			fi

			# Use function name as the command
			local cmd="$func_name"
			local desc="🔧 Function: $func_name"
			local tags="function $func_name"

			# Output in tab-separated format: command\tdescription\ttags\texamples
			echo -e "${cmd}\t${desc}\t${tags}\t"
		done <<EOF
$functions_list
EOF
	fi

	# Process aliases
	if [ -n "$aliases_list" ]; then
		while IFS= read -r alias_line; do
			if [ -z "$alias_line" ]; then
				continue
			fi

			# Extract alias name and value
			# Format: name='value' or name="value" or name=value
			local alias_name
			local alias_value

			# Try to extract name and value using a more robust approach
			# First, try to match quoted values (single or double)
			if echo "$alias_line" | grep -qE "^[^=]+='.*'$"; then
				# Format: name='value' (single quotes)
				alias_name=$(echo "$alias_line" | sed -E "s/='.*'$//")
				alias_value=$(echo "$alias_line" | sed -E "s/^[^=]+='(.*)'$/\1/")
			elif echo "$alias_line" | grep -qE '^[^=]+=".*"$'; then
				# Format: name="value" (double quotes)
				alias_name=$(echo "$alias_line" | sed -E 's/=".*"$//')
				alias_value=$(echo "$alias_line" | sed -E 's/^[^=]+="(.*)"$/\1/')
			else
				# Format: name=value (no quotes) - take everything after first =
				alias_name=$(echo "$alias_line" | sed -E 's/=[^=]*$//')
				alias_value=$(echo "$alias_line" | sed -E 's/^[^=]+=//')
			fi

			# Skip if we couldn't extract a name
			if [ -z "$alias_name" ]; then
				continue
			fi

			# Use alias value as the command (what gets executed)
			# If no value extracted, use the alias name itself
			local cmd="${alias_value:-$alias_name}"
			local desc="🔧 Alias: $alias_name"
			local tags="alias $alias_name"

			# Output in tab-separated format: command\tdescription\ttags\texamples
			echo -e "${cmd}\t${desc}\t${tags}\t"
		done <<EOF
$aliases_list
EOF
	fi
}

