# YAML parser functions for fz-cmd
# Uses Python with PyYAML for reliable parsing

_fz-cmd-parse-yaml() {
	local commands_file="$1"
	local parser_dir="$HOME/.dotfiles/zsh/fz-cmd/parsers"
	local parser_output

	if ! command -v python3 &>/dev/null; then
		echo "Error: python3 not found. Please install Python 3." >&2
		return 1
	fi

	if ! python3 -c "import yaml" 2>/dev/null; then
		echo "Error: PyYAML is required. Install with: pip install pyyaml" >&2
		return 1
	fi

	parser_output=$(python3 "$parser_dir/parse-yaml.py" "$commands_file" 2>&1)
	local exit_code=$?

	if [ $exit_code -ne 0 ] || [ -z "$parser_output" ]; then
		echo "Error: Failed to parse $commands_file" >&2
		if [ -n "$parser_output" ]; then
			echo "$parser_output" >&2
		fi
		return 1
	fi

	echo "$parser_output"
}
