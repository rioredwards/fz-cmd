# =============================================================================
# fz-cmd - Atuin Command History Search with fzf
# =============================================================================
#
# A robust, performant zsh script for fuzzy searching command history using atuin
# and fzf. Provides intelligent command insertion with tldr previews.
#
# Author: Rio Edwards
# License: MIT
# =============================================================================

# -----------------------------------------------------------------------------
# Configuration Constants
# -----------------------------------------------------------------------------
readonly FZ_CMD_VERSION="1.0.0"
readonly FZ_CMD_TIME_PADDING=4
readonly FZ_CMD_DEFAULT_HEIGHT="${FZF_TMUX_HEIGHT:-80%}"

# ANSI Color Codes
readonly COLOR_ORANGE='\033[38;5;208m'
readonly COLOR_YELLOW='\033[33m'
readonly COLOR_BOLD_ORANGE='\033[1;38;5;208m'
readonly COLOR_RESET='\033[0m'

# Atuin Configuration
readonly ATUIN_FORMAT='{relativetime}\t{command}'
readonly ATUIN_OPTS="--print0 --format '$ATUIN_FORMAT'"

# -----------------------------------------------------------------------------
# Dependency Checks
# -----------------------------------------------------------------------------
_check_dependencies() {
    local missing_deps=()

    # Check for required dependencies
    if ! command -v atuin >/dev/null 2>&1; then
        missing_deps+=("atuin")
    fi

    if ! command -v fzf >/dev/null 2>&1; then
        missing_deps+=("fzf")
    fi

    if ! command -v perl >/dev/null 2>&1; then
        missing_deps+=("perl")
    fi

    # Check for optional dependencies
    if ! command -v tldr >/dev/null 2>&1; then
        echo "Warning: tldr not found. Command previews will be disabled." >&2
    fi

    # Report missing dependencies
    if (( ${#missing_deps[@]} > 0 )); then
        echo "Error: Missing required dependencies: ${missing_deps[*]}" >&2
        echo "Please install them and try again." >&2
        return 1
    fi

    return 0
}

# -----------------------------------------------------------------------------
# Preview Script Generation
# -----------------------------------------------------------------------------
_generate_preview_script() {
    cat <<-'EOF'
		cmd=$(echo {2} | awk '{print $1}')
		printf '\033[1;38;5;208m━━━ Command: %s ━━━\033[0m\n' "$cmd"
		if command -v tldr >/dev/null 2>&1; then
		    tldr --color=always "$cmd" 2>/dev/null || printf '\033[33m\nNo tldr page found for '\''%s'\''\033[0m\n' "$cmd"
		else
		    printf '\033[33m\ntldr not available for command preview\033[0m\n'
		fi
EOF
}

# -----------------------------------------------------------------------------
# Perl Formatting Script Generation
# -----------------------------------------------------------------------------
_generate_format_script() {
    local time_padding="${1:-$FZ_CMD_TIME_PADDING}"
    local orange_color="${2:-$COLOR_ORANGE}"
    local reset_color="${3:-$COLOR_RESET}"

    # Use colors directly in heredoc - no escaping needed for ANSI codes
    cat <<-EOF
		chomp;
		my (\$t, \$cmd) = split(/\t/, \$_, 2);

		if (defined \$cmd) {
		    # Strip ANSI codes from time field for accurate padding
		    my \$time_text = \$t;
		    \$time_text =~ s/\\033\\[[0-9;]*m//g;

		    # Pad time field to consistent width
		    my \$padded_text = sprintf("%-${time_padding}s", \$time_text);

		    # Apply colors and output formatted line
		    printf "${orange_color}%s${reset_color}\\t%s\\0", \$padded_text, \$cmd;
		} else {
		    # Pass through unchanged if no command found
		    print \$_, "\\0";
		}
EOF
}

# -----------------------------------------------------------------------------
# History Directory Setup
# -----------------------------------------------------------------------------
_setup_history_dir() {
    local history_dir="${HOME}/.dotfiles/.fz-cmd-recent"
    local history_parent="${history_dir:h}"

    # Create parent directory if it doesn't exist
    if [[ ! -d "$history_parent" ]]; then
        mkdir -p "$history_parent" 2>/dev/null || {
            echo "Warning: Could not create history directory: $history_parent" >&2
            return 1
        }
    fi

    echo "$history_dir"
}

# -----------------------------------------------------------------------------
# FZF Options Configuration
# -----------------------------------------------------------------------------
_build_fzf_options() {
    local history_file="$1"
    local preview_script="$2"
    local current_query="${LBUFFER:-}"

    # Core fzf options
    local -a opts=(
        --ansi                    # Enable ANSI color codes
        --read0                   # Read null-separated input
        --no-hscroll              # Disable horizontal scrolling
        --with-nth='{1} - {2}'    # Display format: time - command
        --accept-nth=2            # Return command part when selected
        --nth=1                   # Search in time field by default
        --layout=reverse          # Top-down layout
        --delimiter=$'\t'         # Tab-separated fields
        --border=rounded          # Rounded border style
        --border-label=" Command History "
        --info=inline-right       # Info style
        --pointer="▸"            # Selection pointer
        --prompt="❯ "            # Input prompt
        --header=" Enter: Execute │ Tab: Select │ Ctrl-/: Preview │ Ctrl-d: Directory Filter │ Ctrl-r: Reload │ Esc: Cancel "
        --header-border=bottom
        --height="$FZ_CMD_DEFAULT_HEIGHT"
        --tac                     # Reverse order (newest first)
        --tiebreak=index          # Break ties by original order
        --history="$history_file" # Enable fzf history
        --query="$current_query"  # Pre-fill with current buffer
        +m                        # Disable multi-select
        --expect=enter,tab        # Expect these keys
    )

    # Color theme (Gruvbox-inspired dark theme)
    opts+=(
        --color=fg:#DDC7A1,bg:#1D2021,hl:#E78A4E
        --color=fg+:#DDC7A1,bg+:#3C3836,hl+:#E78A4E:bold
        --color=info:#928374,prompt:#E78A4E,pointer:#E78A4E
        --color=marker:#A9B665,spinner:#E78A4E,header:#928374
        --color=border:#504945,label:#E78A4E
        --color=preview-bg:#141617
    )

    # Bindings
    local format_script
    format_script="$(_generate_format_script)"

    opts+=(
        "--bind=change:first,ctrl-d:reload(atuin search $ATUIN_OPTS -c \$PWD | perl -0ne '$format_script'),ctrl-r:reload(atuin search $ATUIN_OPTS | perl -0ne '$format_script')"
        --bind="ctrl-/:toggle-preview"
    )

    # Preview configuration
    opts+=(
        --preview="$preview_script"
        --preview-window="hidden,right,50%,wrap,border-rounded,<50(hidden,bottom,40%,wrap,border-rounded)"
    )

    # Output the options array
    printf '%q ' "${opts[@]}"
}

# -----------------------------------------------------------------------------
# Core Search Function
# -----------------------------------------------------------------------------
_fz-cmd-core() {
    # Set shell options for safe execution
    setopt localoptions noglobsubst noposixbuiltins pipefail no_aliases 2>/dev/null

    # Dependency check
    _check_dependencies || return 1

    # Setup
    local history_file
    history_file="$(_setup_history_dir)" || return 1

    local preview_script
    preview_script="$(_generate_preview_script)"

    local format_script
    format_script="$(_generate_format_script)"

    # Build fzf options
    local fzf_opts
    fzf_opts="$(_build_fzf_options "$history_file" "$preview_script")"

    # Execute search pipeline with error handling
    local output exit_code

    if output=$(eval "atuin search $ATUIN_OPTS" 2>/dev/null | perl -0ne "$format_script" 2>/dev/null | eval "fzf $fzf_opts" 2>/dev/null); then
        exit_code=$?
    else
        exit_code=$?
        echo "Error: Command execution failed with exit code $exit_code" >&2
        return $exit_code
    fi

    # Parse output: first line is key pressed, rest is selection
    local key selected
    key=$(echo "$output" | head -n1)
    selected=$(echo "$output" | tail -n +2)

    # Validate output - allow empty selected when key is not a known key (means --expect failed)
    if [[ -z "$selected" ]] && [[ "$key" == "enter" || "$key" == "tab" ]]; then
        return $exit_code
    fi

    # Return formatted result
    echo "${key}|${selected}"
    return $exit_code
}

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------
_validate_command() {
    local cmd="$1"

    # Check for empty command
    [[ -n "$cmd" ]] || return 1

    # Check for dangerous characters (basic security)
    [[ "$cmd" != *';'* ]] || {
        echo "Warning: Command contains semicolon, refusing to execute" >&2
        return 1
    }

    return 0
}

# -----------------------------------------------------------------------------
# Command Insertion Logic
# -----------------------------------------------------------------------------
_insert_command() {
    local cmd="$1"
    local execute="$2"
    local context="$3"  # "function" or "widget"

    # Validate command
    _validate_command "$cmd" || return 1

    # Insert command based on execution mode and context
    if [[ "$execute" == "true" ]]; then
        # Execute immediately
        if [[ "$context" == "function" ]]; then
            # Function context: use print -z
            print -z -- "$cmd"
            zle accept-line
        else
            # Widget context: use LBUFFER
            LBUFFER+="$cmd"
            zle accept-line
        fi
    else
        # Insert only
        if [[ "$context" == "function" ]]; then
            # Function context: use print -z
            print -z -- "$cmd"
        else
            # Widget context: use LBUFFER
            LBUFFER+="$cmd"
            zle reset-prompt
        fi
    fi
}

# -----------------------------------------------------------------------------
# Public API Functions
# -----------------------------------------------------------------------------

# Function version - can be called directly from command line
# Usage: fz-cmd
fz-cmd() {
    # Only works in interactive zsh with zle
    if [[ ! -o interactive ]] || [[ ! -o zle ]]; then
        echo "Error: fz-cmd requires an interactive zsh session with zle" >&2
        return 1
    fi

    local output exit_code

    # Execute core search
    if output=$(_fz-cmd-core); then
        exit_code=$?
    else
        exit_code=$?
        return $exit_code
    fi

    # Process successful results
    if [[ $exit_code -eq 0 ]] && [[ -n "$output" ]]; then
        local key cmd
        key="${output%%|*}"
        cmd="${output#*|}"

        if [[ -n "$cmd" ]]; then
            case "$key" in
                enter)
                    _insert_command "$cmd" true function  # Execute
                    ;;
                tab)
                    _insert_command "$cmd" false function # Insert only
                    ;;
                *)
                    echo "Warning: Unknown key action: $key" >&2
                    _insert_command "$cmd" false function # Insert only as fallback
                    ;;
            esac
        elif [[ -n "$key" ]]; then
            # If cmd is empty but key is not, it means --expect didn't work and key contains the command
            # Assume Enter was pressed and execute
            _insert_command "$key" true function  # Execute (key is actually the command)
        fi
    fi

    return $exit_code
}

# ZLE Widget version - for key bindings
# Usage: bindkey '^R' fz-cmd-widget
fz-cmd-widget() {
    # Ensure we're in a zle context
    if [[ ! -o zle ]]; then
        echo "Error: fz-cmd-widget requires zle context" >&2
        return 1
    fi

    local output exit_code

    # Execute core search
    if output=$(_fz-cmd-core); then
        exit_code=$?
    else
        exit_code=$?
        return $exit_code
    fi

    # Process successful results
    if [[ $exit_code -eq 0 ]] && [[ -n "$output" ]]; then
        local key cmd
        key="${output%%|*}"
        cmd="${output#*|}"

        if [[ -n "$cmd" ]]; then
            case "$key" in
                enter)
                    _insert_command "$cmd" true widget  # Execute
                    ;;
                tab)
                    _insert_command "$cmd" false widget # Insert only
                    ;;
                *)
                    # Unknown key - do nothing
                    ;;
            esac
        elif [[ -n "$key" ]]; then
            # If cmd is empty but key is not, it means --expect didn't work and key contains the command
            # Assume Enter was pressed and execute
            _insert_command "$key" true widget  # Execute (key is actually the command)
        fi
    fi

    return $exit_code
}

