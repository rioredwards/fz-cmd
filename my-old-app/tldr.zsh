# tldr integration for fz-cmd
# Uses cached YAML file for performance

# Enable/disable tldr integration (default: 1 - always loaded, use "?" to filter)
# Set FZ_CMD_ENABLE_TLDR=0 to disable tldr commands entirely
: ${FZ_CMD_ENABLE_TLDR:=1}

# Get all tldr entries from cached YAML file
# Returns tab-separated: command\tdescription\ttags\texamples
_fz-cmd-get-all-tldr-entries() {
	# Check if tldr integration is enabled
	if [ "${FZ_CMD_ENABLE_TLDR:-1}" != "1" ]; then
		return 0
	fi

	local tldr_cache_file="${HOME}/.dotfiles/zsh/fz-cmd/tldr-commands.yaml"

	# Check if cache file exists
	if [ ! -f "$tldr_cache_file" ]; then
		# Cache doesn't exist, try to generate it
		local generate_script="${HOME}/.dotfiles/zsh/fz-cmd/generate-tldr-cache.py"
		if [ -f "$generate_script" ] && command -v python3 >/dev/null 2>&1; then
			# Generate cache in background (non-blocking)
			python3 "$generate_script" >/dev/null 2>&1 &
		fi
		return 0
	fi

	# Parse cached YAML file using the same parser as commands.yaml
	_fz-cmd-parse-yaml "$tldr_cache_file"
}

# Function to refresh tldr cache
# Usage: fz-cmd-refresh-tldr [--limit N]  (limit to first N pages for faster iteration)
fz-cmd-refresh-tldr() {
	local generate_script="${HOME}/.dotfiles/zsh/fz-cmd/generate-tldr-cache.py"

	if [ ! -f "$generate_script" ]; then
		echo "Error: generate-tldr-cache.py not found" >&2
		return 1
	fi

	if ! command -v python3 >/dev/null 2>&1; then
		echo "Error: python3 not found" >&2
		return 1
	fi

	# Check if --limit is in arguments
	local has_limit=0
	for arg in "$@"; do
		if [ "$arg" = "--limit" ]; then
			has_limit=1
			break
		fi
	done

	if [ $has_limit -eq 1 ]; then
		echo "Generating tldr cache (limited sample)..." >&2
	else
		echo "Generating tldr cache (this may take a minute)..." >&2
	fi

	# Pass all arguments to the Python script
	python3 "$generate_script" "$@"
}
