"""macOS permission handling for accessibility features."""

import logging
import subprocess

logger = logging.getLogger(__name__)


def check_accessibility() -> bool:
    """
    Check if the app has Accessibility permissions.
    
    Accessibility permissions are required for:
    - Capturing global keyboard shortcuts
    - Simulating paste keystrokes
    
    Returns:
        True if accessibility is enabled, False otherwise
    """
    try:
        from ApplicationServices import AXIsProcessTrusted
        trusted = AXIsProcessTrusted()
        logger.debug("Accessibility trusted: %s", trusted)
        return bool(trusted)
    except ImportError:
        logger.warning("Could not import ApplicationServices, assuming accessibility is granted")
        return True
    except Exception as e:
        logger.error("Error checking accessibility: %s", e)
        return False


def request_accessibility() -> None:
    """
    Prompt the user to grant Accessibility permissions.
    
    Opens System Settings to the Privacy & Security > Accessibility pane
    where the user can enable permissions for this application.
    """
    logger.info("Requesting accessibility permissions")
    
    try:
        # Open System Settings to Privacy & Security > Accessibility
        subprocess.run([
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        ], check=False)
    except Exception as e:
        logger.error("Failed to open System Settings: %s", e)


def check_and_request_accessibility() -> bool:
    """
    Check accessibility and request if not granted.
    
    Returns:
        True if accessibility is granted, False if user needs to grant it
    """
    if check_accessibility():
        return True
    
    request_accessibility()
    return False