# Smart down arrow widget - triggers fz-cmd when appropriate
fz-cmd-down-widget() {
    # Check if we should trigger fz-cmd instead of normal history navigation
    if [[ -z "$BUFFER" ]] || [[ "$HISTNO" -eq "$HISTSIZE" ]]; then
        # Empty buffer or at history end - trigger fz-cmd
        fz-cmd-widget
    else
        # Fall back to normal down arrow behavior
        zle .down-line-or-history
    fi
}

# -----------------------------------------------------------------------------
# Initialization and Key Bindings
# -----------------------------------------------------------------------------

# Register ZLE widgets
zle -N fz-cmd-widget
zle -N fz-cmd-down-widget

# Bind down arrow keys to smart widget
# This provides intelligent history navigation
bindkey '^[[B'  fz-cmd-down-widget  # Standard escape sequence
bindkey '^[OB'  fz-cmd-down-widget  # Alternative escape sequence

# -----------------------------------------------------------------------------
# Version and Status Functions
# -----------------------------------------------------------------------------

# Display version information
fz-cmd-version() {
    echo "fz-cmd version $FZ_CMD_VERSION"
    echo "https://github.com/rioedwards/fz-cmd"
}

# Display status and configuration
fz-cmd-status() {
    echo "fz-cmd Status"
    echo "============="
    echo "Version: $FZ_CMD_VERSION"
    echo ""

    echo "Dependencies:"
    local deps=(atuin fzf perl tldr)
    for dep in "${deps[@]}"; do
        if command -v "$dep" >/dev/null 2>&1; then
            echo "  ✓ $dep - $(command -v "$dep")"
        else
            echo "  ✗ $dep - NOT FOUND"
        fi
    done
    echo ""

    echo "Configuration:"
    echo "  Time padding: $FZ_CMD_TIME_PADDING characters"
    echo "  Default height: $FZ_CMD_DEFAULT_HEIGHT"
    echo "  History file: ${HOME}/.dotfiles/.fz-cmd-recent"
    echo ""

    echo "Key bindings:"
    echo "  Down arrow: Smart history (fz-cmd when buffer empty)"
    echo "  Ctrl+R: Can be bound to fz-cmd-widget"
}
