"""PastePrompt - Quick prompt snippets for macOS Services menu."""

__version__ = "0.1.0"
__author__ = "Matt Jenior"

# Core data classes
from pasteprompt.prompts import Prompt

# Exception classes
from pasteprompt.prompts import (
    PastePromptError,
    ConfigNotFoundError,
    PromptsConfigError,
    PromptNotFoundError,
    WorkflowGenerationError,
)

# Prompt loading and validation
from pasteprompt.prompts import (
    load_prompts,
    get_prompt_content,
    get_settings,
    validate_prompts,
)

# Configuration management
from pasteprompt.config import (
    get_config_path,
    create_default_config,
    ensure_config_dir,
    ensure_services_dir,
    get_python_executable,
    is_debug_enabled,
    SERVICES_DIR,
    DEFAULT_CONFIG_DIR,
    DEFAULT_PROMPTS_FILE,
)

# Workflow generation
from pasteprompt.workflow import (
    generate_workflow,
    generate_all_workflows,
    cleanup_old_workflows,
    refresh_services_menu,
    list_installed_workflows,
)

# Pasteboard utilities
from pasteprompt.pasteboard import (
    output_for_service,
    copy_to_clipboard,
    get_clipboard_content,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Data classes
    "Prompt",
    # Exceptions
    "PastePromptError",
    "ConfigNotFoundError",
    "PromptsConfigError",
    "PromptNotFoundError",
    "WorkflowGenerationError",
    # Prompt functions
    "load_prompts",
    "get_prompt_content",
    "get_settings",
    "validate_prompts",
    # Config functions
    "get_config_path",
    "create_default_config",
    "ensure_config_dir",
    "ensure_services_dir",
    "get_python_executable",
    "is_debug_enabled",
    # Config constants
    "SERVICES_DIR",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_PROMPTS_FILE",
    # Workflow functions
    "generate_workflow",
    "generate_all_workflows",
    "cleanup_old_workflows",
    "refresh_services_menu",
    "list_installed_workflows",
    # Pasteboard functions
    "output_for_service",
    "copy_to_clipboard",
    "get_clipboard_content",
]

