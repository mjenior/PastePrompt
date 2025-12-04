"""YAML prompt loading and validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


class PastePromptError(Exception):
    """Base exception for PastePrompt."""

    pass


class ConfigNotFoundError(PastePromptError):
    """Configuration file not found."""

    pass


class PromptsConfigError(PastePromptError):
    """Invalid prompts configuration."""

    pass


class PromptNotFoundError(PastePromptError):
    """Requested prompt key not found."""

    pass


class WorkflowGenerationError(PastePromptError):
    """Failed to generate workflow bundle."""

    pass


@dataclass
class Prompt:
    """Represents a single prompt definition."""

    key: str  # Unique identifier
    content: str  # The actual prompt text
    display_name: Optional[str] = None  # Human-readable name for menu
    description: Optional[str] = None  # Optional tooltip/description
    category: Optional[str] = None  # For grouping in submenus

    @property
    def menu_name(self) -> str:
        """Return display name or formatted key."""
        if self.display_name:
            return self.display_name
        # Convert 'save_plan' to 'Save Plan'
        return self.key.replace("_", " ").title()

    def get_menu_name(self, include_key: bool = False) -> str:
        """
        Return menu name with optional key prefix.

        Args:
            include_key: If True, prefix with [key] (e.g., "[investigate] Investigate")

        Returns:
            The formatted menu name
        """
        base_name = self.menu_name
        if include_key:
            return f"[{self.key}] {base_name}"
        return base_name


def load_prompts(config_path: Path) -> dict[str, Prompt]:
    """
    Load prompts from YAML configuration file.

    Args:
        config_path: Path to prompts.yaml file

    Returns:
        Dictionary mapping prompt keys to Prompt objects

    Raises:
        ConfigNotFoundError: If config file doesn't exist
        PromptsConfigError: If YAML is invalid or malformed
    """
    if not config_path.exists():
        raise ConfigNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise PromptsConfigError(f"Invalid YAML in configuration file: {e}")

    if data is None:
        raise PromptsConfigError("Configuration file is empty")

    # Validate structure
    errors = validate_prompts(data)
    if errors:
        raise PromptsConfigError("Configuration validation failed:\n  - " + "\n  - ".join(errors))

    # Parse prompts
    prompts: dict[str, Prompt] = {}
    prompts_data = data.get("prompts", {})

    for key, value in prompts_data.items():
        if isinstance(value, str):
            # Simple format: key: "content"
            prompts[key] = Prompt(key=key, content=value)
        elif isinstance(value, dict):
            # Full format with options
            prompts[key] = Prompt(
                key=key,
                content=value.get("content", ""),
                display_name=value.get("display_name"),
                description=value.get("description"),
                category=value.get("category"),
            )
        else:
            raise PromptsConfigError(f"Invalid prompt format for key '{key}'")

    return prompts


def validate_prompts(data: dict) -> list[str]:
    """
    Validate prompt configuration structure.

    Args:
        data: Parsed YAML data dictionary

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        errors.append("Configuration must be a dictionary")
        return errors

    # Check for prompts key
    if "prompts" not in data:
        errors.append("Missing required 'prompts' section")
        return errors

    prompts = data.get("prompts")
    if not isinstance(prompts, dict):
        errors.append("'prompts' must be a dictionary")
        return errors

    if not prompts:
        errors.append("'prompts' section is empty")
        return errors

    # Validate each prompt
    for key, value in prompts.items():
        if not isinstance(key, str):
            errors.append(f"Prompt key must be a string, got: {type(key).__name__}")
            continue

        if isinstance(value, str):
            if not value.strip():
                errors.append(f"Prompt '{key}' has empty content")
        elif isinstance(value, dict):
            if "content" not in value:
                errors.append(f"Prompt '{key}' missing required 'content' field")
            elif not isinstance(value["content"], str):
                errors.append(f"Prompt '{key}' content must be a string")
            elif not value["content"].strip():
                errors.append(f"Prompt '{key}' has empty content")
        else:
            errors.append(
                f"Prompt '{key}' must be a string or dictionary, got: {type(value).__name__}"
            )

    # Validate settings if present
    settings = data.get("settings")
    if settings is not None:
        if not isinstance(settings, dict):
            errors.append("'settings' must be a dictionary")
        else:
            if "prefix" in settings and not isinstance(settings["prefix"], str):
                errors.append("'settings.prefix' must be a string")
            if "include_key_in_name" in settings and not isinstance(
                settings["include_key_in_name"], bool
            ):
                errors.append("'settings.include_key_in_name' must be a boolean")

    return errors


def get_prompt_content(key: str, config_path: Path) -> str:
    """
    Retrieve content for a specific prompt by key.

    Args:
        key: The prompt identifier (e.g., 'investigate')
        config_path: Path to prompts.yaml

    Returns:
        The prompt content string

    Raises:
        ConfigNotFoundError: If config file doesn't exist
        PromptNotFoundError: If key doesn't exist
    """
    prompts = load_prompts(config_path)

    if key not in prompts:
        available = ", ".join(sorted(prompts.keys()))
        raise PromptNotFoundError(f"Prompt '{key}' not found. Available prompts: {available}")

    return prompts[key].content


def get_settings(config_path: Path) -> dict:
    """
    Get settings from configuration file.

    Args:
        config_path: Path to prompts.yaml

    Returns:
        Settings dictionary with defaults applied
    """
    if not config_path.exists():
        return {"prefix": "PastePrompt", "include_key_in_name": False}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return {"prefix": "PastePrompt", "include_key_in_name": False}

    settings = data.get("settings", {}) if data else {}

    return {
        "prefix": settings.get("prefix", "PastePrompt"),
        "include_key_in_name": settings.get("include_key_in_name", False),
    }

