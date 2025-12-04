"""Tests for hotkey parsing and registration."""

import pytest


class TestHotkeyParsing:
    """Test hotkey string parsing."""
    
    def test_parse_simple_hotkey(self):
        """Test parsing cmd+p."""
        from pasteprompt.menubar.hotkey import parse_hotkey, KEY_CODES
        
        keycode, modifiers = parse_hotkey("cmd+p")
        
        assert keycode == KEY_CODES['p']
        # Modifiers should include command flag
        assert modifiers > 0
    
    def test_parse_compound_hotkey(self):
        """Test parsing cmd+shift+p."""
        from pasteprompt.menubar.hotkey import parse_hotkey, KEY_CODES
        
        keycode, modifiers = parse_hotkey("cmd+shift+p")
        
        assert keycode == KEY_CODES['p']
        # Modifiers should be larger with shift added
        assert modifiers > 0
    
    def test_parse_with_spaces(self):
        """Test parsing with spaces around +."""
        from pasteprompt.menubar.hotkey import parse_hotkey, KEY_CODES
        
        keycode, modifiers = parse_hotkey("cmd + shift + p")
        
        assert keycode == KEY_CODES['p']
    
    def test_parse_alternate_names(self):
        """Test alternate modifier names."""
        from pasteprompt.menubar.hotkey import parse_hotkey
        
        # command vs cmd
        k1, m1 = parse_hotkey("command+p")
        k2, m2 = parse_hotkey("cmd+p")
        assert m1 == m2
        
        # option vs alt vs opt
        k1, m1 = parse_hotkey("option+p")
        k2, m2 = parse_hotkey("alt+p")
        k3, m3 = parse_hotkey("opt+p")
        assert m1 == m2 == m3
    
    def test_parse_number_key(self):
        """Test parsing hotkey with number key."""
        from pasteprompt.menubar.hotkey import parse_hotkey, KEY_CODES
        
        keycode, modifiers = parse_hotkey("cmd+shift+1")
        
        assert keycode == KEY_CODES['1']
    
    def test_parse_invalid_key(self):
        """Test error on invalid key."""
        from pasteprompt.menubar.hotkey import parse_hotkey
        
        with pytest.raises(ValueError, match="Unknown key"):
            parse_hotkey("cmd+invalid")
    
    def test_parse_missing_key(self):
        """Test error when only modifiers."""
        from pasteprompt.menubar.hotkey import parse_hotkey
        
        with pytest.raises(ValueError, match="No key specified"):
            parse_hotkey("cmd+shift")


class TestHotkeyFormat:
    """Test hotkey display formatting."""
    
    def test_format_simple(self):
        """Test formatting cmd+p."""
        from pasteprompt.menubar.hotkey import format_hotkey
        
        result = format_hotkey("cmd+p")
        
        assert "⌘" in result
        assert "P" in result
    
    def test_format_compound(self):
        """Test formatting cmd+shift+p."""
        from pasteprompt.menubar.hotkey import format_hotkey
        
        result = format_hotkey("cmd+shift+p")
        
        assert "⌘" in result
        assert "⇧" in result
        assert "P" in result
    
    def test_format_with_option(self):
        """Test formatting with option key."""
        from pasteprompt.menubar.hotkey import format_hotkey
        
        result = format_hotkey("cmd+option+v")
        
        assert "⌘" in result
        assert "⌥" in result
        assert "V" in result


class TestHotkeyManager:
    """Test hotkey manager functionality."""
    
    def test_register_hotkey(self):
        """Test registering a hotkey."""
        from pasteprompt.menubar.hotkey import HotkeyManager
        
        manager = HotkeyManager()
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        manager.register("cmd+shift+p", callback)
        
        # Verify hotkey was registered
        assert len(manager._hotkeys) == 1
    
    def test_unregister_hotkey(self):
        """Test unregistering a hotkey."""
        from pasteprompt.menubar.hotkey import HotkeyManager
        
        manager = HotkeyManager()
        manager.register("cmd+shift+p", lambda: None)
        manager.unregister("cmd+shift+p")
        
        assert len(manager._hotkeys) == 0
    
    def test_is_running_initially_false(self):
        """Test that manager is not running initially."""
        from pasteprompt.menubar.hotkey import HotkeyManager
        
        manager = HotkeyManager()
        
        assert not manager.is_running
    
    def test_register_multiple_hotkeys(self):
        """Test registering multiple hotkeys."""
        from pasteprompt.menubar.hotkey import HotkeyManager
        
        manager = HotkeyManager()
        manager.register("cmd+shift+1", lambda: None)
        manager.register("cmd+shift+2", lambda: None)
        manager.register("cmd+shift+3", lambda: None)
        
        assert len(manager._hotkeys) == 3
    
    def test_unregister_nonexistent_hotkey(self):
        """Test unregistering a hotkey that was never registered."""
        from pasteprompt.menubar.hotkey import HotkeyManager
        
        manager = HotkeyManager()
        # Should not raise an error
        manager.unregister("cmd+shift+x")
        
        assert len(manager._hotkeys) == 0


class TestKeyCodes:
    """Test key code mappings."""
    
    def test_all_letters_have_codes(self):
        """Test that all letters a-z have key codes."""
        from pasteprompt.menubar.hotkey import KEY_CODES
        
        for char in "abcdefghijklmnopqrstuvwxyz":
            assert char in KEY_CODES, f"Missing key code for '{char}'"
    
    def test_all_numbers_have_codes(self):
        """Test that all numbers 0-9 have key codes."""
        from pasteprompt.menubar.hotkey import KEY_CODES
        
        for char in "0123456789":
            assert char in KEY_CODES, f"Missing key code for '{char}'"
    
    def test_function_keys_have_codes(self):
        """Test that function keys f1-f12 have key codes."""
        from pasteprompt.menubar.hotkey import KEY_CODES
        
        for i in range(1, 13):
            key = f"f{i}"
            assert key in KEY_CODES, f"Missing key code for '{key}'"

