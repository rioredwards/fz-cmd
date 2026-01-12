# fz-cmd - Atuin Command History Search

A robust, performant zsh script that provides intelligent fuzzy search through your command history using atuin and fzf. Features comprehensive error handling, dependency checking, and seamless zsh integration.

## Features

- **🔍 Atuin Integration**: Uses atuin for rich command history with relative timestamps
- **⚡ Fuzzy Search**: Interactive fuzzy finding with fzf and intelligent key bindings
- **📚 TLDR Previews**: Shows command documentation in preview pane
- **🛡️ Error Handling**: Comprehensive dependency checking and input validation
- **🎨 Beautiful UI**: Gruvbox-inspired dark theme with ANSI colors
- **⌨️ Zsh Integration**: ZLE widgets for seamless shell integration
- **🔄 Smart History**: Context-aware history navigation
- **⚙️ Configurable**: Environment variables for customization

## Usage

### Basic Usage

```zsh
# Source the script
source ~/.dotfiles/zsh/fz-cmd/main.zsh

# Use the function
fz-cmd

# Or bind to a key (recommended)
bindkey '^R' fz-cmd-widget  # Ctrl+R for history search
```

### Key Bindings in fzf

- **Enter**: Insert command and execute immediately
- **Tab**: Insert command into buffer (don't execute)
- **Ctrl-/**: Toggle preview pane
- **Ctrl-d**: Reload with current directory filter
- **Ctrl-r**: Reload without directory filter
- **Esc**: Cancel

### Status and Diagnostics

```zsh
# Check status and dependencies
fz-cmd-status

# Show version
fz-cmd-version
```

## Dependencies

- **atuin**: For command history with timestamps (required)
- **fzf**: For fuzzy finding interface (required)
- **perl**: For text processing and formatting (required)
- **tldr**: For command previews (optional)
- **zsh**: With zle support (required)

## Installation

1. Install dependencies:

   ```bash
   # macOS
   brew install atuin fzf tldr

   # Ubuntu/Debian
   # Install atuin from https://github.com/atuinsh/atuin/releases
   sudo apt install fzf tldr
   ```

2. Source the script in your `.zshrc`:

   ```zsh
   source ~/.dotfiles/zsh/fz-cmd/main.zsh
   ```

3. Optional: Bind to a key:
   ```zsh
   bindkey '^R' fz-cmd-widget  # Replace Ctrl+R
   ```

## Configuration

### Environment Variables

```zsh
# UI Configuration
export FZF_TMUX_HEIGHT="90%"           # Default height for fzf window

# Advanced Configuration (usually no need to change)
export FZ_CMD_TIME_PADDING=4           # Characters to pad timestamps
```

### Key Bindings

The script automatically binds the down arrow key to smart history navigation. You can also bind additional keys:

```zsh
# Bind Ctrl+R to fz-cmd-widget
bindkey '^R' fz-cmd-widget

# Bind other keys as needed
bindkey '^H' fz-cmd-widget  # Ctrl+H for history
```

## Architecture

### Core Components

- **`_fz-cmd-core()`**: Main search logic with dependency checking and pipeline execution
- **`fz-cmd()`**: Function version for manual invocation (requires interactive zsh)
- **`fz-cmd-widget()`**: ZLE widget for key bindings (requires zle context)
- **`fz-cmd-down-widget()`**: Smart down arrow navigation
- **`fz-cmd-status()`**: Diagnostic and status reporting
- **`fz-cmd-version()`**: Version information

### Data Flow

```
Atuin History → Perl Formatting → FZF Interface → User Selection → ZLE Insertion
```

### Error Handling

The script includes comprehensive error handling for:

- Missing dependencies (atuin, fzf, perl, tldr)
- Invalid command inputs (dangerous characters)
- ZLE context requirements
- Pipeline execution failures
- History directory creation

### Security

- Commands are never executed automatically
- Input validation prevents dangerous command injection
- User must explicitly confirm execution via Enter key

## Troubleshooting

### Common Issues

**"Error: Missing required dependencies"**

- Install missing dependencies using your package manager
- Run `fz-cmd-status` to check which dependencies are missing

**"Error: fz-cmd requires an interactive zsh session"**

- fz-cmd only works in interactive zsh shells
- Source the script in your `.zshrc`, not in scripts

**"Command not inserted correctly"**

- Ensure you're using the widget version (`fz-cmd-widget`) for key bindings
- Check that zle is available: `zle -l`

**"Preview shows 'tldr not available'"**

- Install tldr: `brew install tldr` (macOS) or `sudo apt install tldr` (Ubuntu)
- Previews work without tldr but are less informative

### Debug Information

Run `fz-cmd-status` to see:

- Dependency status
- Configuration values
- Key binding information
- Version information

## Performance

- **Startup**: < 100ms with proper dependencies
- **Search**: Near-instant with atuin's indexed history
- **Memory**: Minimal - streams data through pipelines
- **CPU**: Low - uses optimized perl and fzf

## Contributing

This script is designed to be robust and maintainable. Key principles:

- Comprehensive error handling
- Input validation
- Clear separation of concerns
- Extensive documentation
- Dependency checking

## License

MIT License - see repository for details.
