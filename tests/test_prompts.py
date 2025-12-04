"""Tests for prompts module."""

import tempfile
from pathlib import Path

import pytest

from pasteprompt.prompts import (
    ConfigNotFoundError,
    Prompt,
    PromptNotFoundError,
    PromptsConfigError,
    get_prompt_content,
    get_settings,
    load_prompts,
    validate_prompts,
)


class TestPrompt:
    """Tests for the Prompt dataclass."""

    def test_menu_name_from_display_name(self):
        """Test that display_name is used when provided."""
        prompt = Prompt(key="test_key", content="test", display_name="Custom Name")
        assert prompt.menu_name == "Custom Name"

    def test_menu_name_from_key(self):
        """Test that key is formatted when display_name is not provided."""
        prompt = Prompt(key="some_test_key", content="test")
        assert prompt.menu_name == "Some Test Key"

    def test_menu_name_simple_key(self):
        """Test menu name with a simple key."""
        prompt = Prompt(key="investigate", content="test")
        assert prompt.menu_name == "Investigate"

    def test_get_menu_name_without_key(self):
        """Test get_menu_name without including key."""
        prompt = Prompt(key="test_key", content="test", display_name="Custom Name")
        assert prompt.get_menu_name(include_key=False) == "Custom Name"

    def test_get_menu_name_with_key(self):
        """Test get_menu_name with key prefix."""
        prompt = Prompt(key="test_key", content="test", display_name="Custom Name")
        assert prompt.get_menu_name(include_key=True) == "[test_key] Custom Name"

    def test_get_menu_name_with_key_no_display_name(self):
        """Test get_menu_name with key prefix when no display_name."""
        prompt = Prompt(key="investigate", content="test")
        assert prompt.get_menu_name(include_key=True) == "[investigate] Investigate"


class TestValidatePrompts:
    """Tests for validate_prompts function."""

    def test_valid_minimal_config(self):
        """Test validation of minimal valid config."""
        data = {"prompts": {"test": "content"}}
        errors = validate_prompts(data)
        assert errors == []

    def test_valid_full_config(self):
        """Test validation of full config with all options."""
        data = {
            "settings": {"prefix": "Test", "include_key_in_name": True},
            "prompts": {
                "test": {
                    "content": "Test content",
                    "display_name": "Test Prompt",
                    "description": "A test",
                    "category": "Testing",
                }
            },
        }
        errors = validate_prompts(data)
        assert errors == []

    def test_missing_prompts_section(self):
        """Test that missing prompts section is caught."""
        data = {"settings": {}}
        errors = validate_prompts(data)
        assert any("Missing required 'prompts' section" in e for e in errors)

    def test_empty_prompts_section(self):
        """Test that empty prompts section is caught."""
        data = {"prompts": {}}
        errors = validate_prompts(data)
        assert any("'prompts' section is empty" in e for e in errors)

    def test_empty_content(self):
        """Test that empty content is caught."""
        data = {"prompts": {"test": ""}}
        errors = validate_prompts(data)
        assert any("empty content" in e for e in errors)

    def test_missing_content_in_dict(self):
        """Test that missing content field is caught."""
        data = {"prompts": {"test": {"display_name": "Test"}}}
        errors = validate_prompts(data)
        assert any("missing required 'content' field" in e for e in errors)

    def test_invalid_prompts_type(self):
        """Test that non-dict prompts is caught."""
        data = {"prompts": ["list", "not", "dict"]}
        errors = validate_prompts(data)
        assert any("'prompts' must be a dictionary" in e for e in errors)


class TestLoadPrompts:
    """Tests for load_prompts function."""

    def test_load_simple_prompts(self):
        """Test loading prompts with simple string values."""
        yaml_content = """
prompts:
  test1: "Content 1"
  test2: "Content 2"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            prompts = load_prompts(path)
            assert len(prompts) == 2
            assert prompts["test1"].content == "Content 1"
            assert prompts["test2"].content == "Content 2"
        finally:
            path.unlink()

    def test_load_full_prompts(self):
        """Test loading prompts with full options."""
        yaml_content = """
prompts:
  test:
    content: "Test content"
    display_name: "Test Prompt"
    description: "A test prompt"
    category: "Testing"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            prompts = load_prompts(path)
            assert len(prompts) == 1
            assert prompts["test"].content == "Test content"
            assert prompts["test"].display_name == "Test Prompt"
            assert prompts["test"].description == "A test prompt"
            assert prompts["test"].category == "Testing"
        finally:
            path.unlink()

    def test_load_nonexistent_file(self):
        """Test that ConfigNotFoundError is raised for missing file."""
        with pytest.raises(ConfigNotFoundError):
            load_prompts(Path("/nonexistent/path.yaml"))

    def test_load_invalid_yaml(self):
        """Test that PromptsConfigError is raised for invalid YAML."""
        yaml_content = "invalid: yaml: content:"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(PromptsConfigError):
                load_prompts(path)
        finally:
            path.unlink()


class TestGetPromptContent:
    """Tests for get_prompt_content function."""

    def test_get_existing_prompt(self):
        """Test getting content for an existing prompt."""
        yaml_content = """
prompts:
  test: "Test content"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            content = get_prompt_content("test", path)
            assert content == "Test content"
        finally:
            path.unlink()

    def test_get_nonexistent_prompt(self):
        """Test that PromptNotFoundError is raised for missing prompt."""
        yaml_content = """
prompts:
  test: "Test content"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(PromptNotFoundError):
                get_prompt_content("nonexistent", path)
        finally:
            path.unlink()


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_with_custom_values(self):
        """Test loading custom settings."""
        yaml_content = """
settings:
  prefix: "CustomPrefix"
  include_key_in_name: true

prompts:
  test: "content"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            settings = get_settings(path)
            assert settings["prefix"] == "CustomPrefix"
            assert settings["include_key_in_name"] is True
        finally:
            path.unlink()

    def test_get_settings_defaults(self):
        """Test that defaults are applied when settings not specified."""
        yaml_content = """
prompts:
  test: "content"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            settings = get_settings(path)
            assert settings["prefix"] == "PastePrompt"
            assert settings["include_key_in_name"] is False
        finally:
            path.unlink()

    def test_get_settings_nonexistent_file(self):
        """Test that defaults are returned for nonexistent file."""
        settings = get_settings(Path("/nonexistent/path.yaml"))
        assert settings["prefix"] == "PastePrompt"
        assert settings["include_key_in_name"] is False

    def test_get_settings_partial(self):
        """Test partial settings with defaults for missing values."""
        yaml_content = """
settings:
  prefix: "MyPrefix"

prompts:
  test: "content"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            settings = get_settings(path)
            assert settings["prefix"] == "MyPrefix"
            assert settings["include_key_in_name"] is False  # Default
        finally:
            path.unlink()

