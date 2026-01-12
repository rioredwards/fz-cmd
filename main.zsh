DIM="\033[38;2;29;32;33m"  # RGB(29,32,33) = #1D2021 - matches fzf bg
RESET="\033[0m"

_fz-cmd-core() {
	# Set shell options: disable glob substitution, use zsh builtins, enable pipefail, disable aliases
	setopt localoptions noglobsubst noposixbuiltins pipefail no_aliases 2>/dev/null

	# gets the first word of the command and passes it to tldr with fancy formatting
	local preview_script="cmd=\$(echo {2} | awk '{print \$1}'); printf '\033[1;38;5;208m━━━ Command: %s ━━━\033[0m\n' \"\$cmd\"; tldr --color=always \"\$cmd\" 2>/dev/null || printf '\033[33m\nNo tldr page found for '\''%s'\''\033[0m\n' \"\$cmd\""

	local atuin_opts="--format $'\033[38;5;208m{relativetime}\033[0m\t{command}'"
	# Array of fzf options
	local fzf_opts=(
			--ansi \
			--no-hscroll \
			--with-nth='{1} - {2}' \
			--accept-nth="2" \
			--nth='1' \
			--layout=reverse \
			--delimiter=$'\t' \
			--border=rounded \
			--border-label=" Command History " \
			--info=inline-right \
			--pointer="▸" \
			--prompt="❯ " \
			--header=" Enter: Select │ Ctrl-/: Preview │ Ctrl-d: Directory Filter │ Ctrl-r: Reload │ Esc: Cancel " \
			--header-border=bottom \
			# Set fzf height (80% if FZF_TMUX_HEIGHT is unset)
			--height=${FZF_TMUX_HEIGHT:-80%}
			# Reverse order (newest first)
			--tac
			# Break ties by original order
			--tiebreak=index
			# Enable fzf's history feature
			--history="${HOME}/.dotfiles/.fz-cmd-recent"
			# Pre-fill fzf with current command line buffer
			"--query=${LBUFFER}"
			# Disable multi-select
			"+m"
			# Keybindings: Ctrl+D reloads with current directory filter, Ctrl+R reloads without filter
			"--bind=ctrl-d:reload(atuin search $atuin_opts -c $PWD | awk -F'\t' '{match(\$1, /\\033\\[[0-9;]*m/); ansi_start = substr(\$1, 1, RLENGTH); text = substr(\$1, RLENGTH + 1); match(text, /\\033\\[0m/); if (RLENGTH > 0) {ansi_end = substr(text, RSTART, RLENGTH); text = substr(text, 1, RSTART - 1) substr(text, RSTART + RLENGTH)} else {ansi_end = \"\"}; printf \"%s%-10s%s\t%s\n\", ansi_start, text, ansi_end, \$2}'),ctrl-r:reload(atuin search $atuin_opts | awk -F'\t' '{match(\$1, /\\033\\[[0-9;]*m/); ansi_start = substr(\$1, 1, RLENGTH); text = substr(\$1, RLENGTH + 1); match(text, /\\033\\[0m/); if (RLENGTH > 0) {ansi_end = substr(text, RSTART, RLENGTH); text = substr(text, 1, RSTART - 1) substr(text, RSTART + RLENGTH)} else {ansi_end = \"\"}; printf \"%s%-10s%s\t%s\n\", ansi_start, text, ansi_end, \$2}')"
			
			--color=fg:#DDC7A1,bg:#1D2021,hl:#E78A4E \
			--color=fg+:#DDC7A1,bg+:#3C3836,hl+:#E78A4E:bold \
			--color=info:#928374,prompt:#E78A4E,pointer:#E78A4E \
			--color=marker:#A9B665,spinner:#E78A4E,header:#928374 \
			--color=border:#504945,label:#E78A4E \
			--color=preview-bg:#141617 \
			# toggle preview with ctrl-/
			--bind="ctrl-/:toggle-preview" \

			# --bind "?:preview:${preview_script}" \
			--preview="$preview_script" \
			--preview-window="right,50%,wrap,border-rounded,<50(bottom,40%,wrap,border-rounded)" \
	)

	# Run Atuin search, pipe to fzf, store selected command
	selected=$(
			eval "atuin search ${atuin_opts}" |
					awk -F'\t' '{
						# Extract ANSI codes and text from field 1
						match($1, /\033\[[0-9;]*m/)
						ansi_start = substr($1, 1, RLENGTH)
						text = substr($1, RLENGTH + 1)
						match(text, /\033\[0m/)
						if (RLENGTH > 0) {
							ansi_end = substr(text, RSTART, RLENGTH)
							text = substr(text, 1, RSTART - 1) substr(text, RSTART + RLENGTH)
						} else {
							ansi_end = ""
						}
						# Pad text to 10 characters, then reconstruct with ANSI codes
						printf "%s%-10s%s\t%s\n", ansi_start, text, ansi_end, $2
					}' |
					fzf "${fzf_opts[@]}"
	)
	# Save fzf's exit code
	local ret=$?
	# If a command was selected, append it to the left buffer (inserts at cursor position)
	if [ -n "$selected" ]; then
			# the += lets it insert at current pos instead of replacing
			LBUFFER+="${selected}"
	fi

	# Refresh the prompt display
	# zle reset-prompt
	# Return fzf's exit code
	echo $selected
}

# Function version - can be called directly
# Type 'fz-cmd' to select a command and insert it into the command line
# SECURITY: This function ONLY inserts text into the command history/buffer.
# It NEVER executes commands. User must press Enter to execute.
fz-cmd() {
	local script_dir="${HOME}/.dotfiles/zsh/fz-cmd"

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
