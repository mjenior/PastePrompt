"""Clipboard management and paste simulation."""

import logging
import threading
import time

logger = logging.getLogger(__name__)

# Key code for 'V' on macOS
KEY_V = 9


class PasteManager:
    """
    Manages clipboard operations and paste simulation.
    
    This class handles:
    - Getting and setting clipboard content
    - Simulating Cmd+V keystroke to paste
    - Optionally preserving and restoring original clipboard content
    
    Requires Accessibility permissions for keystroke simulation.
    """
    
    def __init__(self, restore_clipboard: bool = True):
        """
        Initialize the paste manager.
        
        Args:
            restore_clipboard: If True, restore original clipboard content
                after pasting prompt text (default: True)
        """
        self.restore_clipboard = restore_clipboard
        self._pasteboard = None
    
    def _get_pasteboard(self):
        """Get the system pasteboard (lazy initialization)."""
        if self._pasteboard is None:
            from AppKit import NSPasteboard
            self._pasteboard = NSPasteboard.generalPasteboard()
        return self._pasteboard
    
    def get_clipboard(self) -> str | None:
        """
        Get current clipboard content.
        
        Returns:
            Current clipboard text, or None if clipboard is empty or not text
        """
        try:
            from AppKit import NSPasteboard, NSStringPboardType
            pasteboard = self._get_pasteboard()
            content = pasteboard.stringForType_(NSStringPboardType)
            return content
        except Exception as e:
            logger.error("Failed to get clipboard: %s", e)
            return None
    
    def set_clipboard(self, text: str) -> bool:
        """
        Set clipboard content.
        
        Args:
            text: Text to copy to clipboard
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from AppKit import NSPasteboard, NSStringPboardType
            pasteboard = self._get_pasteboard()
            pasteboard.clearContents()
            success = pasteboard.setString_forType_(text, NSStringPboardType)
            return bool(success)
        except Exception as e:
            logger.error("Failed to set clipboard: %s", e)
            return False
    
    def simulate_paste(self) -> bool:
        """
        Simulate Cmd+V keystroke to paste clipboard content.
        
        This uses Quartz Core Graphics to create and post keyboard events.
        Requires Accessibility permissions.
        
        Returns:
            True if paste simulation was attempted, False on error
        """
        try:
            from Quartz import (
                CGEventCreateKeyboardEvent,
                CGEventPost,
                CGEventSetFlags,
                kCGHIDEventTap,
                kCGEventFlagMaskCommand,
            )
            
            # Small delay to ensure clipboard is ready
            time.sleep(0.05)
            
            # Key down with Cmd modifier
            event_down = CGEventCreateKeyboardEvent(None, KEY_V, True)
            if event_down is None:
                logger.error("Failed to create key down event")
                return False
            CGEventSetFlags(event_down, kCGEventFlagMaskCommand)
            CGEventPost(kCGHIDEventTap, event_down)
            
            # Small delay between down and up
            time.sleep(0.01)
            
            # Key up
            event_up = CGEventCreateKeyboardEvent(None, KEY_V, False)
            if event_up is None:
                logger.error("Failed to create key up event")
                return False
            CGEventSetFlags(event_up, kCGEventFlagMaskCommand)
            CGEventPost(kCGHIDEventTap, event_up)
            
            return True
            
        except ImportError as e:
            logger.error("Quartz not available: %s", e)
            return False
        except Exception as e:
            logger.error("Failed to simulate paste: %s", e)
            return False
    
    def paste_text(self, text: str) -> bool:
        """
        Paste text into the active application.
        
        This works by:
        1. Saving current clipboard (if restore_clipboard is True)
        2. Setting clipboard to the prompt text
        3. Simulating Cmd+V keystroke
        4. Restoring original clipboard after a delay (if restore_clipboard is True)
        
        Args:
            text: Text to paste into the active application
            
        Returns:
            True if paste was successful, False otherwise
        """
        try:
            # Save original clipboard content
            original = None
            if self.restore_clipboard:
                original = self.get_clipboard()
                logger.debug("Saved original clipboard content")
            
            # Set new content to clipboard
            if not self.set_clipboard(text):
                logger.error("Failed to set clipboard content")
                return False
            
            logger.debug("Set clipboard to prompt text (%d chars)", len(text))
            
            # Simulate paste keystroke
            if not self.simulate_paste():
                logger.error("Failed to simulate paste")
                # Try to restore clipboard even on failure
                if original is not None:
                    self.set_clipboard(original)
                return False
            
            logger.debug("Paste simulation completed")
            
            # Restore original clipboard after a delay
            if self.restore_clipboard and original is not None:
                def restore():
                    time.sleep(0.3)  # Wait for paste to complete
                    self.set_clipboard(original)
                    logger.debug("Restored original clipboard content")
                
                threading.Thread(target=restore, daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error("Paste failed: %s", e)
            return False

