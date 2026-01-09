#!/bin/zsh
# Master script to refresh all caches
# Run this manually when source data changes

set -e

FZ_CMD_DIR="$HOME/.dotfiles/zsh/fz-cmd"
CACHE_DIR="$FZ_CMD_DIR/cache"
SOURCES_DIR="$FZ_CMD_DIR/sources"

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"

echo "Refreshing fz-cmd caches..."

# Refresh commands.yaml cache
echo "  - Refreshing commands.yaml cache..."
python3 "$SOURCES_DIR/source_commands_yaml.py" "$HOME/.dotfiles/commands.yaml" "$CACHE_DIR/commands.json"

# Refresh aliases cache
echo "  - Refreshing aliases cache..."
python3 "$SOURCES_DIR/source_aliases.py" "$CACHE_DIR/aliases.json"

# Refresh functions cache
echo "  - Refreshing functions cache..."
python3 "$SOURCES_DIR/source_functions.py" "$CACHE_DIR/functions.json"

# Refresh history cache
echo "  - Refreshing history cache..."
python3 "$SOURCES_DIR/source_history.py" 500 "$CACHE_DIR/history.json"

# Refresh tldr cache (optional - only if tldr-commands.yaml exists)
if [ -f "$FZ_CMD_DIR/tldr-commands.yaml" ]; then
    echo "  - Refreshing tldr cache..."
    python3 "$SOURCES_DIR/source_tldr.py" "$FZ_CMD_DIR/tldr-commands.yaml" "$CACHE_DIR/tldr.json"
else
    echo "  - Skipping tldr cache (tldr-commands.yaml not found)"
fi

echo ""
echo "✅ All caches refreshed!"
echo "Cache files are in: $CACHE_DIR"

