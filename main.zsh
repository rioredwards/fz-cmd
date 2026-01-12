_fz-cmd-core() {
	# Set shell options: disable glob substitution, use zsh builtins, enable pipefail, disable aliases
	setopt localoptions noglobsubst noposixbuiltins pipefail no_aliases 2>/dev/null

	local atuin_opts="--cmd-only"
	# Array of fzf options
	local fzf_opts=(
			# Set fzf height (80% if FZF_TMUX_HEIGHT is unset)
			--height=${FZF_TMUX_HEIGHT:-80%}
			# Reverse order (newest first)
			--tac
			# Search from column 2 onwards (skip time column)
			"-n2..,.."
			# Break ties by original order
			--tiebreak=index
			# Enable fzf's history feature
			"--history"
			# Pre-fill fzf with current command line buffer
			"--query=${LBUFFER}"
			# Disable multi-select
			"+m"
			# Keybindings: Ctrl+D reloads with current directory filter, Ctrl+R reloads without filter
			"--bind=ctrl-d:reload(atuin search $atuin_opts -c $PWD),ctrl-r:reload(atuin search $atuin_opts)"
	)

	# Run Atuin search, pipe to fzf, store selected command
	selected=$(
			eval "atuin search ${atuin_opts}" |
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
