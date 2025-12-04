"""Configuration management for PastePrompt."""

import os
import sys
from pathlib import Path

from pasteprompt.prompts import ConfigNotFoundError


# Default paths
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "pasteprompt"
DEFAULT_PROMPTS_FILE = DEFAULT_CONFIG_DIR / "prompts.yaml"
SERVICES_DIR = Path.home() / "Library" / "Services"

# Menu bar app defaults
DEFAULT_MENUBAR_HOTKEY = "cmd+shift+p"
DEFAULT_RESTORE_CLIPBOARD = True
DEFAULT_SHOW_NOTIFICATIONS = True

# LaunchAgent paths
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
LAUNCH_AGENT_LABEL = "com.pasteprompt.menubar"
LAUNCH_AGENT_PLIST = LAUNCH_AGENTS_DIR / f"{LAUNCH_AGENT_LABEL}.plist"


def get_config_path(config_arg: str | None = None) -> Path:
    """
    Get the prompts configuration file path.

    Checks in order:
    1. Explicit config argument (from CLI --config flag)
    2. PASTEPROMPT_CONFIG environment variable
    3. ~/.config/pasteprompt/prompts.yaml
    4. ./prompts.yaml (current directory)

    Args:
        config_arg: Optional explicit path from CLI argument

    Returns:
        Path to prompts.yaml

    Raises:
        ConfigNotFoundError: If no config file found
    """
    # 1. Explicit argument
    if config_arg:
        path = Path(config_arg)
        if path.exists():
            return path
        raise ConfigNotFoundError(f"Specified configuration file not found: {path}")

    # 2. Environment variable
    env_path = os.environ.get("PASTEPROMPT_CONFIG")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        raise ConfigNotFoundError(
            f"Configuration file from PASTEPROMPT_CONFIG not found: {path}"
        )

    # 3. Default config location
    if DEFAULT_PROMPTS_FILE.exists():
        return DEFAULT_PROMPTS_FILE

    # 4. Current directory
    cwd_config = Path.cwd() / "prompts.yaml"
    if cwd_config.exists():
        return cwd_config

    raise ConfigNotFoundError(
        f"No configuration file found. Searched:\n"
        f"  - {DEFAULT_PROMPTS_FILE}\n"
        f"  - {cwd_config}\n"
        f"Run 'pasteprompt init' to create a default configuration."
    )


def ensure_config_dir() -> Path:
    """
    Create config directory if it doesn't exist.

    Returns:
        Path to the config directory
    """
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CONFIG_DIR


def ensure_services_dir() -> Path:
    """
    Ensure the Services directory exists.

    Returns:
        Path to ~/Library/Services/
    """
    SERVICES_DIR.mkdir(parents=True, exist_ok=True)
    return SERVICES_DIR


def get_python_executable() -> str:
    """
    Get the path to the Python executable running pasteprompt.

    This is critical for workflows to call the correct Python.

    Returns:
        Absolute path to the Python executable
    """
    return sys.executable


def _get_example_config_path() -> Path | None:
    """
    Find the path to prompts.example.yaml file.

    Checks multiple locations:
    1. Relative to repo root from package location (development)
    2. Relative to current working directory (development)
    3. By walking up directory tree to find repo root

    Returns:
        Path to example config file, or None if not found
    """
    # File is at: src/pasteprompt/config.py
    # Repo root should be: parent.parent.parent (go up 3 levels)
    config_file = Path(__file__)  # src/pasteprompt/config.py
    repo_root = config_file.parent.parent.parent  # Go up to repo root
    example_path = repo_root / "config" / "prompts.example.yaml"
    if example_path.exists():
        return example_path

    # Try relative to current working directory (development)
    cwd_path = Path.cwd() / "config" / "prompts.example.yaml"
    if cwd_path.exists():
        return cwd_path

    # Try finding repo root by walking up and looking for config directory
    current = Path(__file__).parent
    while current != current.parent:
        example_path = current / "config" / "prompts.example.yaml"
        if example_path.exists():
            return example_path
        parent_config = current.parent / "config" / "prompts.example.yaml"
        if parent_config.exists():
            return parent_config
        current = current.parent

    return None


