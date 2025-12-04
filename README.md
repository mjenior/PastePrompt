# PastePrompt

A macOS utility that adds customizable prompt snippets to the system Services menu, accessible via right-click context menu in any text field.

## Features

- **Native macOS Integration**: Prompts appear in the right-click Services menu
- **Works Everywhere**: Use in any app that supports Services (VS Code, Terminal, browsers, etc.)
- **Easy Configuration**: Define prompts in a simple YAML file
- **Fast Access**: No need to switch windows or copy/paste manually
- **Organized**: Group prompts by category

## Installation

### With UV (Recommended)

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/mjenior/pasteprompt.git
cd pasteprompt
uv venv
uv pip install -e .
```

### With pip

```bash
pip install -e .
# or directly from GitHub
pip install git+https://github.com/mjenior/pasteprompt.git
```

## Quick Start

```bash
# 1. Initialize configuration (creates ~/.config/pasteprompt/prompts.yaml)
pasteprompt init

# 2. Edit prompts to your liking
nano ~/.config/pasteprompt/prompts.yaml

# 3. Build workflows
pasteprompt build

# 4. Enable Services in System Settings (required on macOS Ventura+)
#    Go to: System Settings > Keyboard > Keyboard Shortcuts > Services
#    Enable the PastePrompt services under "Text"

# 5. Verify installation
pasteprompt list
```

## Usage

### Option 1: Services Menu (Built-in)

1. **In any text field** (VS Code, Terminal, Notes, browser, etc.)
2. **Right-click** to open context menu
3. Navigate to **Services** submenu
4. Select **PastePrompt - [Prompt Name]**
5. Prompt text is inserted at cursor position

Alternatively, access via the application menu: **App Name > Services > PastePrompt - [name]**

### Option 2: Menu Bar App with Global Hotkey ⭐

For faster access, use the menu bar app with global hotkey support:

```bash
# Install menu bar dependencies
pip install pasteprompt[menubar]

# Start the menu bar app
pasteprompt menubar start
```

Then:
1. **Press ⌘⇧P** (Cmd+Shift+P) anywhere to open the quick picker
2. **Type to search** prompts by name or content
3. **Press Enter** to paste the selected prompt instantly

Or click the 📋 menu bar icon to see all prompts in a dropdown.

#### Auto-Start on Login

```bash
# Install for automatic startup
pasteprompt menubar install

# Check status
pasteprompt menubar status

# Remove from login items
pasteprompt menubar uninstall
```

## Configuration

Prompts are defined in `~/.config/pasteprompt/prompts.yaml`:

```yaml
settings:
  prefix: "PastePrompt"
  include_key_in_name: false  # Set to true for "[key] Name" format

prompts:
  # Simple format
  investigate:
    content: "Investigate the root causes for these logs..."
    display_name: "Investigate"
    category: "Analysis"

  # Multi-line content
  code_review:
    content: |
      Please review this code with attention to:
      1. Correctness and logic errors
      2. Performance implications
      3. Security vulnerabilities
    display_name: "Code Review"
    category: "Review"
```

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `prefix` | `"PastePrompt"` | Prefix for all menu items |
| `include_key_in_name` | `false` | When `true`, shows key in menu (e.g., `"[investigate] Investigate"`) |

### Menu Bar Settings

Add these under `settings.menubar` in your config:

```yaml
settings:
  menubar:
    hotkey: "cmd+shift+p"        # Global hotkey (default: ⌘⇧P)
    restore_clipboard: true       # Restore clipboard after paste
    show_notifications: true      # Show notification messages
```

| Setting | Default | Description |
|---------|---------|-------------|
| `hotkey` | `"cmd+shift+p"` | Global hotkey for quick picker |
| `restore_clipboard` | `true` | Restore original clipboard after pasting |
| `show_notifications` | `true` | Show macOS notifications |

**Hotkey format**: Use `+` to combine modifiers: `cmd`, `shift`, `ctrl`/`control`, `alt`/`option`/`opt`

Examples: `cmd+shift+p`, `cmd+shift+1`, `ctrl+alt+v`

### Prompt Options

| Field | Required | Description |
|-------|----------|-------------|
| `content` | Yes | The prompt text to insert |
| `display_name` | No | Name shown in Services menu (defaults to formatted key) |
| `description` | No | Optional description for documentation |
| `category` | No | Group prompts for organization |

## CLI Commands

```
pasteprompt [command]

