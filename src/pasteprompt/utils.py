"""Utility functions for PastePrompt."""

import re


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        name: The string to sanitize

    Returns:
        A filesystem-safe string
    """
    # Remove/replace problematic characters
    sanitized = re.sub(r'[/\\:*?"<>|]', "-", name)
    # Remove multiple consecutive spaces or dashes
    sanitized = re.sub(r"[-\s]+", " ", sanitized)
    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()
    return sanitized


def truncate_text(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: The text to truncate
        max_length: Maximum length including suffix
        suffix: String to append when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_prompt_key(key: str) -> str:
    """
    Format a prompt key for display.

    Converts 'some_prompt_key' to 'Some Prompt Key'.

    Args:
        key: The prompt key

    Returns:
        Formatted display name
    """
    return key.replace("_", " ").title()