def create_default_config(output_path: Path | None = None) -> Path:
    """
    Create a default prompts.yaml with example prompts.

    Reads from config/prompts.example.yaml if available, otherwise uses
    a fallback default configuration.

    Args:
        output_path: Optional custom path. If None, uses DEFAULT_PROMPTS_FILE

    Returns:
        Path to the created configuration file
    """
    if output_path is None:
        ensure_config_dir()
        output_path = DEFAULT_PROMPTS_FILE

    # Try to read from the example file
    example_path = _get_example_config_path()
    if example_path and example_path.exists():
        default_config = example_path.read_text(encoding="utf-8")
    else:
        # Fallback to hardcoded default if example file not found
        default_config = '''# PastePrompt Example Configuration
# Copy this file to ~/.config/pasteprompt/prompts.yaml
# Documentation: https://github.com/mjenior/pasteprompt

settings:
  prefix: "PastePrompt"          # Prefix for menu items
  include_key_in_name: false     # Show key in menu (e.g., "[investigate] Investigate")

prompts:
  # === Investigation & Analysis ===
  investigate:
    content: "Methodically investigate the most likely collection of root causes for the following stdout logs. Return all possible causes ranked in terms of severity."
    display_name: "Investigate"
    description: "Analyze logs for root causes"
    category: "Analysis"

  analyze:
    content: "Thoroughly analyze the full code implementation of this plan to ensure that there are no missing components, potential improvements, lingering bugs, and silent errors. Implement any necessary changes identified in this search."
    display_name: "Analyze"
    description: "Deep code analysis"
    category: "Analysis"

  peripheral_analysis:
    content: "Since further issues were identified, perform a supplementary analysis of the peripheral code sections for any additional potential problems. It is also possible that no outstanding issues still exist."
    display_name: "Peripheral Analysis"
    description: "Analyze surrounding code"
    category: "Analysis"

  # === Planning & Strategy ===
  strategize:
    content: "Analyze ALL related sections of the codebase to your findings and create a comprehensive and detailed strategy to address all related issues. Be sure to include peripheral code regions in your analysis which reference or import the impacted code regions."
    display_name: "Strategize"
    description: "Create comprehensive strategy"
    category: "Planning"

  evaluate:
    content: "Evaluate this plan now and restructure as necessary to be as parsimonious as possible with the current codebase, while maintaining ALL of the desired functionality. This should ensure an easier to maintain codebase moving forward."
    display_name: "Evaluate"
    description: "Evaluate and optimize plan"
    category: "Planning"

  recommendations:
    content: "Critically assess all combined planning now and create what would be the most recommended approach. Keep in mind that combining elements of each may actually provide the most optimal implementation for addressing all of the required functionality."
    display_name: "Recommendations"
    description: "Generate recommendations"
    category: "Planning"

  save_plan:
    content: "Save this complete refined hybrid plan to a new text file. All changes will be implemented by an LLM downstream, therefore include relevant details and formatting accordingly."
    display_name: "Save Plan"
    description: "Save plan to file"
    category: "Planning"

  # === Implementation ===
  implement:
    content: "Thoroughly read and understand the provided implementation plan, only after which you may begin applying the highest priority listed features, refactors, or upgrades."
    display_name: "Implement"
    description: "Start implementation"
    category: "Implementation"

  complete:
    content: "Carefully review the planning document and implement any remaining or skipped updates now."
    display_name: "Complete"
    description: "Complete remaining tasks"
    category: "Implementation"

  # === Code Review ===
  detailed_review:
    content: |
      Please review this code with attention to:
      1. Correctness and logic errors
      2. Performance implications
      3. Security vulnerabilities
      4. Code style and readability
      
      Provide specific line-by-line feedback.
    display_name: "Detailed Code Review"
    description: "Comprehensive code review"
    category: "Review"

  # Simple format examples (just key: content)
  explain:
    content: "Explain this code in detail, including what each function does and how they work together."
    display_name: "Explain Code"
    category: "Review"

  refactor:
    content: "Refactor this code to improve readability, maintainability, and performance while preserving all existing functionality."
    display_name: "Refactor"
    category: "Implementation"
'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(default_config, encoding="utf-8")
    return output_path


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled via environment variable."""
    return os.environ.get("PASTEPROMPT_DEBUG", "").lower() in ("true", "1", "yes")