Core Commands:
  init      Create default configuration file
  build     Generate Automator workflows from config
  list      List all available prompts
  paste     Output prompt content (used by workflows)
  validate  Validate configuration file
  clean     Remove all PastePrompt workflows
  refresh   Refresh macOS Services menu
  status    Show current installation status

Menu Bar Commands:
  menubar start      Start the menu bar app (foreground)
  menubar install    Install for auto-start on login
  menubar uninstall  Remove from login items
  menubar status     Show menu bar app status
```

### Common Operations

```bash
# Create initial configuration
pasteprompt init

# Build workflows (generates .workflow files)
pasteprompt build

# Rebuild after editing prompts
pasteprompt build --force

# List all prompts
pasteprompt list

# Show detailed prompt content
pasteprompt list --verbose

# Validate configuration
pasteprompt validate

# Check installation status
pasteprompt status

# Remove all workflows
pasteprompt clean

# Force refresh Services menu
pasteprompt refresh
```

### Using a Custom Config File

```bash
# Use a specific config file
pasteprompt build --config ./my-prompts.yaml
pasteprompt list --config ./my-prompts.yaml
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PASTEPROMPT_CONFIG` | `~/.config/pasteprompt/prompts.yaml` | Path to config file |
| `PASTEPROMPT_DEBUG` | `false` | Enable debug logging |

## Troubleshooting

### Services Menu Not Showing

1. **Enable Services in System Settings** (most common issue on macOS Ventura+):
   - Open **System Settings > Keyboard > Keyboard Shortcuts > Services**
   - Scroll to the **Text** section
   - Enable the PastePrompt services you want to use
   - Alternatively, open directly via Terminal:
     ```bash
     open "x-apple.systempreferences:com.apple.Keyboard-Settings.extension?Services"
     ```

2. **Refresh Services Cache**:
   ```bash
   pasteprompt refresh
   # or manually:
   /System/Library/CoreServices/pbs -flush
   /System/Library/CoreServices/pbs -update
   ```

3. **Check Workflow Location**:
   ```bash
   ls -la ~/Library/Services/PastePrompt*
   ```

4. **Log out and back in** - Sometimes required for Services to update

5. **Rebuild workflows** if you upgraded from an older version:
   ```bash
   pasteprompt build --force
   ```

### Prompt Not Inserting

1. **Test CLI Directly**:
   ```bash
   pasteprompt paste investigate
   # Should output the prompt content
   ```

2. **Check Installation**:
   ```bash
   pasteprompt status
   ```

3. **Ensure cursor is in a text field** - Services only work in editable text contexts

### Permission Issues

The first time a workflow runs, macOS may prompt for permissions:
- Go to **System Settings > Privacy & Security > Privacy**
- Enable **Accessibility** for Automator
- Enable **Automation** for your terminal app

### Menu Bar App Issues

**Global hotkey not working:**
1. Grant Accessibility permissions:
   - Open **System Settings > Privacy & Security > Accessibility**
   - Add and enable your terminal app (Terminal, iTerm, etc.)
   - If running as a standalone app, add Python or the app itself

2. Restart the menu bar app:
   ```bash
   pasteprompt menubar start
   ```

**Paste not inserting text:**
- Ensure the cursor is in an editable text field
- Check that Accessibility permissions are granted
- Try clicking the menu bar icon and selecting a prompt directly

**Menu bar icon not appearing:**
- Check that the app is running: `pasteprompt menubar status`
- Ensure rumps dependencies are installed: `pip install pasteprompt[menubar]`

## Development

```bash
# Clone repository
git clone https://github.com/mjenior/pasteprompt.git
cd pasteprompt

# Create virtual environment
uv venv
source .venv/bin/activate

# Install in development mode
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/
```

## How It Works

1. **Configuration**: User defines prompts in `prompts.yaml`
2. **Build**: `pasteprompt build` generates macOS Automator Quick Action workflows
3. **Integration**: Workflows are placed in `~/Library/Services/`
4. **Execution**: When selected from Services menu, workflow runs `pasteprompt paste <key>`
5. **Output**: Prompt content is output to stdout and inserted by Automator

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

