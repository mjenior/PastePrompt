"""Tests for paste manager."""

import pytest


class TestPasteManagerInit:
    """Test paste manager initialization."""
    
    def test_default_restore_clipboard(self):
        """Test default restore_clipboard is True."""
        from pasteprompt.menubar.paste import PasteManager
        
        manager = PasteManager()
        
        assert manager.restore_clipboard is True
    
    def test_disable_restore_clipboard(self):
        """Test disabling restore_clipboard."""
        from pasteprompt.menubar.paste import PasteManager
        
        manager = PasteManager(restore_clipboard=False)
        
        assert manager.restore_clipboard is False


# Note: Full clipboard tests require macOS AppKit which may not be available in CI
# These tests are marked to skip if AppKit is not available


@pytest.fixture
def skip_if_no_appkit():
    """Skip test if AppKit is not available."""
    try:
        from AppKit import NSPasteboard  # noqa: F401
    except ImportError:
        pytest.skip("AppKit not available")


class TestPasteManagerClipboard:
    """Test clipboard operations (requires AppKit)."""
    
    def test_set_and_get_clipboard(self, skip_if_no_appkit):
        """Test setting and getting clipboard content."""
        from pasteprompt.menubar.paste import PasteManager
        
        manager = PasteManager(restore_clipboard=False)
        
        test_text = "Test clipboard content"
        assert manager.set_clipboard(test_text)
        
        result = manager.get_clipboard()
        assert result == test_text
    
    def test_set_clipboard_unicode(self, skip_if_no_appkit):
        """Test clipboard with unicode content."""
        from pasteprompt.menubar.paste import PasteManager
        
        manager = PasteManager(restore_clipboard=False)
        
        test_text = "Unicode test: 你好世界 🎉"
        assert manager.set_clipboard(test_text)
        
        result = manager.get_clipboard()
        assert result == test_text

