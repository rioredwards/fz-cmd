# fz-cmd - Command Search with Tags

A tag-based command search system using fzf that allows natural language queries to find terminal commands.

## Structure

```
fz-cmd/
├── main.zsh          # Main entry point, orchestrates the command search
├── recent.zsh        # Recent command tracking functions
├── parsers.zsh       # YAML parser orchestration (yq, python, awk)
├── format.zsh        # Formatting and sorting functions
├── history.zsh       # Shell history integration
├── analyze-history.sh # AI-powered history analyzer (optional)
└── parsers/
    ├── parse-yaml.py      # Python YAML parser
    ├── parse-yaml.awk     # awk YAML parser (fallback)
    ├── format.awk         # Formatting script for display
    ├── sort-recent.awk    # Sorting by recent usage
    └── preview.awk        # Preview window formatting
```

## Components

### main.zsh

- Entry point that sources all dependencies
- Defines `_fz-cmd-core()`, `fz-cmd-widget()`, and `fz-cmd()`
- Orchestrates the command search flow

### recent.zsh

- `_fz-cmd-record-usage()` - Records command usage
- `_fz-cmd-get-recent-order()` - Retrieves recent command order

### parsers.zsh

- `_fz-cmd-parse-yaml()` - Tries yq, python, or awk to parse commands.yaml
- Handles parser fallback logic

### format.zsh

- `_fz-cmd-format-output()` - Formats and sorts command output
- `_fz-cmd-build-preview-cmd()` - Builds preview command for fzf

### history.zsh

- `_fz-cmd-get-history()` - Extracts and formats shell history entries
- `_fz-cmd-infer-description()` - Generates descriptions for history commands (with tldr support)
- `_fz-cmd-infer-tags()` - Generates tags for history commands based on patterns

### parsers/

Contains standalone scripts for parsing and formatting:

- **parse-yaml.py**: Python-based YAML parser (requires PyYAML)
- **parse-yaml.awk**: awk-based YAML parser (fallback)
- **format.awk**: Formats output with fixed-width columns
- **sort-recent.awk**: Sorts commands by recent usage
- **preview.awk**: Generates preview text for fzf

## Usage

The module is automatically loaded from `zsh/fzf.zsh`. Use:

- `fz-cmd` - Function to search and select commands
- `fz-cmd-widget` - ZLE widget (can be bound to a key)

## Data Format

Commands are stored in `~/.dotfiles/commands.yaml` with the following structure:

```yaml
commands:
  - command: hostname -I
    description: Get local IP address
    tags: [ip, address, network]
    examples: ["hostname -I", "hostname -I | xargs"]
```

## Recent Commands

Recent command usage is tracked in `~/.dotfiles/.fz-cmd-recent` (gitignored).
Most recently used commands appear first in the search results.

## Shell History Integration

`fz-cmd` now automatically merges your shell history with curated commands from `commands.yaml`. This means:

- **Curated commands** (from `commands.yaml`) appear first with full descriptions, tags, and examples
- **History commands** appear after, with auto-generated descriptions and tags
- **Deduplication**: If a command exists in both, the curated version is preferred
- **Smart filtering**: Common noise commands (like `ls`, `cd`, `pwd`) are filtered out

### Configuration

Control history integration with environment variables:

```zsh
# Disable history integration (fastest - curated commands only)
export FZ_CMD_ENABLE_HISTORY=0

# Limit number of history entries (default: 200, lower = faster)
export FZ_CMD_MAX_HISTORY=100

# Enable tldr lookups (slower but better descriptions, default: 0)
export FZ_CMD_USE_TLDR=1

# Enable debug mode to see what's happening (default: 0)
export FZ_CMD_DEBUG=1
```

**Performance Tips:**

- Default settings are optimized for speed (200 history entries, no tldr)
- If it's still slow, reduce `FZ_CMD_MAX_HISTORY` to 50-100
- Disable history entirely with `FZ_CMD_ENABLE_HISTORY=0` for fastest startup
- Check status with: `fz-cmd-status`

### Auto-Enrichment with tldr

tldr lookups are **disabled by default** for performance. If you want better descriptions, enable it:

```bash
brew install tldr
tldr --update
export FZ_CMD_USE_TLDR=1
```

Note: tldr lookups can slow down history processing significantly.

## History Analysis Script

The `analyze-history.sh` script can analyze your shell history and suggest new commands to add to `commands.yaml`:

```bash
# Dry run (show suggestions without modifying)
./zsh/fz-cmd/analyze-history.sh --dry-run

# Analyze last 2000 history entries
./zsh/fz-cmd/analyze-history.sh --limit 2000
```

This helps identify frequently used commands that aren't yet in your curated list.

## Alternative Tools

If you want to explore existing command palette tools, consider:

- **navi** - Interactive cheatsheet tool: `brew install navi`
- **tldr** - Simplified man pages: `brew install tldr`
- **cheat** - Create and view cheatsheets: `brew install cheat`
- **bro** - Command-line bookmark manager: `brew install bro`

These tools can complement `fz-cmd` by providing additional command documentation and examples.

## Troubleshooting

### Cache directory not found

**Error**: `Error: Cache directory not found`

**Solution**: Run the cache refresh script:
```bash
cd ~/.dotfiles/zsh/fz-cmd
zsh scripts/refresh_cache.sh
```

### No cache files found

**Error**: `Error: No cache files found`

**Solution**: Ensure cache files were generated successfully:
```bash
ls -la ~/.dotfiles/zsh/fz-cmd/cache/
# Should see: commands.json, aliases.json, functions.json, history.json
```

### Python dependency errors

**Error**: `ModuleNotFoundError: No module named 'yaml'`

**Solution**: Install PyYAML:
```bash
pip3 install pyyaml
```

### Slow startup

**Issue**: fz-cmd takes > 1 second to start

**Solution**: Reduce data limits via environment variables:
```bash
export FZ_CMD_LIMIT_CURATED=500
export FZ_CMD_LIMIT_HISTORY=100
export FZ_CMD_LIMIT_ALIAS=50
export FZ_CMD_LIMIT_FUNCTION=50
```

### Command not being inserted

**Issue**: Selected command doesn't appear in the prompt

**Solution**:
- For widget mode: Ensure `fz-cmd-widget` is bound to a key
- For function mode: Use `fz-cmd` directly (not in a pipeline)
- Check that `pbcopy` is available (macOS)

### tldr commands not appearing

**Issue**: tldr commands are missing from search

**Solution**: tldr is disabled by default for speed. Enable it:
```bash
export FZ_CMD_INCLUDE_TLDR=1
```

Then refresh the tldr cache if needed:
```bash
cd ~/.dotfiles/zsh/fz-cmd
python3 generate-tldr-cache.py
```
