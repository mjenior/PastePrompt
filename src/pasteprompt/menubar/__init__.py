"""PastePrompt Menu Bar Application.

Provides global hotkey access to PastePrompt snippets via a macOS menu bar app.

This module requires additional dependencies:
    pip install pasteprompt[menubar]

Or install directly:
    pip install rumps pyobjc-framework-Cocoa pyobjc-framework-Quartz watchdog
"""

from pasteprompt.menubar.app import PastePromptMenuBar, run_menubar_app

__all__ = [
    "PastePromptMenuBar",
    "run_menubar_app",
]

