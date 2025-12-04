"""LaunchAgent management for auto-starting menu bar app on login."""

import logging
import plistlib
import subprocess
from pathlib import Path

from pasteprompt.config import (
    LAUNCH_AGENTS_DIR,
    LAUNCH_AGENT_LABEL,
    LAUNCH_AGENT_PLIST,
    get_python_executable,
)

logger = logging.getLogger(__name__)


def generate_launch_agent_plist(
    config_path: Path | None = None,
    hotkey: str = "cmd+shift+p",
    restore_clipboard: bool = True,
) -> dict:
    """
    Generate LaunchAgent plist content.
    
    Args:
        config_path: Path to prompts.yaml (optional)
        hotkey: Global hotkey string
        restore_clipboard: Whether to restore clipboard after paste
        
    Returns:
        Dictionary suitable for plistlib.dump()
    """
    python_path = get_python_executable()
    
    # Build command arguments
    args = [python_path, "-m", "pasteprompt", "menubar", "start"]
    
    if config_path:
        args.extend(["--config", str(config_path)])
    
    args.extend(["--hotkey", hotkey])
    
    if not restore_clipboard:
        args.append("--no-restore-clipboard")
    
    # Create log directory if needed
    log_dir = Path.home() / "Library" / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        "Label": LAUNCH_AGENT_LABEL,
        "ProgramArguments": args,
        "RunAtLoad": True,
        "KeepAlive": {
            "SuccessfulExit": False,  # Restart if it crashes
        },
        "StandardOutPath": str(log_dir / "pasteprompt.log"),
        "StandardErrorPath": str(log_dir / "pasteprompt.error.log"),
        "ProcessType": "Interactive",  # Required for accessibility
        "LimitLoadToSessionType": "Aqua",  # Only run in GUI sessions
    }


def install_launch_agent(
    config_path: Path | None = None,
    hotkey: str = "cmd+shift+p",
    restore_clipboard: bool = True,
) -> Path:
    """
    Install the LaunchAgent for auto-start on login.
    
    This creates a LaunchAgent plist file that will start the
    PastePrompt menu bar app automatically when the user logs in.
    
    Args:
        config_path: Path to prompts.yaml (optional)
        hotkey: Global hotkey string
        restore_clipboard: Whether to restore clipboard after paste
        
    Returns:
        Path to the installed plist file
        
    Raises:
        OSError: If plist file cannot be written
    """
    # Ensure LaunchAgents directory exists
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Unload existing agent if present
    if LAUNCH_AGENT_PLIST.exists():
        try:
            subprocess.run(
                ["launchctl", "unload", str(LAUNCH_AGENT_PLIST)],
                capture_output=True,
                check=False,
            )
        except Exception:
            pass
    
    # Generate plist content
    plist_content = generate_launch_agent_plist(
        config_path=config_path,
        hotkey=hotkey,
        restore_clipboard=restore_clipboard,
    )
    
    # Write plist file
    with open(LAUNCH_AGENT_PLIST, "wb") as f:
        plistlib.dump(plist_content, f)
    
    logger.info("Created LaunchAgent: %s", LAUNCH_AGENT_PLIST)
    
    # Load the agent
    result = subprocess.run(
        ["launchctl", "load", str(LAUNCH_AGENT_PLIST)],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        logger.warning("launchctl load returned non-zero: %s", result.stderr)
    else:
        logger.info("LaunchAgent loaded successfully")
    
    return LAUNCH_AGENT_PLIST


def uninstall_launch_agent() -> bool:
    """
    Uninstall the LaunchAgent.
    
    This removes the LaunchAgent plist file and unloads it,
    so the menu bar app will no longer start on login.
    
    Returns:
        True if uninstalled successfully, False if not found
    """
    if not LAUNCH_AGENT_PLIST.exists():
        logger.info("LaunchAgent not found: %s", LAUNCH_AGENT_PLIST)
        return False
    
    # Unload the agent
    result = subprocess.run(
        ["launchctl", "unload", str(LAUNCH_AGENT_PLIST)],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        logger.warning("launchctl unload returned non-zero: %s", result.stderr)
    
    # Remove the plist file
    LAUNCH_AGENT_PLIST.unlink()
    logger.info("Removed LaunchAgent: %s", LAUNCH_AGENT_PLIST)
    
    return True


def get_launch_agent_status() -> dict:
    """
    Get the current status of the LaunchAgent.
    
    Returns:
        Dictionary with status information:
        - installed: bool - Whether the plist file exists
        - plist_path: str | None - Path to plist if installed
        - running: bool - Whether the agent is currently running
        - pid: int | None - Process ID if running
        - config: dict | None - Current configuration from plist
    """
    status = {
        "installed": LAUNCH_AGENT_PLIST.exists(),
        "plist_path": str(LAUNCH_AGENT_PLIST) if LAUNCH_AGENT_PLIST.exists() else None,
        "running": False,
        "pid": None,
        "config": None,
    }
    
    # Read current configuration
    if status["installed"]:
        try:
            with open(LAUNCH_AGENT_PLIST, "rb") as f:
                status["config"] = plistlib.load(f)
        except Exception as e:
            logger.warning("Could not read plist: %s", e)
    
    # Check if running via launchctl
    result = subprocess.run(
        ["launchctl", "list", LAUNCH_AGENT_LABEL],
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        # Parse output to get PID
        # Output format: "PID\tStatus\tLabel" or just label info
        lines = result.stdout.strip().split("\n")
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 1:
                # First column is PID (or "-" if not running)
                pid_str = parts[0].strip()
                if pid_str.isdigit():
                    status["running"] = True
                    status["pid"] = int(pid_str)
                    break
    
    # Alternative check: look for running process
    if not status["running"]:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "pasteprompt.*menubar"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                if pids:
                    status["running"] = True
                    status["pid"] = int(pids[0])
        except Exception:
            pass
    
    return status


def start_launch_agent() -> bool:
    """
    Start the LaunchAgent if installed.
    
    Returns:
        True if started or already running, False if not installed
    """
    if not LAUNCH_AGENT_PLIST.exists():
        logger.error("LaunchAgent not installed")
        return False
    
    status = get_launch_agent_status()
    if status["running"]:
        logger.info("LaunchAgent already running (PID: %s)", status["pid"])
        return True
    
    result = subprocess.run(
        ["launchctl", "start", LAUNCH_AGENT_LABEL],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        logger.error("Failed to start LaunchAgent: %s", result.stderr)
        return False
    
    logger.info("LaunchAgent started")
    return True


def stop_launch_agent() -> bool:
    """
    Stop the LaunchAgent if running.
    
    Returns:
        True if stopped or not running, False on error
    """
    status = get_launch_agent_status()
    if not status["running"]:
        logger.info("LaunchAgent not running")
        return True
    
    result = subprocess.run(
        ["launchctl", "stop", LAUNCH_AGENT_LABEL],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        logger.error("Failed to stop LaunchAgent: %s", result.stderr)
        return False
    
    logger.info("LaunchAgent stopped")
    return True

