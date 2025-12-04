"""Global hotkey registration for macOS."""

import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)

# macOS key codes for common keys
KEY_CODES: dict[str, int] = {
    'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4,
    'i': 34, 'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31,
    'p': 35, 'q': 12, 'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9,
    'w': 13, 'x': 7, 'y': 16, 'z': 6,
    '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22, '7': 26,
    '8': 28, '9': 25, '0': 29,
    'space': 49, 'return': 36, 'tab': 48, 'escape': 53,
    'up': 126, 'down': 125, 'left': 123, 'right': 124,
    'delete': 51, 'forwarddelete': 117,
    'f1': 122, 'f2': 120, 'f3': 99, 'f4': 118, 'f5': 96, 'f6': 97,
    'f7': 98, 'f8': 100, 'f9': 101, 'f10': 109, 'f11': 103, 'f12': 111,
}

# Modifier flag constants (will be set from Quartz when available)
MODIFIER_FLAGS: dict[str, int] = {}


def _init_modifier_flags() -> None:
    """Initialize modifier flags from Quartz constants."""
    global MODIFIER_FLAGS
    if MODIFIER_FLAGS:
        return
    
    try:
        from Quartz import (
            kCGEventFlagMaskCommand,
            kCGEventFlagMaskShift,
            kCGEventFlagMaskControl,
            kCGEventFlagMaskAlternate,
        )
        MODIFIER_FLAGS = {
            'cmd': kCGEventFlagMaskCommand,
            'command': kCGEventFlagMaskCommand,
            'shift': kCGEventFlagMaskShift,
            'ctrl': kCGEventFlagMaskControl,
            'control': kCGEventFlagMaskControl,
            'alt': kCGEventFlagMaskAlternate,
            'option': kCGEventFlagMaskAlternate,
            'opt': kCGEventFlagMaskAlternate,
        }
    except ImportError:
        # Fallback values if Quartz not available
        MODIFIER_FLAGS = {
            'cmd': 0x100000,
            'command': 0x100000,
            'shift': 0x20000,
            'ctrl': 0x40000,
            'control': 0x40000,
            'alt': 0x80000,
            'option': 0x80000,
            'opt': 0x80000,
        }


def parse_hotkey(hotkey_string: str) -> tuple[int, int]:
    """
    Parse a hotkey string into (keycode, modifiers).
    
    Args:
        hotkey_string: String like "cmd+shift+p" or "ctrl+alt+1"
        
    Returns:
        Tuple of (keycode, modifier_flags)
        
    Raises:
        ValueError: If hotkey string is invalid
        
    Examples:
        >>> parse_hotkey("cmd+p")
        (35, 1048576)
        >>> parse_hotkey("cmd+shift+p")
        (35, 1179648)
    """
    _init_modifier_flags()
    
    parts = hotkey_string.lower().replace(' ', '').split('+')
    
    modifiers = 0
    key = None
    
    for part in parts:
        if part in MODIFIER_FLAGS:
            modifiers |= MODIFIER_FLAGS[part]
        elif part in KEY_CODES:
            key = KEY_CODES[part]
        else:
            raise ValueError(f"Unknown key or modifier: '{part}' in hotkey '{hotkey_string}'")
    
    if key is None:
        raise ValueError(f"No key specified in hotkey: '{hotkey_string}'")
    
    return (key, modifiers)


def format_hotkey(hotkey_string: str) -> str:
    """
    Format a hotkey string for display with macOS symbols.
    
    Args:
        hotkey_string: String like "cmd+shift+p"
        
    Returns:
        Formatted string like "⌘⇧P"
    """
    symbols = {
        'cmd': '⌘', 'command': '⌘',
        'shift': '⇧',
        'ctrl': '⌃', 'control': '⌃',
        'alt': '⌥', 'option': '⌥', 'opt': '⌥',
    }
    
    parts = hotkey_string.lower().replace(' ', '').split('+')
    result = []
    key_part = None
    
    for part in parts:
        if part in symbols:
            result.append(symbols[part])
        else:
            key_part = part.upper()
    
    if key_part:
        result.append(key_part)
    
    return ''.join(result)


