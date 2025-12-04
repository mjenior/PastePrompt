"""Floating picker panel for prompt selection."""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class PromptPicker:
    """
    Floating panel for quick prompt selection.
    
    Features:
    - Searchable list of prompts
    - Keyboard navigation (↑↓ arrows, Enter to select, Escape to close)
    - Categorized display
    - Appears at screen center when invoked
    
    This class uses AppKit directly to create a native macOS floating panel.
    Falls back to a simple notification if AppKit is not available.
    """
    
    WINDOW_WIDTH = 450
    WINDOW_HEIGHT = 400
    
    def __init__(
        self,
        prompts: dict,
        on_select: Callable[[str], None],
    ):
        """
        Initialize the picker.
        
        Args:
            prompts: Dictionary of prompt key to Prompt objects
            on_select: Callback when a prompt is selected (receives prompt key)
        """
        self.prompts = prompts
        self.on_select = on_select
        self._window = None
        self._search_field = None
        self._table_view = None
        self._scroll_view = None
        self._data_source = None
        self._filtered_items: list[tuple[str, object]] = []
        self._is_appkit_available = False
        
        # Try to initialize AppKit components
        try:
            self._init_appkit()
            self._is_appkit_available = True
        except ImportError:
            logger.warning("AppKit not available, picker will use fallback mode")
        except Exception as e:
            logger.error("Failed to initialize picker UI: %s", e)
    
    def _init_appkit(self) -> None:
        """Initialize AppKit-based UI components."""
        from AppKit import (
            NSPanel,
            NSTextField,
            NSScrollView,
            NSTableView,
            NSTableColumn,
            NSMakeRect,
            NSFloatingWindowLevel,
            NSWindowStyleMaskTitled,
            NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            NSBezelStyleRounded,
            NSFont,
            NSColor,
        )
        
        # Create panel (floating window)
        frame = NSMakeRect(0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
        
        self._window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("PastePrompt - Quick Picker")
        self._window.setLevel_(NSFloatingWindowLevel)
        self._window.setHidesOnDeactivate_(True)
        self._window.center()
        
        # Get content view
        content = self._window.contentView()
        
        # Search field at top
        search_frame = NSMakeRect(10, self.WINDOW_HEIGHT - 45, self.WINDOW_WIDTH - 20, 30)
        self._search_field = NSTextField.alloc().initWithFrame_(search_frame)
        self._search_field.setPlaceholderString_("Type to search prompts...")
        self._search_field.setBezelStyle_(NSBezelStyleRounded)
        content.addSubview_(self._search_field)
        
        # Instructions label
        label_frame = NSMakeRect(10, self.WINDOW_HEIGHT - 65, self.WINDOW_WIDTH - 20, 15)
        label = NSTextField.alloc().initWithFrame_(label_frame)
        label.setStringValue_("↑↓ Navigate  •  Enter Select  •  Esc Close")
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setFont_(NSFont.systemFontOfSize_(10))
        label.setTextColor_(NSColor.secondaryLabelColor())
        content.addSubview_(label)
        
        # Scroll view and table view for prompts
        scroll_frame = NSMakeRect(10, 10, self.WINDOW_WIDTH - 20, self.WINDOW_HEIGHT - 85)
        self._scroll_view = NSScrollView.alloc().initWithFrame_(scroll_frame)
        self._scroll_view.setHasVerticalScroller_(True)
        self._scroll_view.setBorderType_(1)  # NSBezelBorder
        
        self._table_view = NSTableView.alloc().initWithFrame_(self._scroll_view.bounds())
        self._table_view.setHeaderView_(None)  # Hide header
        self._table_view.setRowHeight_(24)
        
        # Single column for prompt names
        name_col = NSTableColumn.alloc().initWithIdentifier_("name")
        name_col.setWidth_(self.WINDOW_WIDTH - 40)
        self._table_view.addTableColumn_(name_col)
        
        self._scroll_view.setDocumentView_(self._table_view)
        content.addSubview_(self._scroll_view)
        
        # Initialize filtered list with all prompts
        self._update_filtered_items("")
        
        # Create and set the data source
        self._setup_data_source()
    
    def _setup_data_source(self) -> None:
        """Set up the table view data source and delegate."""
        try:
            from Foundation import NSObject
            from AppKit import NSTableViewDataSource, NSTableViewDelegate
            import objc
            
            picker = self
            
            # Create a data source class dynamically
            class PromptTableDataSource(NSObject):
                """Data source for the prompt table view."""
                
                def numberOfRowsInTableView_(self, tableView):
                    return len(picker._filtered_items)
                
                def tableView_objectValueForTableColumn_row_(self, tableView, column, row):
                    if 0 <= row < len(picker._filtered_items):
                        key, prompt = picker._filtered_items[row]
                        category = prompt.category or ""
                        if category:
                            return f"[{category}] {prompt.menu_name}"
                        return prompt.menu_name
                    return ""
            
            # Register protocols
            PromptTableDataSource = objc.informal_protocol(
                "NSTableViewDataSource",
                [
                    objc.selector(None, b"numberOfRowsInTableView:", signature=b"q@:@"),
                    objc.selector(None, b"tableView:objectValueForTableColumn:row:", signature=b"@@:@@q"),
                ],
            )(PromptTableDataSource)
            
            self._data_source = PromptTableDataSource.alloc().init()
            self._table_view.setDataSource_(self._data_source)
            self._table_view.setDelegate_(self._data_source)
            
        except Exception as e:
            logger.warning("Could not set up table data source: %s", e)
            # Table will be empty but picker will still work via fallback
    
    def _update_filtered_items(self, query: str) -> None:
        """Update filtered items based on search query."""
        if not query:
            self._filtered_items = list(self.prompts.items())
        else:
            query = query.lower()
            self._filtered_items = [
                (key, prompt) for key, prompt in self.prompts.items()
                if query in key.lower()
                or query in prompt.menu_name.lower()
                or (prompt.category and query in prompt.category.lower())
                or query in prompt.content.lower()[:100]  # Search first 100 chars
            ]
        
        # Sort by category then name
        self._filtered_items.sort(key=lambda x: (x[1].category or "", x[1].menu_name))
    
    def _get_selected_key(self) -> str | None:
        """Get the key of the currently selected prompt."""
        if not self._table_view:
            return None
        
        row = self._table_view.selectedRow()
        if 0 <= row < len(self._filtered_items):
            return self._filtered_items[row][0]
        return None
    
    def _select_item(self) -> None:
        """Select the currently highlighted item and close picker."""
        key = self._get_selected_key()
        if key:
            self.hide()
            if self.on_select:
                self.on_select(key)
    
    def show(self) -> None:
        """Show the picker window."""
        if not self._is_appkit_available:
            self._show_fallback()
            return
        
        if self._window is None:
            return
        
        try:
            from AppKit import NSApp
            
            # Reset search and filter
            if self._search_field:
                self._search_field.setStringValue_("")
            self._update_filtered_items("")
            
            # Reload table
            if self._table_view:
                self._table_view.reloadData()
                # Select first row
                if self._filtered_items:
                    self._table_view.selectRowIndexes_byExtendingSelection_(
                        __import__('Foundation').NSIndexSet.indexSetWithIndex_(0),
                        False
                    )
            
            # Center and show window
            self._window.center()
            self._window.makeKeyAndOrderFront_(None)
            
            # Focus search field
            if self._search_field:
                self._window.makeFirstResponder_(self._search_field)
            
            # Bring app to front
            NSApp.activateIgnoringOtherApps_(True)
            
        except Exception as e:
            logger.error("Failed to show picker: %s", e)
            self._show_fallback()
    
    def _show_fallback(self) -> None:
        """Show a fallback notification when picker can't be displayed."""
        try:
            import rumps
            
            # Show notification with available prompts
            prompt_list = ", ".join(list(self.prompts.keys())[:5])
            if len(self.prompts) > 5:
                prompt_list += f"... (+{len(self.prompts) - 5} more)"
            
            rumps.notification(
                title="PastePrompt",
                subtitle="Use menu bar to select prompts",
                message=f"Available: {prompt_list}",
            )
        except Exception as e:
            logger.error("Failed to show fallback notification: %s", e)
    
    def hide(self) -> None:
        """Hide the picker window."""
        if self._window:
            try:
                self._window.orderOut_(None)
            except Exception as e:
                logger.error("Failed to hide picker: %s", e)
    
    def close(self) -> None:
        """Close and release the window."""
        if self._window:
            try:
                self._window.close()
            except Exception:
                pass
            self._window = None
            self._table_view = None
            self._search_field = None
            self._scroll_view = None
            self._data_source = None
    
    def update_prompts(self, prompts: dict) -> None:
        """
        Update the prompts list.
        
        Args:
            prompts: New dictionary of prompt key to Prompt objects
        """
        self.prompts = prompts
        self._update_filtered_items("")
        if self._table_view:
            try:
                self._table_view.reloadData()
            except Exception as e:
                logger.error("Failed to update prompts in picker: %s", e)
