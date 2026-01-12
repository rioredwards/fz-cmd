# fz-cmd - Atuin Command History Search

A simple zsh script that provides fuzzy search through your command history using atuin and fzf.

## Features

- **Atuin Integration**: Uses atuin to access your command history with relative timestamps
- **Fuzzy Search**: Interactive fuzzy finding with fzf
- **tldr Previews**: Shows tldr documentation for commands in the preview pane
- **Zsh Integration**: ZLE widgets for seamless shell integration
- **Key Bindings**: Tab to insert, Enter to execute

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

## Dependencies

- **atuin**: For command history with timestamps
- **fzf**: For fuzzy finding interface
- **tldr**: For command previews (optional)
- **zsh**: With zle support

## Installation

1. Install dependencies:

   ```bash
   # macOS
   brew install atuin fzf tldr

   # Ubuntu/Debian
   # Install atuin from https://github.com/atuinsh/atuin
   # Install fzf and tldr from package manager
   ```

2. Source the script in your `.zshrc`:

   ```zsh
   source ~/.dotfiles/zsh/fz-cmd/main.zsh
   ```

3. Optional: Bind to a key:
   ```zsh
   bindkey '^R' fz-cmd-widget  # Replace Ctrl+R
   ```

## Architecture

The script consists of:

- `_fz-cmd-core()`: Main search logic using atuin + fzf
- `fz-cmd()`: Function version for manual invocation
- `fz-cmd-widget()`: ZLE widget for key binding
- `fz-cmd-down-widget()`: Smart down arrow that triggers fz-cmd when appropriate

All command processing is done with perl for text formatting and ANSI color handling.
