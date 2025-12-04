"""PastePrompt Menu Bar Application."""

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class PastePromptMenuBar:
    """
    Menu bar application for PastePrompt.
    
    Provides:
    - Menu bar icon with dropdown of all prompts
    - Global hotkey to open quick picker
    - Config file watching for auto-reload
    - Clipboard-based paste into any application
    
    Requires:
    - rumps (menu bar framework)
    - pyobjc-framework-Cocoa (clipboard operations)
    - pyobjc-framework-Quartz (global hotkey)
    - watchdog (optional, for config watching)
    """
    
    ICON_NORMAL = "📋"
    ICON_ACTIVE = "✨"
    
    def __init__(
        self,
        config_path: Path | None = None,
        hotkey: str = "cmd+shift+p",
        restore_clipboard: bool = True,
        show_notifications: bool = True,
    ):
        """
        Initialize the menu bar app.
        
        Args:
            config_path: Path to prompts.yaml (uses default if None)
            hotkey: Global hotkey string (e.g., "cmd+shift+p")
            restore_clipboard: Whether to restore clipboard after paste
            show_notifications: Whether to show notification messages
        """
        import rumps
        
        self._rumps = rumps
        self._app: rumps.App | None = None
        
        # Store configuration
        self.config_path = config_path
        self.hotkey_string = hotkey
        self.restore_clipboard = restore_clipboard
        self.show_notifications = show_notifications
        
        # Initialize managers (lazy loaded)
        self._paste_manager = None
        self._hotkey_manager = None
        self._config_watcher = None
        self._picker = None
        
        # State
        self.prompts: dict = {}
        self.settings: dict = {}
        self._menu_items: dict = {}
    
    def _get_config_path(self) -> Path:
        """Get the configuration file path."""
        if self.config_path:
            return self.config_path
        
        from pasteprompt.config import get_config_path
        return get_config_path()
    
    def _load_config(self) -> bool:
        """
        Load prompts from configuration file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            from pasteprompt.prompts import load_prompts, get_settings
            
            config_path = self._get_config_path()
            self.prompts = load_prompts(config_path)
            self.settings = get_settings(config_path)
            
            logger.info("Loaded %d prompts from %s", len(self.prompts), config_path)
            return True
            
        except Exception as e:
            logger.error("Failed to load config: %s", e)
            if self.show_notifications:
                self._rumps.notification(
                    title="PastePrompt",
                    subtitle="Configuration Error",
                    message=str(e),
                )
            return False
    
    def _get_paste_manager(self):
        """Get or create the paste manager."""
        if self._paste_manager is None:
            from pasteprompt.menubar.paste import PasteManager
            self._paste_manager = PasteManager(restore_clipboard=self.restore_clipboard)
        return self._paste_manager
    
    def _build_menu(self) -> list:
        """Build the dropdown menu items."""
        menu_items = []
        
        # Group prompts by category
        categorized: dict[str, list[tuple[str, object]]] = {}
        for key, prompt in self.prompts.items():
            category = prompt.category or "General"
            if category not in categorized:
                categorized[category] = []
            categorized[category].append((key, prompt))
        
        # Add categorized prompts
        for category in sorted(categorized.keys()):
            # Add category header as disabled item
            header = self._rumps.MenuItem(f"── {category} ──")
            header.set_callback(None)  # Disabled
            menu_items.append(header)
            
            # Add prompts in category
            for key, prompt in sorted(categorized[category], key=lambda x: x[1].menu_name):
                # Create menu item
                item = self._rumps.MenuItem(
                    title=f"  {prompt.menu_name}",
                    callback=self._create_paste_callback(key),
                )
                menu_items.append(item)
                self._menu_items[key] = item
        
        # Add separator
        menu_items.append(None)  # None creates a separator in rumps
        
        # Quick picker item
        from pasteprompt.menubar.hotkey import format_hotkey
        hotkey_display = format_hotkey(self.hotkey_string)
        picker_item = self._rumps.MenuItem(
            title=f"⚡ Quick Picker  {hotkey_display}",
            callback=self._on_show_picker,
        )
        menu_items.append(picker_item)
        
        # Separator
        menu_items.append(None)
        
        # Utility items
        menu_items.append(self._rumps.MenuItem("↻ Reload Config", callback=self._on_reload_config))
        menu_items.append(self._rumps.MenuItem("⚙️  Open Config...", callback=self._on_open_config))
        
        # Separator and quit
        menu_items.append(None)
        menu_items.append(self._rumps.MenuItem("✕ Quit PastePrompt", callback=self._on_quit))
        
        return menu_items
    
    def _create_paste_callback(self, key: str):
        """Create a callback function for pasting a specific prompt."""
        def callback(sender):
            self._paste_prompt(key)
        return callback
    
    def _paste_prompt(self, key: str) -> None:
        """Paste the prompt content for the given key."""
        if key not in self.prompts:
            logger.error("Prompt not found: %s", key)
            return
        
        content = self.prompts[key].content
        
        logger.debug("Pasting prompt: %s (%d chars)", key, len(content))
        
        # Brief visual feedback - change icon
        if self._app:
            self._app.title = self.ICON_ACTIVE
        
        # Small delay to let the menu close
        def do_paste():
            import time
            time.sleep(0.1)  # Let menu close
            
            # Perform paste
            paste_manager = self._get_paste_manager()
            success = paste_manager.paste_text(content)
            
            # Reset icon after delay
            time.sleep(0.2)
            if self._app:
                self._app.title = self.ICON_NORMAL
            
            if not success and self.show_notifications:
                self._rumps.notification(
                    title="PastePrompt",
                    subtitle="Paste Failed",
                    message="Could not paste text. Check accessibility permissions.",
                )
        
        threading.Thread(target=do_paste, daemon=True).start()
    
    def _on_show_picker(self, sender=None) -> None:
        """Show the quick picker panel."""
        try:
            if self._picker is None:
                from pasteprompt.menubar.picker import PromptPicker
                self._picker = PromptPicker(
                    prompts=self.prompts,
                    on_select=self._paste_prompt,
                )
            self._picker.show()
        except Exception as e:
            logger.error("Failed to show picker: %s", e)
            if self.show_notifications:
                self._rumps.notification(
                    title="PastePrompt",
                    subtitle="Picker Error",
                    message=str(e),
                )
    
    def _on_reload_config(self, sender=None) -> None:
        """Reload configuration from file."""
        if self._load_config():
            # Rebuild menu
            if self._app:
                self._app.menu.clear()
                for item in self._build_menu():
                    if item is None:
                        self._app.menu.add(self._rumps.separator)
                    else:
                        self._app.menu.add(item)
            
            # Update picker if it exists
            if self._picker:
                self._picker.update_prompts(self.prompts)
            
            if self.show_notifications:
                self._rumps.notification(
                    title="PastePrompt",
                    subtitle="Config Reloaded",
                    message=f"Loaded {len(self.prompts)} prompts",
                )
    
    def _on_open_config(self, sender=None) -> None:
        """Open the config file in default editor."""
        import subprocess
        try:
            config_path = self._get_config_path()
            subprocess.run(["open", str(config_path)], check=False)
        except Exception as e:
            logger.error("Failed to open config: %s", e)
    
    def _on_quit(self, sender=None) -> None:
        """Quit the application."""
        self._cleanup()
        self._rumps.quit_application()
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up...")
        
        if self._hotkey_manager:
            self._hotkey_manager.stop()
            self._hotkey_manager = None
        
        if self._config_watcher:
            self._config_watcher.stop()
            self._config_watcher = None
        
        if self._picker:
            self._picker.close()
            self._picker = None
    
    def _setup_hotkey(self) -> bool:
        """Set up the global hotkey listener."""
        try:
            from pasteprompt.menubar.hotkey import HotkeyManager
            
            self._hotkey_manager = HotkeyManager()
            self._hotkey_manager.register(
                self.hotkey_string,
                callback=self._on_show_picker,
            )
            
            if self._hotkey_manager.start():
                logger.info("Global hotkey registered: %s", self.hotkey_string)
                return True
            else:
                logger.warning("Failed to start hotkey listener")
                return False
                
        except Exception as e:
            logger.error("Failed to setup hotkey: %s", e)
            return False
    
    def _setup_config_watcher(self) -> None:
        """Set up the config file watcher."""
        try:
            from pasteprompt.menubar.watcher import ConfigWatcher
            
            config_path = self._get_config_path()
            self._config_watcher = ConfigWatcher(
                path=config_path,
                callback=self._on_reload_config,
            )
            self._config_watcher.start()
            
        except Exception as e:
            logger.warning("Failed to setup config watcher: %s", e)
    
    def run(self) -> None:
        """Start the menu bar application."""
        # Check accessibility permissions
        from pasteprompt.menubar.permissions import check_accessibility, request_accessibility
        
        if not check_accessibility():
            logger.warning("Accessibility permissions not granted")
            request_accessibility()
            if self.show_notifications:
                self._rumps.notification(
                    title="PastePrompt",
                    subtitle="Permissions Required",
                    message="Please grant Accessibility permissions in System Settings.",
                )
        
        # Load configuration
        if not self._load_config():
            logger.error("Failed to load configuration, exiting")
            return
        
        # Build menu
        menu_items = self._build_menu()
        
        # Create the app
        self._app = self._rumps.App(
            name="PastePrompt",
            title=self.ICON_NORMAL,
            quit_button=None,  # We handle quit ourselves
        )
        
        # Add menu items
        for item in menu_items:
            if item is None:
                self._app.menu.add(self._rumps.separator)
            else:
                self._app.menu.add(item)
        
        # Setup global hotkey
        self._setup_hotkey()
        
        # Setup config watcher
        self._setup_config_watcher()
        
        logger.info("PastePrompt menu bar app starting...")
        logger.info("Global hotkey: %s", self.hotkey_string)
        logger.info("Prompts loaded: %d", len(self.prompts))
        
        # Run the app (blocks until quit)
        self._app.run()


def run_menubar_app(
    config_path: Path | None = None,
    hotkey: str = "cmd+shift+p",
    restore_clipboard: bool = True,
    show_notifications: bool = True,
) -> None:
    """
    Run the PastePrompt menu bar application.
    
    This is the main entry point for the menu bar app.
    
    Args:
        config_path: Path to prompts.yaml (uses default if None)
        hotkey: Global hotkey string (e.g., "cmd+shift+p")
        restore_clipboard: Whether to restore clipboard after paste
        show_notifications: Whether to show notification messages
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    app = PastePromptMenuBar(
        config_path=config_path,
        hotkey=hotkey,
        restore_clipboard=restore_clipboard,
        show_notifications=show_notifications,
    )
    app.run()

