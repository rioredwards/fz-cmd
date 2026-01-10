_fz-cmd-core() {
	local script_dir="${HOME}/.dotfiles/zsh/fz-cmd"
	local dedupe_script="${script_dir}/utils/deduplicate_history.py"
	
	local selected
	selected=$(
		atuin history list --format "{command}" --reverse=false --print0 2>/dev/null |
			python3 "$dedupe_script" |
			fzf \
				--ansi \
				--no-hscroll \
				--height=80% \
				--layout=reverse \
				--border=rounded \
				--border-label=" Command History " \
				--info=inline-right \
				--pointer="▸" \
				--prompt="❯ " \
				--header=" Enter: Select │ Esc: Cancel " \
				--header-border=bottom \
				--color=fg:#DDC7A1,bg:#1D2021,hl:#E78A4E \
				--color=fg+:#DDC7A1,bg+:#3C3836,hl+:#E78A4E:bold \
				--color=info:#928374,prompt:#E78A4E,pointer:#E78A4E \
				--color=marker:#A9B665,spinner:#E78A4E,header:#928374 \
				--color=border:#504945,label:#E78A4E \
				--color=preview-bg:#141617 \
				--read0
		# --preview "$preview_cmd" \
		# --preview-window="right,50%,wrap,border-rounded,<50(bottom,40%,wrap,border-rounded)" \
		# --bind=ctrl-/:toggle-preview \
		# --bind="ctrl-y:execute-silent(echo {} | cut -f2 | pbcopy)+bell" \
	)

	if [ -z "$selected" ]; then
		return 1
	fi

	# Since atuin outputs raw commands (not tab-separated), $selected IS the command
	# Remove any trailing null bytes that might have been preserved
	local cmd
	cmd=$(echo -n "$selected" | tr -d '\0')

	# SECURITY: Validate that we extracted a command, not something dangerous
	# Ensure the command doesn't contain embedded newlines that could cause execution
	if [[ "$cmd" == *$'\n'* ]]; then
		echo "Error: Command contains newlines (potential security issue)" >&2
		return 1
	fi

	echo -n "$cmd" | pbcopy

	echo "$cmd"
}

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
		print -z -- "$cmd"
	fi
}
