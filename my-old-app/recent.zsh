# Recent command tracking for fz-cmd
# Tracks command usage to sort by most recently used

# Record command usage for recent sorting
_fz-cmd-record-usage() {
    local cmd="$1"
    local recent_file="$HOME/.dotfiles/.fz-cmd-recent"
    
    if [ -z "$cmd" ]; then
        return
    fi
    
    # Create recent file if it doesn't exist
    [ -f "$recent_file" ] || touch "$recent_file"
    
    # Remove the command if it already exists (to avoid duplicates)
    # Then prepend the new usage to the file
    # Limit to 100 most recent commands
    {
        echo "$cmd"
        grep -vFx "$cmd" "$recent_file" | head -99
    } > "${recent_file}.tmp" && mv "${recent_file}.tmp" "$recent_file"
}

# Get recent command order (returns commands in order of most recent first)
_fz-cmd-get-recent-order() {
    local recent_file="$HOME/.dotfiles/.fz-cmd-recent"
    
    if [ -f "$recent_file" ]; then
        cat "$recent_file"
    fi
}

