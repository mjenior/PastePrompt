"""Tests for permissions handling."""

import pytest


class TestPermissions:
    """Test permission checking functions."""
    
    def test_check_accessibility_returns_bool(self):
        """Test that check_accessibility returns a boolean."""
        from pasteprompt.menubar.permissions import check_accessibility
        
        result = check_accessibility()
        
        assert isinstance(result, bool)
    
    def test_check_and_request_returns_bool(self):
        """Test that check_and_request_accessibility returns a boolean."""
        from pasteprompt.menubar.permissions import check_and_request_accessibility
        
        # Note: This may trigger a system dialog, so we just verify return type
        result = check_and_request_accessibility()
        
        assert isinstance(result, bool)

