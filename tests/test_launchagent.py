"""Tests for LaunchAgent management."""

import pytest
from pathlib import Path


class TestGeneratePlist:
    """Test LaunchAgent plist generation."""
    
    def test_generate_basic_plist(self):
        """Test generating basic plist content."""
        from pasteprompt.launchagent import generate_launch_agent_plist, LAUNCH_AGENT_LABEL
        
        plist = generate_launch_agent_plist()
        
        assert plist["Label"] == LAUNCH_AGENT_LABEL
        assert plist["RunAtLoad"] is True
        assert "ProgramArguments" in plist
        assert len(plist["ProgramArguments"]) > 0
    
    def test_generate_plist_with_config(self, tmp_path):
        """Test plist with config path."""
        from pasteprompt.launchagent import generate_launch_agent_plist
        
        config_path = tmp_path / "prompts.yaml"
        plist = generate_launch_agent_plist(config_path=config_path)
        
        args = plist["ProgramArguments"]
        assert "--config" in args
        assert str(config_path) in args
    
    def test_generate_plist_with_hotkey(self):
        """Test plist with custom hotkey."""
        from pasteprompt.launchagent import generate_launch_agent_plist
        
        plist = generate_launch_agent_plist(hotkey="cmd+shift+v")
        
        args = plist["ProgramArguments"]
        assert "--hotkey" in args
        assert "cmd+shift+v" in args
    
    def test_generate_plist_no_restore_clipboard(self):
        """Test plist with restore_clipboard disabled."""
        from pasteprompt.launchagent import generate_launch_agent_plist
        
        plist = generate_launch_agent_plist(restore_clipboard=False)
        
        args = plist["ProgramArguments"]
        assert "--no-restore-clipboard" in args


class TestLaunchAgentStatus:
    """Test LaunchAgent status checking."""
    
    def test_get_status_returns_dict(self):
        """Test that get_launch_agent_status returns a dict."""
        from pasteprompt.launchagent import get_launch_agent_status
        
        status = get_launch_agent_status()
        
        assert isinstance(status, dict)
        assert "installed" in status
        assert "running" in status
        assert "plist_path" in status
        assert "pid" in status
    
    def test_status_installed_is_bool(self):
        """Test that installed status is a boolean."""
        from pasteprompt.launchagent import get_launch_agent_status
        
        status = get_launch_agent_status()
        
        assert isinstance(status["installed"], bool)
    
    def test_status_running_is_bool(self):
        """Test that running status is a boolean."""
        from pasteprompt.launchagent import get_launch_agent_status
        
        status = get_launch_agent_status()
        
        assert isinstance(status["running"], bool)

