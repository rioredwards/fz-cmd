# fz-cmd Application Overview

## Purpose

`fz-cmd` is a command search and selection tool for zsh that aggregates commands from multiple sources (curated YAML, shell history, aliases, functions, and tldr) and provides a fast, fuzzy-searchable interface using `fzf`. Selected commands are inserted into the command line buffer (not executed automatically) and copied to the clipboard.

## Architecture

### Data Flow

```
Data Sources → Source Scripts (Python) → JSON Cache Files → Merge Utility → Limit Utility → Format Utility → fzf → User Selection → Command Insertion
```

### Key Design Principles

1. **Caching Strategy**: All data sources are pre-processed into JSON cache files for fast startup
2. **Separation of Concerns**: Data sourcing, merging, formatting, and display are separate Python utilities
3. **Source Priority**: Commands are deduplicated with priority: `curated > alias > function > history > tldr`
4. **Manual Cache Refresh**: Cache files are updated manually via `refresh_cache.sh` (no automatic invalidation in v1)
5. **Security**: Commands are NEVER executed automatically - only inserted into buffer and copied to clipboard

## Directory Structure

```
fz-cmd/
├── main.zsh                    # Main entry point - orchestrates search flow
├── cache/                      # JSON cache files (gitignored)
│   ├── commands.json           # From commands.yaml (curated)
│   ├── aliases.json            # From shell aliases
│   ├── functions.json          # From shell functions
│   ├── history.json            # From shell history
│   └── tldr.json               # From tldr-commands.yaml
├── sources/                     # Data sourcing scripts (Python)
│   ├── source_commands_yaml.py # Parses commands.yaml → JSON
│   ├── source_aliases.py     # Extracts aliases → JSON
│   ├── source_functions.py     # Extracts functions → JSON
│   ├── source_history.py       # Processes history → JSON
│   └── source_tldr.py          # Parses tldr cache → JSON
├── utils/                       # Reusable Python utilities
│   ├── merge_commands.py       # Merges multiple JSON files, deduplicates
│   ├── format_for_fzf.py       # Formats JSON → tab-separated for fzf
│   ├── build_preview.py        # Generates preview text for fzf
│   └── limit_commands.py       # Limits commands per source (for fast startup)
├── scripts/                     # Shell wrapper scripts
│   ├── refresh_cache.sh        # Master script to refresh all caches
│   └── run_tests.sh            # Run all tests
└── tests/                       # Test files (TDD approach)
    ├── test_merge_commands.py
    ├── test_format_for_fzf.py
    ├── test_build_preview.py
    ├── test_limit_commands.py
    └── test_source_*.py         # Tests for each source script
```

## Core Components

### 1. main.zsh

**Entry Point**: `fz-cmd()` function or `fz-cmd-widget` ZLE widget

**Flow**:

1. Loads cached JSON files from `cache/` directory
2. Merges all cache files using `merge_commands.py` (deduplicates by source priority)
3. Applies limits per source using `limit_commands.py` (for fast startup)
4. Formats merged data using `format_for_fzf.py` (tab-separated format)
5. Displays in `fzf` with preview window using `build_preview.py`
6. On selection: copies command to clipboard (`pbcopy`) and inserts into buffer

**Key Functions**:

- `_fz-cmd-core()`: Orchestrates the entire search flow
- `fz-cmd-widget()`: ZLE widget version (inserts into `LBUFFER`)
- `fz-cmd()`: Function version (uses `print -z` to insert)
- `fz-cmd-status()`: Shows configuration and cache status

**Security Model**:

- NEVER executes commands automatically
- Only inserts text into command buffer
- User must press Enter to execute
- Commands are validated (no newlines, control characters)

### 2. Source Scripts (`sources/`)

Each source script is a standalone Python script that:

- Reads from a specific data source
- Outputs standardized JSON format to a cache file
- Handles errors gracefully (missing files, invalid data)

**source_commands_yaml.py**:

- Input: `~/.dotfiles/commands.yaml`
- Output: `cache/commands.json`
- Source tag: `"curated"`

**source_aliases.py**:

- Input: Shell `alias` command output
- Output: `cache/aliases.json`
- Source tag: `"alias"`

**source_functions.py**:

- Input: Shell `functions` command output
- Output: `cache/functions.json`
- Source tag: `"function"`

**source_history.py**:

- Input: Shell history (via `fc -l`)
- Output: `cache/history.json`
- Source tag: `"history"`
- Filters noise commands (ls, cd, pwd, etc.)
- Takes limit parameter (default: 500)

**source_tldr.py**:

- Input: `fz-cmd/tldr-commands.yaml`
- Output: `cache/tldr.json`
- Source tag: `"tldr"`
- Optional (only if tldr-commands.yaml exists)

### 3. Utility Scripts (`utils/`)

**merge_commands.py**:

- Merges multiple JSON command files
- Deduplicates by command string
- Preserves source priority (curated > alias > function > history > tldr)
- Usage: `merge_commands.py file1.json file2.json ...`

**format_for_fzf.py**:

- Formats JSON commands into tab-separated format for fzf
- Format: `<display_text>\t<command>\t<description>\t<tags>\t<examples>`
- Display text: `command | description [tags]`
- Usage: `format_for_fzf.py merged.json`

**build_preview.py**:

- Generates preview text for fzf preview window
- Takes individual fields as arguments (to avoid tab-separated reconstruction issues)
- Formats with command, description, tags, examples, source
- Usage: `build_preview.py '{1}' '{2}' '{3}' '{4}' '{5}'` (fzf field placeholders)

