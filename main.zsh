DIM="\033[38;2;29;32;33m"  # RGB(29,32,33) = #1D2021 - matches fzf bg
RESET="\033[0m"

_fz-cmd-core() {
	# Set shell options: disable glob substitution, use zsh builtins, enable pipefail, disable aliases
	setopt localoptions noglobsubst noposixbuiltins pipefail no_aliases 2>/dev/null

	# gets the first word of the command and passes it to tldr with fancy formatting
	local preview_script="cmd=\$(echo {2} | awk '{print \$1}'); printf '\033[1;38;5;208m━━━ Command: %s ━━━\033[0m\n' \"\$cmd\"; tldr --color=always \"\$cmd\" 2>/dev/null || printf '\033[33m\nNo tldr page found for '\''%s'\''\033[0m\n' \"\$cmd\""

	local atuin_opts="--print0 --format '{relativetime}\t{command}'"
	# Array of fzf options
	local fzf_opts=(
			--ansi \
			--read0 \
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
			--height=${FZF_TMUX_HEIGHT:-40%}
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
			"--bind=ctrl-d:reload(atuin search $atuin_opts -c $PWD | perl -0ne 'chomp; my (\$t, \$cmd) = split(/\\t/, \$_, 2); if (defined \$cmd) { my \$time_text = \$t; \$time_text =~ s/\\033\\[[0-9;]*m//g; my \$padded_text = sprintf(\"%-10s\", \$time_text); my \$orange = \"\\033[38;5;208m\"; my \$reset = \"\\033[0m\"; printf \"%s%s%s\\t%s\\0\", \$orange, \$padded_text, \$reset, \$cmd; } else { print \$_, \"\\0\"; }'),ctrl-r:reload(atuin search $atuin_opts | perl -0ne 'chomp; my (\$t, \$cmd) = split(/\\t/, \$_, 2); if (defined \$cmd) { my \$time_text = \$t; \$time_text =~ s/\\033\\[[0-9;]*m//g; my \$padded_text = sprintf(\"%-10s\", \$time_text); my \$orange = \"\\033[38;5;208m\"; my \$reset = \"\\033[0m\"; printf \"%s%s%s\\t%s\\0\", \$orange, \$padded_text, \$reset, \$cmd; } else { print \$_, \"\\0\"; }')"
			
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
					perl -0ne '
						chomp;                           # remove trailing NUL for this record
						my ($t, $cmd) = split(/\t/, $_, 2);

						if (defined $cmd) {
							# Strip ANSI codes from time field to get actual text length
							my $time_text = $t;
							$time_text =~ s/\033\[[0-9;]*m//g;  # Remove ANSI codes
							
							# Pad the actual text (without ANSI codes) to 10 chars
							my $padded_text = sprintf("%-10s", $time_text);
							
							# Add ANSI color codes around the padded text
							my $orange = "\033[38;5;208m";
							my $reset = "\033[0m";
							printf "%s%s%s\t%s\0", $orange, $padded_text, $reset, $cmd;
						} else {
							# if no tab found, pass record through unchanged
							print $_, "\0";
						}
					' |
					fzf "${fzf_opts[@]}"
	)
	# Save fzf's exit code
	local ret=$?
	
	# Return the selected command (caller will handle LBUFFER or printing)
	echo "$selected"
	return $ret
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

# Zsh widget for down arrow key - triggers fz-cmd when appropriate
fz-cmd-down-widget() {
	# If command line is empty or we're at the end of history, trigger fz-cmd
	if [[ -z "$BUFFER" ]] || [[ "$HISTNO" -eq $HISTSIZE ]]; then
		# Call fz-cmd as a widget
		fz-cmd-widget
	else
		# Fall back to normal down arrow behavior
		zle .down-line-or-history
	fi
}

# Zsh widget wrapper for fz-cmd
fz-cmd-widget() {
	local cmd
	# Temporarily disable nomatch to prevent glob expansion errors
	setopt localoptions
	setopt +o nomatch

	cmd=$(_fz-cmd-core)
	local exit_code=$?

	if [ $exit_code -eq 0 ] && [ -n "$cmd" ]; then
		# Insert the command into the buffer at cursor position
		LBUFFER+="$cmd"
		zle reset-prompt
	fi
	return $exit_code
}

# Register the widgets
zle -N fz-cmd-widget
zle -N fz-cmd-down-widget

# Bind down arrow to the smart widget
# This will trigger fz-cmd when the line is empty or at history end
bindkey '^[[B' fz-cmd-down-widget
bindkey '^[OB' fz-cmd-down-widget  # Also handle different terminal escape sequences
