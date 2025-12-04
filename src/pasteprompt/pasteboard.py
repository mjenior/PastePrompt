"""macOS pasteboard and text output handling."""

import os
import subprocess
import sys


def _get_utf8_env() -> dict[str, str]:
    """
    Get environment with UTF-8 locale settings.

    Returns:
        Copy of current environment with LANG set for UTF-8
    """
    env = os.environ.copy()
    env["LANG"] = "en_US.UTF-8"
    return env


def output_for_service(text: str) -> None:
    """
    Output text for Automator service to capture.

    The workflow is configured to take stdout as output,
    so simply printing is sufficient.

    Args:
        text: The prompt content to output
    """
    print(text, end="")  # No trailing newline
    sys.stdout.flush()  # Ensure immediate output


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text directly to system clipboard using pbcopy.

    Args:
        text: The text to copy to clipboard

    Returns:
        True if successful, False otherwise
    """
    try:
        process = subprocess.Popen(
            ["pbcopy"],
            stdin=subprocess.PIPE,
            env=_get_utf8_env(),
        )
        process.communicate(text.encode("utf-8"))
        return process.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def get_clipboard_content() -> str | None:
    """
    Get current clipboard content using pbpaste.

    Returns:
        Clipboard text content, or None if failed
    """
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            env=_get_utf8_env(),
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (OSError, subprocess.SubprocessError):
        return None