class HotkeyManager:
    """
    Manages global hotkey registration and handling.
    
    Uses macOS Quartz Event Taps to capture keyboard events system-wide.
    Requires Accessibility permissions to function.
    
    Example:
        manager = HotkeyManager()
        manager.register("cmd+shift+p", callback=my_callback)
        manager.start()
        # ... app runs ...
        manager.stop()
    """
    
    def __init__(self):
        """Initialize the hotkey manager."""
        self._hotkeys: dict[tuple[int, int], Callable[[], None]] = {}
        self._thread: threading.Thread | None = None
        self._running = False
        self._run_loop = None
        self._tap = None
        self._tap_source = None
    
    def register(self, hotkey_string: str, callback: Callable[[], None]) -> None:
        """
        Register a global hotkey.
        
        Args:
            hotkey_string: Hotkey like "cmd+shift+p"
            callback: Function to call when hotkey is pressed (no arguments)
            
        Raises:
            ValueError: If hotkey string is invalid
        """
        key_combo = parse_hotkey(hotkey_string)
        self._hotkeys[key_combo] = callback
        logger.info("Registered hotkey: %s -> %s", hotkey_string, format_hotkey(hotkey_string))
    
    def unregister(self, hotkey_string: str) -> None:
        """
        Unregister a global hotkey.
        
        Args:
            hotkey_string: The hotkey to unregister
        """
        try:
            key_combo = parse_hotkey(hotkey_string)
            if key_combo in self._hotkeys:
                del self._hotkeys[key_combo]
                logger.info("Unregistered hotkey: %s", hotkey_string)
        except ValueError:
            pass
    
    def _create_callback(self):
        """Create the event tap callback function."""
        # Import here to avoid issues if Quartz not available
        from Quartz import (
            kCGEventKeyDown,
            kCGEventFlagMaskCommand,
            kCGEventFlagMaskShift,
            kCGEventFlagMaskControl,
            kCGEventFlagMaskAlternate,
        )
        from Quartz.CoreGraphics import CGEventGetIntegerValueField, kCGKeyboardEventKeycode
        
        # Mask to only the modifier keys we care about
        modifier_mask = (
            kCGEventFlagMaskCommand |
            kCGEventFlagMaskShift |
            kCGEventFlagMaskControl |
            kCGEventFlagMaskAlternate
        )
        
        hotkeys = self._hotkeys
        
        def callback(proxy, event_type, event, refcon):
            if event_type != kCGEventKeyDown:
                return event
            
            # Get key code
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            
            # Get event flags properly using CGEventGetFlags
            from Quartz import CGEventGetFlags
            flags = CGEventGetFlags(event)
            modifiers = flags & modifier_mask
            
            # Check if this matches any registered hotkey
            key_combo = (keycode, modifiers)
            if key_combo in hotkeys:
                logger.debug("Hotkey triggered: keycode=%d, modifiers=0x%x", keycode, modifiers)
                # Call callback on a separate thread to not block event processing
                callback_func = hotkeys[key_combo]
                threading.Thread(target=callback_func, daemon=True).start()
                # Return None to consume the event (prevent it from reaching other apps)
                return None
            
            return event
        
        return callback
    
    def start(self) -> bool:
        """
        Start listening for hotkeys in a background thread.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            return True
        
        if not self._hotkeys:
            logger.warning("No hotkeys registered, not starting listener")
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="HotkeyListener")
        self._thread.start()
        return True
    
    def _run(self) -> None:
        """Run the event tap loop (called in background thread)."""
        try:
            from Quartz import (
                CGEventTapCreate,
                CGEventTapEnable,
                CFMachPortCreateRunLoopSource,
                CFRunLoopAddSource,
                CFRunLoopGetCurrent,
                CFRunLoopRun,
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                kCGEventKeyDown,
            )
            from Foundation import kCFRunLoopCommonModes
            
            # Create the callback
            callback = self._create_callback()
            
            # Create event tap
            self._tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                1 << kCGEventKeyDown,  # Only key down events
                callback,
                None,
            )
            
            if self._tap is None:
                logger.error(
                    "Failed to create event tap. "
                    "Please grant Accessibility permissions in System Settings > "
                    "Privacy & Security > Accessibility"
                )
                self._running = False
                return
            
            # Add to run loop
            self._tap_source = CFMachPortCreateRunLoopSource(None, self._tap, 0)
            self._run_loop = CFRunLoopGetCurrent()
            CFRunLoopAddSource(self._run_loop, self._tap_source, kCFRunLoopCommonModes)
            
            # Enable the tap
            CGEventTapEnable(self._tap, True)
            
            logger.info("Hotkey listener started")
            
            # Run the loop (blocks until stopped)
            CFRunLoopRun()
            
        except ImportError as e:
            logger.error("Quartz framework not available: %s", e)
            self._running = False
        except Exception as e:
            logger.error("Error in hotkey listener: %s", e)
            self._running = False
    
    def stop(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False
        
        try:
            if self._tap:
                from Quartz import CGEventTapEnable
                CGEventTapEnable(self._tap, False)
            
            if self._run_loop:
                from Quartz import CFRunLoopStop
                CFRunLoopStop(self._run_loop)
        except Exception as e:
            logger.error("Error stopping hotkey listener: %s", e)
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        self._tap = None
        self._tap_source = None
        self._run_loop = None
        self._thread = None
        
        logger.info("Hotkey listener stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if the hotkey listener is running."""
        return self._running and self._thread is not None and self._thread.is_alive()