**limit_commands.py**:

- Limits number of commands per source
- Preserves source priority when limiting
- Usage: `limit_commands.py merged.json --limit curated:1000 --limit history:200`

### 4. Cache Management

**refresh_cache.sh**:

- Master script to refresh all cache files
- Runs all source scripts in sequence
- Creates cache directory if missing
- Should be run manually when source data changes

## Data Format

### Standard JSON Format

All cache files use this structure:

```json
{
  "commands": [
    {
      "command": "git status",
      "description": "Show git repository status",
      "tags": ["git", "status", "repository"],
      "examples": ["git status", "git status -s"],
      "source": "curated|alias|function|history|tldr",
      "metadata": {}
    }
  ]
}
```

### fzf Format (Tab-Separated)

After formatting, commands are tab-separated:

```
<command>\t<description>\t<tags>\t<examples>
```

Example:

```
git status\tShow git repository status\tgit, status, repositorygit status	Show git repository status	git, status, repository	git status | git status -s
```

## Configuration

### Environment Variables

**Data Limits** (for fast startup):

- `FZ_CMD_LIMIT_CURATED` (default: 1000)
- `FZ_CMD_LIMIT_ALIAS` (default: 100)
- `FZ_CMD_LIMIT_FUNCTION` (default: 100)
- `FZ_CMD_LIMIT_HISTORY` (default: 200)
- `FZ_CMD_LIMIT_TLDR` (default: 500)
- Set to `0` to disable a source entirely

**Feature Flags**:

- `FZ_CMD_INCLUDE_TLDR` (default: 0) - Include tldr cache in search
- `FZ_CMD_DEBUG` (default: 0) - Enable debug output with timing

### Usage

```zsh
# Basic usage
fz-cmd                    # Function version
fz-cmd-widget             # Widget version (bind to key)

# Check status
fz-cmd-status

# Refresh caches manually
~/.dotfiles/zsh/fz-cmd/scripts/refresh_cache.sh
```

## Command Selection Behavior

When a command is selected in fzf:

1. **Command is extracted** from tab-separated output (field 2)
2. **Validated** (no newlines, control characters)
3. **Copied to clipboard** using `pbcopy` (macOS)
4. **Inserted into command buffer**:
   - Widget version: `LBUFFER+="$cmd"` (inserts at cursor)
   - Function version: `print -z -- "$cmd"` (adds to history, appears on next prompt)
5. **User must press Enter** to execute (never executed automatically)

## Extending the Application

### Adding a New Data Source

1. **Create source script** (`sources/source_new_source.py`):

   - Read from your data source
   - Output standardized JSON format
   - Add `source` field with unique identifier

2. **Update refresh_cache.sh**:

   - Add call to your source script

3. **Update merge_commands.py**:

   - Add source to `SOURCE_PRIORITY` dict with appropriate priority

4. **Update main.zsh**:

   - Add cache file to `cache_files` array
   - Add limit variable if needed

5. **Write tests** (`tests/test_source_new_source.py`)

### Modifying Display Format

Edit `utils/format_for_fzf.py` to change how commands appear in fzf.

### Modifying Preview Format

Edit `utils/build_preview.py` to change preview window content.

## Common Issues & Troubleshooting

### Cache Files Missing

**Symptom**: Error "No cache files found"

**Solution**: Run `refresh_cache.sh` to generate cache files

### Slow Startup

**Symptom**: fz-cmd takes too long to start

**Solutions**:

- Reduce limits: `export FZ_CMD_LIMIT_HISTORY=50`
- Disable tldr: `export FZ_CMD_INCLUDE_TLDR=0`
- Disable sources: `export FZ_CMD_LIMIT_TLDR=0`

### Commands Not Appearing

**Symptom**: Expected commands missing from search

**Possible Causes**:

1. Cache not refreshed after adding commands to `commands.yaml`
2. Command filtered out by deduplication (lower priority source)
3. Command filtered by limit (too many commands from that source)

**Solution**:

- Refresh cache: `refresh_cache.sh`
- Check cache files: `cat cache/commands.json | jq`
- Check limits: `fz-cmd-status`

### Preview Not Working

**Symptom**: Preview window shows errors or empty

**Possible Causes**:

1. `build_preview.py` receiving wrong field format
2. Tab-separated field extraction issues

**Solution**: Check fzf field placeholders match format_for_fzf.py output

### Command Insertion Issues

**Symptom**: Command not inserted correctly into buffer

**Possible Causes**:

1. Special characters in command (brackets, globs)
2. `nomatch` option causing glob expansion errors

**Solution**: `main.zsh` disables `nomatch` with `setopt +o nomatch`

## Testing

All components have corresponding test files in `tests/`. Run tests with:

```bash
./zsh/fz-cmd/scripts/run_tests.sh
```

Tests use TDD approach and cover:

- Edge cases (empty files, missing fields)
- Data format validation
- Source priority logic
- Formatting correctness

## Performance Characteristics

- **Startup Time**: < 100ms (with limits, cached data)
- **Cache Refresh**: 1-5 seconds (depends on history size)
- **Memory**: Minimal (streams data through pipes)

## Future Enhancements (v2)

- Smart cache invalidation (detect source changes)
- Incremental history updates (append-only)
- Usage tracking and sorting by frequency
- Background cache refresh
- More data sources (cheat sheets, custom scripts)
