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

# 4. Verify installation
pasteprompt list
```

## Usage

1. **In any text field** (VS Code, Terminal, Notes, browser, etc.)
2. **Right-click** to open context menu
3. Navigate to **Services** submenu
4. Select **PastePrompt - [Prompt Name]**
5. Prompt text is inserted at cursor position

Alternatively, access via the application menu: **App Name > Services > PastePrompt - [name]**

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

Commands:
  init      Create default configuration file
  build     Generate Automator workflows from config
  list      List all available prompts
  paste     Output prompt content (used by workflows)
  validate  Validate configuration file
  clean     Remove all PastePrompt workflows
  refresh   Refresh macOS Services menu
  status    Show current installation status
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

1. **Refresh Services Cache**:
   ```bash
   pasteprompt refresh
   # or manually:
   /System/Library/CoreServices/pbs -update
   ```

2. **Check Workflow Location**:
   ```bash
   ls -la ~/Library/Services/PastePrompt*
   ```

3. **Log out and back in** - Sometimes required for Services to update

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

### Permission Issues

The first time a workflow runs, macOS may prompt for permissions:
- Go to **System Preferences > Security & Privacy > Privacy**
- Enable **Accessibility** for Automator
- Enable **Automation** for your terminal app

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

