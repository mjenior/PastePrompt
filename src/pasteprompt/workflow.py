"""Automator workflow generation for macOS Services menu."""

import html
import shutil
import subprocess
import uuid
from pathlib import Path

from pasteprompt.prompts import Prompt, WorkflowGenerationError
from pasteprompt.config import SERVICES_DIR, get_python_executable


def _escape_xml(text: str) -> str:
    """
    Escape text for safe inclusion in XML.

    Args:
        text: The text to escape

    Returns:
        XML-safe escaped text
    """
    return html.escape(text, quote=True)


def get_workflow_name(
    prompt: Prompt, prefix: str = "PastePrompt", include_key_in_name: bool = False
) -> str:
    """
    Generate safe filename for workflow bundle.

    Args:
        prompt: The Prompt object
        prefix: Prefix for the workflow name
        include_key_in_name: If True, include key in menu name (e.g., "[investigate] Investigate")

    Returns:
        Safe filename string ending in .workflow
    """
    safe_name = prompt.get_menu_name(include_key=include_key_in_name)
    # Remove/replace problematic filesystem characters
    for char in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        safe_name = safe_name.replace(char, "-")
    # Remove any double spaces
    while "  " in safe_name:
        safe_name = safe_name.replace("  ", " ")
    return f"{prefix} - {safe_name}.workflow"


def generate_info_plist(
    prompt: Prompt, prefix: str = "PastePrompt", include_key_in_name: bool = False
) -> str:
    """
    Generate Info.plist content for the workflow bundle.

    Args:
        prompt: The Prompt object
        prefix: Prefix for the menu item
        include_key_in_name: If True, include key in menu name

    Returns:
        Info.plist XML content

    Note:
        NSSendTypes is empty so the service appears without requiring text selection.
        NSRequiredContext with NSTextContent ensures the service only appears in text contexts.
        NSReturnTypes specifies the service outputs text to insert at cursor position.
    """
    menu_name = prompt.get_menu_name(include_key=include_key_in_name)
    full_name = _escape_xml(f"{prefix} - {menu_name}")
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSServices</key>
    <array>
        <dict>
            <key>NSMenuItem</key>
            <dict>
                <key>default</key>
                <string>{full_name}</string>
            </dict>
            <key>NSMessage</key>
            <string>runWorkflowAsService</string>
            <key>NSRequiredContext</key>
            <dict>
                <key>NSTextContent</key>
                <array>
                    <string>Text</string>
                </array>
            </dict>
            <key>NSSendTypes</key>
            <array/>
            <key>NSReturnTypes</key>
            <array>
                <string>NSStringPboardType</string>
            </array>
        </dict>
    </array>
</dict>
</plist>'''


def generate_document_wflow(prompt_key: str, python_path: str, config_path: Path | None = None) -> str:
    """
    Generate document.wflow content for the workflow bundle.

    Args:
        prompt_key: The key to pass to the paste command
        python_path: Absolute path to the Python executable
        config_path: Optional path to the config file

    Returns:
        document.wflow XML content
    """
    uuid1 = str(uuid.uuid4()).upper()
    uuid2 = str(uuid.uuid4()).upper()

    # Build the command string (shell-safe quoting)
    if config_path:
        command = f'{python_path} -m pasteprompt paste "{prompt_key}" --config "{config_path}"'
    else:
        command = f'{python_path} -m pasteprompt paste "{prompt_key}"'

    # Escape for XML embedding
    command = _escape_xml(command)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AMApplicationBuild</key>
    <string>523</string>
    <key>AMApplicationVersion</key>
    <string>2.10</string>
    <key>AMDocumentVersion</key>
    <string>2</string>
    <key>actions</key>
    <array>
        <dict>
            <key>action</key>
            <dict>
                <key>AMAccepts</key>
                <dict>
                    <key>Container</key>
                    <string>List</string>
                    <key>Optional</key>
                    <true/>
                    <key>Types</key>
                    <array>
                        <string>com.apple.cocoa.string</string>
                    </array>
                </dict>
                <key>AMActionVersion</key>
                <string>2.0.3</string>
                <key>AMApplication</key>
                <array>
                    <string>Automator</string>
                </array>
                <key>AMCategory</key>
                <string>AMCategoryUtilities</string>
                <key>AMIconName</key>
                <string>Run Shell Script</string>
                <key>AMName</key>
                <string>Run Shell Script</string>
                <key>AMParameterProperties</key>
                <dict>
                    <key>COMMAND_STRING</key>
                    <dict/>
                    <key>CheckedForUserDefaultShell</key>
                    <dict/>
                    <key>inputMethod</key>
                    <dict/>
                    <key>shell</key>
                    <dict/>
                    <key>source</key>
                    <dict/>
                </dict>
                <key>AMProvides</key>
                <dict>
                    <key>Container</key>
                    <string>List</string>
                    <key>Types</key>
                    <array>
                        <string>com.apple.cocoa.string</string>
                    </array>
                </dict>
                <key>AMRequiredResources</key>
                <array/>
                <key>ActionBundlePath</key>
                <string>/System/Library/Automator/Run Shell Script.action</string>
                <key>ActionName</key>
                <string>Run Shell Script</string>
                <key>ActionParameters</key>
                <dict>
                    <key>COMMAND_STRING</key>
                    <string>{command}</string>
                    <key>CheckedForUserDefaultShell</key>
                    <true/>
                    <key>inputMethod</key>
                    <integer>1</integer>
                    <key>shell</key>
                    <string>/bin/zsh</string>
                    <key>source</key>
                    <string></string>
                </dict>
                <key>BundleIdentifier</key>
                <string>com.apple.RunShellScript</string>
                <key>CFBundleVersion</key>
                <string>2.0.3</string>
                <key>CanShowSelectedItemsWhenRun</key>
                <false/>
                <key>CanShowWhenRun</key>
                <true/>
                <key>GroupRecordsInOutput</key>
                <false/>
                <key>InputUUID</key>
                <string>{uuid1}</string>
                <key>OutputUUID</key>
                <string>{uuid2}</string>
            </dict>
        </dict>
    </array>
    <key>connectors</key>
    <dict/>
    <key>workflowMetaData</key>
    <dict>
        <key>workflowTypeIdentifier</key>
        <string>com.apple.Automator.servicesMenu</string>
    </dict>
</dict>
</plist>'''


