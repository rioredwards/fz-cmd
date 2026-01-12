# Usage: atuin search [OPTIONS] [QUERY]...

# Arguments:
#   [QUERY]...  

# Options:
#   -c, --cwd <CWD>                      Filter search result by directory
#       --exclude-cwd <EXCLUDE_CWD>      Exclude directory from results
#   -e, --exit <EXIT>                    Filter search result by exit code
#       --exclude-exit <EXCLUDE_EXIT>    Exclude results with this exit code
#   -b, --before <BEFORE>                Only include results added before this date
#       --after <AFTER>                  Only include results after this date
#       --limit <LIMIT>                  How many entries to return at most
#       --offset <OFFSET>                Offset from the start of the results
#   -i, --interactive                    Open interactive search UI
#       --filter-mode <FILTER_MODE>      Allow overriding filter mode over config [possible values: global, host, session, directory, workspace, session-preload]
#       --search-mode <SEARCH_MODE>      Allow overriding search mode over config [possible values: prefix, full-text, fuzzy, skim]
#       --keymap-mode <KEYMAP_MODE>      Notify the keymap at the shell's side [default: auto] [possible values: emacs, vim-normal, vim-insert, auto]
#       --human                          Use human-readable formatting for time
#       --cmd-only                       Show only the text of the command
#       --print0                         Terminate the output with a null, for better multiline handling
#       --delete                         Delete anything matching this query. Will not print out the match
#       --delete-it-all                  Delete EVERYTHING!
#   -r, --reverse                        Reverse the order of results, oldest first
#       --timezone [<TIMEZONE>]          Display the command time in another timezone other than the configured default [aliases: --tz]
#   -f, --format <FORMAT>                Available variables: {command}, {directory}, {duration}, {user}, {host}, {time}, {exit} and {relativetime}. Example: --format "{time} - [{duration}] - {directory}$\t{command}"
#       --inline-height <INLINE_HEIGHT>  Set the maximum number of lines Atuin's interface should take up
#       --include-duplicates             Include duplicate commands in the output (non-interactive only)
#   -h, --help                           Print help (see more with '--help')


# Source Atuin's environment file to set up environment variables and paths
. "$HOME/.atuin/bin/env"

# Initialize Atuin for zsh shell integration
eval "$(atuin init zsh)"

# Custom setup function for Atuin with fzf-based history widget
atuin-setup() {
        # Check if atuin is installed, exit function if not found
        if ! which atuin &> /dev/null; then return 1; fi
        # Bind Ctrl+E to Atuin's default search widget
        bindkey '^E' _atuin_search_widget

        # Option to disable Atuin's default keybindings (commented out)
        # export ATUIN_NOBIND="true"
        # Re-initialize Atuin (redundant with line 204, but ensures it's set up in this function)
        eval "$(atuin init "zsh")"
        # Define custom widget that combines Atuin history with fzf
        fzf-atuin-history-widget() {
            # Declare local variables (only 'selected' is actually used)
            local selected num
            # Set shell options: disable glob substitution, use zsh builtins, enable pipefail, disable aliases
            setopt localoptions noglobsubst noposixbuiltins pipefail no_aliases 2>/dev/null

            # Alternative: limit results to 5000 (commented out)
            # local atuin_opts="--cmd-only --limit ${ATUIN_LIMIT:-5000}"
            # Set Atuin to return only commands (no metadata)
            local atuin_opts="--cmd-only"
            # Alternative format with more fields (commented out)
            # local atuin_opts="--format '{command}, {directory}, {duration}, {user}, {host} and {time}'"
            # Override: use human-readable time format with command (tab-separated)
            # local atuin_opts="--human --format '{time}\t{command}'"
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
            zle reset-prompt
            # Return fzf's exit code
            return $ret
        }
        # Register the function as a zsh line editor widget
        zle -N fzf-atuin-history-widget
        # Bind Ctrl+R to the custom widget (overrides default history search)
        bindkey '^R' fzf-atuin-history-widget
    }
# Call the setup function to apply configuration
atuin-setup
