# Formatting and sorting functions for fz-cmd

_fz-cmd-format-output() {
	local parser_output="$1"
	local parser_dir="$HOME/.dotfiles/zsh/fz-cmd/parsers"

	# Format output with fixed-width columns
	local formatted_output
	formatted_output=$(echo "$parser_output" | awk -F'\t' -f "$parser_dir/format.awk")

	# Sort by recent usage: most recently used commands appear first
	local recent_order
	recent_order=$(_fz-cmd-get-recent-order)

	if [ -n "$recent_order" ]; then
		# Create a temporary file with recent order for awk to reference
		local recent_order_file
		recent_order_file=$(mktemp)
		echo "$recent_order" >"$recent_order_file"

		# Sort: commands in recent file first (in order), then others
		# Use LC_ALL=C to handle any byte sequence (including invalid UTF-8)
		formatted_output=$(echo "$formatted_output" | awk -F'\t' -v recent_file="$recent_order_file" -f "$parser_dir/sort-recent.awk" | LC_ALL=C sort -t$'\t' -k1,1n | LC_ALL=C cut -f2-)

		rm -f "$recent_order_file"
	fi

	echo "$formatted_output"
}

_fz-cmd-build-preview-cmd() {
	local parser_dir="$HOME/.dotfiles/zsh/fz-cmd/parsers"
	echo "echo {} | awk -F\"\\t\" -f $parser_dir/preview.awk"
}
