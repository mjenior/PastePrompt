"""Configuration file watcher for auto-reload."""

import logging
import threading
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """
    Watches the configuration file for changes and triggers reload.
    
    Uses the watchdog library for efficient file system monitoring.
    Changes are debounced to avoid rapid-fire reloads when files
    are being edited.
    """
    
    def __init__(self, path: Path, callback: Callable[[], None], debounce_delay: float = 0.5):
        """
        Initialize the config watcher.
        
        Args:
            path: Path to the config file to watch
            callback: Function to call when file changes
            debounce_delay: Seconds to wait before triggering callback (default: 0.5)
        """
        self.path = path.resolve()
        self.callback = callback
        self.debounce_delay = debounce_delay
        self._observer = None
        self._debounce_timer: threading.Timer | None = None
    
    def _on_modified(self, event_path: Path) -> None:
        """Handle file modification event."""
        # Check if this is our target file
        if event_path.resolve() != self.path:
            return
        
        # Debounce rapid changes
        if self._debounce_timer:
            self._debounce_timer.cancel()
        
        self._debounce_timer = threading.Timer(
            self.debounce_delay,
            self._trigger_callback,
        )
        self._debounce_timer.start()
    
    def _trigger_callback(self) -> None:
        """Trigger the callback after debounce delay."""
        logger.info("Config file changed, triggering reload")
        try:
            self.callback()
        except Exception as e:
            logger.error("Failed to reload config: %s", e)
    
    def start(self) -> None:
        """Start watching the config file."""
        if self._observer is not None:
            return
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileModifiedEvent
            
            # Create event handler
            watcher = self
            
            class ConfigFileHandler(FileSystemEventHandler):
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    watcher._on_modified(Path(event.src_path))
            
            handler = ConfigFileHandler()
            
            self._observer = Observer()
            self._observer.schedule(
                handler,
                str(self.path.parent),  # Watch the directory
                recursive=False,
            )
            self._observer.start()
            
            logger.info("Watching config file: %s", self.path)
            
        except ImportError:
            logger.warning("watchdog not installed, config auto-reload disabled")
        except Exception as e:
            logger.error("Failed to start config watcher: %s", e)
    
    def stop(self) -> None:
        """Stop watching the config file."""
        if self._debounce_timer:
            self._debounce_timer.cancel()
            self._debounce_timer = None
        
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=1.0)
            self._observer = None
            logger.info("Stopped watching config file")

