"""CLI interface for PastePrompt."""

from pathlib import Path

import click
import yaml

from pasteprompt import __version__
from pasteprompt.config import (
    DEFAULT_PROMPTS_FILE,
    SERVICES_DIR,
    create_default_config,
    ensure_config_dir,
    get_config_path,
)
from pasteprompt.pasteboard import output_for_service
from pasteprompt.prompts import (
    ConfigNotFoundError,
    PastePromptError,
    PromptNotFoundError,
    PromptsConfigError,
    get_prompt_content,
    get_settings,
    load_prompts,
    validate_prompts,
)
from pasteprompt.workflow import (
    cleanup_old_workflows,
    generate_all_workflows,
    list_installed_workflows,
    refresh_services_menu,
)


@click.group()
@click.version_option(version=__version__, prog_name="pasteprompt")
def cli():
    """PastePrompt - Quick prompt snippets for your Services menu."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to prompts.yaml file",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing workflows",
)
def build(config: str | None, force: bool):
    """
    Build Automator workflows from prompts configuration.

    Generates .workflow bundles in ~/Library/Services/ for each
    prompt defined in your prompts.yaml file.

    \b
    Example:
        pasteprompt build
        pasteprompt build --config ./my-prompts.yaml
    """
    try:
        config_path = get_config_path(config)
        click.echo(f"Loading prompts from {config_path}...")

        prompts = load_prompts(config_path)
        settings = get_settings(config_path)
        prefix = settings.get("prefix", "PastePrompt")

        click.echo(f"Found {len(prompts)} prompts")

        # Clean existing workflows if force flag is set
        if force:
            removed, failed = cleanup_old_workflows(prefix=prefix)
            if removed > 0:
                click.echo(f"Removed {removed} existing workflows")
            if failed:
                click.echo(
                    f"{click.style('!', fg='yellow')} Could not remove {len(failed)} workflows"
                )

        include_key = settings.get("include_key_in_name", False)

        click.echo("\nGenerating workflows:")

        # Generate workflows
        created = generate_all_workflows(
            prompts=prompts,
            prefix=prefix,
            config_path=config_path,
            include_key_in_name=include_key,
        )

        for workflow_path in created:
            click.echo(f"  {click.style('✓', fg='green')} {workflow_path.name}")

        click.echo(f"\n{click.style('✓', fg='green')} Generated {len(created)} workflows in {SERVICES_DIR}/")

        # Refresh services menu
        if refresh_services_menu():
            click.echo(f"{click.style('✓', fg='green')} Services menu refreshed")
        else:
            click.echo(
                f"{click.style('!', fg='yellow')} Could not refresh Services menu automatically.\n"
                "  You may need to log out and back in, or run:\n"
                "  /System/Library/CoreServices/pbs -update"
            )

        click.echo(
            f"\nYour prompts are now available in:\n"
            f"  Right-click menu > Services > {prefix} - [name]\n"
            f"  or\n"
            f"  App menu > Services > {prefix} - [name]"
        )

    except ConfigNotFoundError as e:
        raise click.ClickException(str(e))
    except PromptsConfigError as e:
        raise click.ClickException(f"Configuration error: {e}")
    except PastePromptError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("key")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to prompts.yaml file",
)
def paste(key: str, config: str | None):
    """
    Output prompt content for the given key.

    This command is called by the generated Automator workflows.
    It outputs the prompt content to stdout for the workflow to capture.

    \b
    Example:
        pasteprompt paste investigate
    """
    try:
        config_path = get_config_path(config)
        content = get_prompt_content(key, config_path)
        output_for_service(content)

    except ConfigNotFoundError as e:
        # For paste command, we output to stderr to not interfere with stdout
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except PromptNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except PastePromptError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command("list")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to prompts.yaml file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show full prompt content",
)
def list_prompts(config: str | None, verbose: bool):
    """
    List all available prompts.

    \b
    Example:
        pasteprompt list
        pasteprompt list --verbose
    """
    try:
        config_path = get_config_path(config)
        prompts = load_prompts(config_path)
        settings = get_settings(config_path)

        click.echo(f"Prompts from: {config_path}\n")

        # Group by category if categories exist
        categorized: dict[str, list] = {}
        for key, prompt in prompts.items():
            category = prompt.category or "Uncategorized"
            if category not in categorized:
                categorized[category] = []
            categorized[category].append((key, prompt))

        for category, items in sorted(categorized.items()):
            click.echo(click.style(f"=== {category} ===", bold=True))
            for key, prompt in sorted(items, key=lambda x: x[0]):
                click.echo(f"  {click.style(key, fg='cyan')}: {prompt.menu_name}")
                if prompt.description:
                    click.echo(f"    {click.style(prompt.description, dim=True)}")
                if verbose:
                    # Show content with indentation
                    content_lines = prompt.content.split("\n")
                    click.echo(f"    {click.style('Content:', fg='yellow')}")
                    for line in content_lines:
                        click.echo(f"      {line}")
            click.echo()

        click.echo(f"Total: {len(prompts)} prompts")

        # Also show installed workflows
        prefix = settings.get("prefix", "PastePrompt")
        installed = list_installed_workflows(prefix=prefix)
        if installed:
            click.echo(f"Installed workflows: {len(installed)}")

    except ConfigNotFoundError as e:
        raise click.ClickException(str(e))
    except PastePromptError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing configuration",
)
def init(force: bool):
    """
    Initialize PastePrompt configuration.

    Creates ~/.config/pasteprompt/prompts.yaml with example prompts.
    """
    config_path = DEFAULT_PROMPTS_FILE

    if config_path.exists() and not force:
        click.echo(f"Configuration already exists: {config_path}")
        click.echo("Use --force to overwrite")
        return

    try:
        ensure_config_dir()
        create_default_config(config_path)

        click.echo(f"{click.style('✓', fg='green')} Created configuration directory: {config_path.parent}/")
        click.echo(f"{click.style('✓', fg='green')} Created example prompts file: prompts.yaml")
        click.echo(
            f"\nNext steps:\n"
            f"  1. Edit {config_path}\n"
            f"  2. Run 'pasteprompt build' to generate workflows"
        )

    except OSError as e:
        raise click.ClickException(f"Failed to create configuration: {e}")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to prompts.yaml file",
)
def validate(config: str | None):
    """
    Validate prompts configuration file.

    Checks YAML syntax and required fields.
    """
    try:
        config_path = get_config_path(config)
        click.echo(f"Validating: {config_path}")

        # Load and parse YAML
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            raise click.ClickException("Configuration file is empty")

        # Validate structure
        errors = validate_prompts(data)

        if errors:
            click.echo(f"\n{click.style('Validation failed:', fg='red')}")
            for error in errors:
                click.echo(f"  - {error}")
            raise SystemExit(1)

        # Try to load prompts to catch any other issues
        prompts = load_prompts(config_path)

        click.echo(f"\n{click.style('✓', fg='green')} Configuration is valid")
        click.echo(f"  Found {len(prompts)} prompts")

        # List prompts
        for key, prompt in prompts.items():
            click.echo(f"  - {key}: {prompt.menu_name}")

    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML syntax: {e}")
    except ConfigNotFoundError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.option(
    "--prefix",
    "-p",
    default="PastePrompt",
    help="Workflow prefix to clean (default: PastePrompt)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clean(prefix: str, yes: bool):
    """
    Remove all PastePrompt workflows from Services.

    This removes any .workflow files starting with the specified prefix
    from ~/Library/Services/.
    """
    installed = list_installed_workflows(prefix=prefix)

    if not installed:
        click.echo(f"No {prefix} workflows found in {SERVICES_DIR}")
        return

    click.echo(f"Found {len(installed)} workflows to remove:")
    for name in installed:
        click.echo(f"  - {prefix} - {name}")

    if not yes:
        if not click.confirm("\nRemove these workflows?"):
            click.echo("Aborted")
            return

    removed, failed = cleanup_old_workflows(prefix=prefix)
    click.echo(f"\n{click.style('✓', fg='green')} Removed {removed} workflows")

    if failed:
        click.echo(f"{click.style('!', fg='yellow')} Could not remove {len(failed)} workflows:")
        for name in failed:
            click.echo(f"  - {name}")

    if refresh_services_menu():
        click.echo(f"{click.style('✓', fg='green')} Services menu refreshed")


@cli.command()
def refresh():
    """
    Refresh Services menu to recognize new workflows.

    Runs the necessary system commands to update the Services menu.
    """
    click.echo("Refreshing Services menu...")

    if refresh_services_menu():
        click.echo(f"{click.style('✓', fg='green')} Services menu refreshed successfully")
    else:
        click.echo(
            f"{click.style('!', fg='yellow')} Could not refresh automatically.\n"
            "Try these alternatives:\n"
            "  1. Log out and back in\n"
            "  2. Run: /System/Library/CoreServices/pbs -update\n"
            "  3. Restart Finder: killall Finder"
        )


@cli.command()
def status():
    """
    Show current PastePrompt status.

    Displays configuration location and installed workflows.
    """
    click.echo(click.style("PastePrompt Status", bold=True))
    click.echo(f"Version: {__version__}\n")

    # Check for config file
    try:
        config_path = get_config_path()
        click.echo(f"Configuration: {click.style(str(config_path), fg='green')}")

        prompts = load_prompts(config_path)
        settings = get_settings(config_path)
        prefix = settings.get("prefix", "PastePrompt")
        include_key = settings.get("include_key_in_name", False)

        click.echo(f"Prompts defined: {len(prompts)}")

        # Check installed workflows
        installed = list_installed_workflows(prefix=prefix)
        click.echo(f"Workflows installed: {len(installed)}")

        # Check if they match - use get_menu_name with include_key setting
        installed_names = set(installed)
        prompt_menu_names = {p.get_menu_name(include_key=include_key) for p in prompts.values()}

        if installed_names == prompt_menu_names:
            click.echo(f"\n{click.style('✓', fg='green')} Workflows are up to date")
        else:
            missing = prompt_menu_names - installed_names
            extra = installed_names - prompt_menu_names

            if missing:
                click.echo(f"\n{click.style('!', fg='yellow')} Missing workflows:")
                for name in sorted(missing):
                    click.echo(f"  - {name}")

            if extra:
                click.echo(f"\n{click.style('!', fg='yellow')} Extra workflows (not in config):")
                for name in sorted(extra):
                    click.echo(f"  - {name}")

            click.echo(f"\nRun 'pasteprompt build --force' to sync")

    except ConfigNotFoundError:
        click.echo(f"Configuration: {click.style('Not found', fg='red')}")
        click.echo("\nRun 'pasteprompt init' to create a configuration file")


@cli.group()
def menubar():
    """Menu bar application with global hotkey support."""
    pass


@menubar.command("start")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to prompts.yaml file",
)
@click.option(
    "--hotkey",
    "-k",
    default="cmd+shift+p",
    help="Global hotkey (default: cmd+shift+p)",
)
@click.option(
    "--no-restore-clipboard",
    is_flag=True,
    help="Don't restore clipboard after paste",
)
@click.option(
    "--no-notifications",
    is_flag=True,
    help="Disable notification messages",
)
def menubar_start(config: str | None, hotkey: str, no_restore_clipboard: bool, no_notifications: bool):
    """
    Start the PastePrompt menu bar application.

    Runs in the foreground. The app provides:
    - Menu bar icon with dropdown of all prompts
    - Global hotkey (default: Cmd+Shift+P) for quick picker
    - Auto-reload when config file changes

    Use 'pasteprompt menubar install' for automatic startup on login.

    \b
    Example:
        pasteprompt menubar start
        pasteprompt menubar start --hotkey "cmd+shift+v"
    """
    # Check for required dependencies
    try:
        import rumps  # noqa: F401
    except ImportError:
        raise click.ClickException(
            "Menu bar dependencies not installed.\n"
            "Install with: pip install pasteprompt[menubar]\n"
            "Or: pip install rumps pyobjc-framework-Cocoa pyobjc-framework-Quartz watchdog"
        )

    # Validate hotkey format
    try:
        from pasteprompt.menubar.hotkey import parse_hotkey, format_hotkey
        parse_hotkey(hotkey)
        hotkey_display = format_hotkey(hotkey)
    except ValueError as e:
        raise click.ClickException(f"Invalid hotkey format: {e}")

    try:
        from pasteprompt.menubar import run_menubar_app

        config_path = Path(config) if config else None

        click.echo("Starting PastePrompt menu bar app...")
        click.echo(f"Global hotkey: {hotkey} ({hotkey_display})")
        click.echo("Press Ctrl+C to quit\n")

        run_menubar_app(
            config_path=config_path,
            hotkey=hotkey,
            restore_clipboard=not no_restore_clipboard,
            show_notifications=not no_notifications,
        )

    except KeyboardInterrupt:
        click.echo("\nStopped")
    except PastePromptError as e:
        raise click.ClickException(str(e))


@menubar.command("install")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to prompts.yaml file",
)
@click.option(
    "--hotkey",
    "-k",
    default="cmd+shift+p",
    help="Global hotkey",
)
def menubar_install(config: str | None, hotkey: str):
    """
    Install the menu bar app to start automatically on login.

    Creates a LaunchAgent that starts the menu bar app when you log in.

    \b
    Example:
        pasteprompt menubar install
        pasteprompt menubar install --hotkey "cmd+shift+v"
    """
    # Validate hotkey format
    try:
        from pasteprompt.menubar.hotkey import parse_hotkey
        parse_hotkey(hotkey)
    except ImportError:
        # Hotkey module not available, skip validation (will fail at runtime if invalid)
        pass
    except ValueError as e:
        raise click.ClickException(f"Invalid hotkey format: {e}")

    try:
        from pasteprompt.launchagent import install_launch_agent

        config_path = Path(config) if config else None

        plist_path = install_launch_agent(
            config_path=config_path,
            hotkey=hotkey,
        )

        click.echo(f"{click.style('✓', fg='green')} Installed LaunchAgent: {plist_path}")
        click.echo("\nThe menu bar app will start automatically on login.")
        click.echo("To start now, run: pasteprompt menubar start")

    except Exception as e:
        raise click.ClickException(f"Failed to install LaunchAgent: {e}")


@menubar.command("uninstall")
def menubar_uninstall():
    """
    Remove the menu bar app from login items.

    Removes the LaunchAgent so the app won't start on login.
    """
    try:
        from pasteprompt.launchagent import uninstall_launch_agent

        if uninstall_launch_agent():
            click.echo(f"{click.style('✓', fg='green')} Removed LaunchAgent")
            click.echo("The menu bar app will no longer start on login.")
        else:
            click.echo("LaunchAgent not found (already uninstalled)")

    except Exception as e:
        raise click.ClickException(f"Failed to uninstall LaunchAgent: {e}")


@menubar.command("status")
def menubar_status():
    """
    Show menu bar app status.

    Displays whether the LaunchAgent is installed and if the app is running.
    """
    from pasteprompt.launchagent import get_launch_agent_status

    status = get_launch_agent_status()

    click.echo(click.style("Menu Bar App Status", bold=True))
    click.echo()

    if status["installed"]:
        click.echo(f"LaunchAgent: {click.style('Installed', fg='green')}")
        click.echo(f"  Path: {status['plist_path']}")
    else:
        click.echo(f"LaunchAgent: {click.style('Not installed', fg='yellow')}")
        click.echo("  Run 'pasteprompt menubar install' to enable auto-start")

    click.echo()

    if status["running"]:
        click.echo(f"App Status: {click.style('Running', fg='green')}")
        if status["pid"]:
            click.echo(f"  PID: {status['pid']}")
    else:
        click.echo(f"App Status: {click.style('Not running', fg='yellow')}")
        click.echo("  Run 'pasteprompt menubar start' to start the app")

    click.echo()

    # Check dependencies
    try:
        import rumps  # noqa: F401
        click.echo(f"Dependencies: {click.style('Installed', fg='green')}")
    except ImportError:
        click.echo(f"Dependencies: {click.style('Not installed', fg='red')}")
        click.echo("  Run: pip install pasteprompt[menubar]")


if __name__ == "__main__":
    cli()