def generate_workflow(
    prompt: Prompt,
    output_dir: Path | None = None,
    python_path: str | None = None,
    prefix: str = "PastePrompt",
    config_path: Path | None = None,
    include_key_in_name: bool = False,
) -> Path:
    """
    Generate a .workflow bundle for a single prompt.

    Args:
        prompt: The Prompt object to create workflow for
        output_dir: Directory to write workflow (default: ~/Library/Services/)
        python_path: Absolute path to pasteprompt Python executable
        prefix: Prefix for workflow names
        config_path: Optional path to the config file to embed in workflow
        include_key_in_name: If True, include key in menu name (e.g., "[investigate] Investigate")

    Returns:
        Path to the created .workflow bundle

    Raises:
        WorkflowGenerationError: If workflow generation fails
    """
    if output_dir is None:
        output_dir = SERVICES_DIR

    if python_path is None:
        python_path = get_python_executable()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate workflow bundle path
    workflow_name = get_workflow_name(prompt, prefix, include_key_in_name)
    workflow_path = output_dir / workflow_name

    try:
        # Remove existing workflow if present
        if workflow_path.exists():
            shutil.rmtree(workflow_path)

        # Create workflow bundle structure
        contents_dir = workflow_path / "Contents"
        contents_dir.mkdir(parents=True)

        # Create QuickLook directory (optional, for future thumbnail support)
        quicklook_dir = contents_dir / "QuickLook"
        quicklook_dir.mkdir(parents=True, exist_ok=True)

        # Write Info.plist
        info_plist_path = contents_dir / "Info.plist"
        info_plist_content = generate_info_plist(prompt, prefix, include_key_in_name)
        info_plist_path.write_text(info_plist_content, encoding="utf-8")

        # Write document.wflow
        document_wflow_path = contents_dir / "document.wflow"
        document_wflow_content = generate_document_wflow(prompt.key, python_path, config_path)
        document_wflow_path.write_text(document_wflow_content, encoding="utf-8")

        return workflow_path

    except OSError as e:
        raise WorkflowGenerationError(f"Failed to generate workflow for '{prompt.key}': {e}")


def generate_all_workflows(
    prompts: dict[str, Prompt],
    output_dir: Path | None = None,
    prefix: str = "PastePrompt",
    config_path: Path | None = None,
    include_key_in_name: bool = False,
) -> list[Path]:
    """
    Generate workflows for all prompts.

    Args:
        prompts: Dictionary of prompt key to Prompt objects
        output_dir: Directory to write workflows
        prefix: Prefix for workflow names
        config_path: Optional path to the config file to embed in workflows
        include_key_in_name: If True, include key in menu name (e.g., "[investigate] Investigate")

    Returns:
        List of paths to created workflow bundles
    """
    if output_dir is None:
        output_dir = SERVICES_DIR

    python_path = get_python_executable()
    created_workflows: list[Path] = []

    for prompt in prompts.values():
        workflow_path = generate_workflow(
            prompt=prompt,
            output_dir=output_dir,
            python_path=python_path,
            prefix=prefix,
            config_path=config_path,
            include_key_in_name=include_key_in_name,
        )
        created_workflows.append(workflow_path)

    return created_workflows


def cleanup_old_workflows(
    output_dir: Path | None = None, prefix: str = "PastePrompt"
) -> tuple[int, list[str]]:
    """
    Remove previously generated PastePrompt workflows.

    Args:
        output_dir: Directory containing workflows (default: ~/Library/Services/)
        prefix: Prefix to match for removal

    Returns:
        Tuple of (number of workflows removed, list of failed workflow names)
    """
    if output_dir is None:
        output_dir = SERVICES_DIR

    if not output_dir.exists():
        return 0, []

    removed_count = 0
    failed: list[str] = []
    pattern = f"{prefix} - "

    for item in output_dir.iterdir():
        if item.name.startswith(pattern) and item.name.endswith(".workflow"):
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed_count += 1
            except OSError:
                failed.append(item.name)

    return removed_count, failed


def refresh_services_menu() -> bool:
    """
    Refresh the macOS Services menu cache.

    Runs the pbs -update command to refresh Services.

    Returns:
        True if refresh was successful, False otherwise
    """
    try:
        subprocess.run(
            ["/System/Library/CoreServices/pbs", "-update"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def list_installed_workflows(output_dir: Path | None = None, prefix: str = "PastePrompt") -> list[str]:
    """
    List currently installed PastePrompt workflows.

    Args:
        output_dir: Directory containing workflows
        prefix: Prefix to match

    Returns:
        List of workflow names (without .workflow extension)
    """
    if output_dir is None:
        output_dir = SERVICES_DIR

    if not output_dir.exists():
        return []

    workflows: list[str] = []
    pattern = f"{prefix} - "

    for item in output_dir.iterdir():
        if item.name.startswith(pattern) and item.name.endswith(".workflow"):
            # Extract the display name
            name = item.name[len(pattern) : -len(".workflow")]
            workflows.append(name)

    return sorted(workflows)

