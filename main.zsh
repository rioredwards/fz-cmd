_fz-cmd-core() {
	local script_dir="${HOME}/.dotfiles/zsh/fz-cmd"
	local dedupe_script="${script_dir}/utils/deduplicate_with_tldr.py"
	local preview_script="${script_dir}/utils/preview_tldr.py"
	
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
			--read0
	)

	if [ -z "$selected" ]; then
		return 1
	fi

	# Extract command from tab-delimited format: <command>\t<tldr_content>
	# Field 1 is the command, field 2 is the tldr content (we only need field 1)
	local cmd
	cmd=$(echo -n "$selected" | cut -f1 | tr -d '\0')

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
