"""Configuration management for PastePrompt."""

import os
import sys
from pathlib import Path

from pasteprompt.prompts import ConfigNotFoundError


# Default paths
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "pasteprompt"
DEFAULT_PROMPTS_FILE = DEFAULT_CONFIG_DIR / "prompts.yaml"
SERVICES_DIR = Path.home() / "Library" / "Services"


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


def create_default_config(output_path: Path | None = None) -> Path:
    """
    Create a default prompts.yaml with example prompts.

    Args:
        output_path: Optional custom path. If None, uses DEFAULT_PROMPTS_FILE

    Returns:
        Path to the created configuration file
    """
    if output_path is None:
        ensure_config_dir()
        output_path = DEFAULT_PROMPTS_FILE

    default_config = '''# PastePrompt Configuration
# Location: ~/.config/pasteprompt/prompts.yaml
# Documentation: https://github.com/mjenior/pasteprompt

settings:
  prefix: "PastePrompt"
  include_key_in_name: false

prompts:
  # === Investigation & Analysis ===
  investigate:
    content: "Meticulously investigate the most likely collection of root causes for the following stdout logs. Return all possible causes ranked in terms of severity."
    display_name: "Investigate"
    category: "Analysis"

  analyze:
    content: "Painstakingly analyze the full code implementation of this plan to ensure that there are no missing components, potential improvements, lingering bugs, and silent errors. Implement any necessary changes identified in this search."
    display_name: "Analyze"
    category: "Analysis"

  peripheral_analysis:
    content: "Since further issues were identified, perform a supplementary analysis of the peripheral code sections for any additional potential problems. It is also possible that no outstanding issues still exist and implement the required fixes."
    display_name: "Peripheral Analysis"
    category: "Analysis"

  # === Planning & Strategy ===
  strategize:
    content: "Analyze ALL related sections of the codebase to your findings and create a comprehensive and detailed strategy to address all related issues. Be sure to include peripheral code regions in your analysis which reference or import the impacted code regions."
    display_name: "Strategize"
    category: "Planning"

  evaluate:
    content: "Evaluate this plan now and restructure as necessary to be as parsimonious as possible with the current codebase, while maintaining ALL of the desired functionality. This should ensure an easier to maintain codebase moving forward."
    display_name: "Evaluate"
    category: "Planning"

  recommendations:
    content: "Critically assess all combined planning now and create what would be the most recommended approach. Keep in mind that combining elements of each may actually provide the most optimal implementation for addressing all of the underlying issues."
    display_name: "Recommendations"
    category: "Planning"

  save_plan:
    content: "Save this complete refined hybrid plan to a new text file. All changes will be implemented by an LLM downstream, therefore include relevant details and formatting accordingly."
    display_name: "Save Plan"
    category: "Planning"

  # === Implementation ===
  implement:
    content: "Thoroughly read and understand the provided implementation plan, only after which you may begin applying the highest priority listed refactors or upgrades."
    display_name: "Implement"
    category: "Implementation"

  complete:
    content: "Carefully review the planning document and implement any remaining or skipped updates now."
    display_name: "Complete"
    category: "Implementation"
'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(default_config, encoding="utf-8")
    return output_path


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled via environment variable."""
    return os.environ.get("PASTEPROMPT_DEBUG", "").lower() in ("true", "1", "yes")

