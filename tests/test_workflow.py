"""Tests for workflow module."""

import tempfile
from pathlib import Path

import pytest

from pasteprompt.prompts import Prompt
from pasteprompt.workflow import (
    cleanup_old_workflows,
    generate_document_wflow,
    generate_info_plist,
    generate_workflow,
    get_workflow_name,
    list_installed_workflows,
)


class TestGetWorkflowName:
    """Tests for get_workflow_name function."""

    def test_basic_name(self):
        """Test workflow name generation with basic prompt."""
        prompt = Prompt(key="test", content="content")
        name = get_workflow_name(prompt)
        assert name == "PastePrompt - Test.workflow"

    def test_custom_display_name(self):
        """Test workflow name with custom display name."""
        prompt = Prompt(key="test", content="content", display_name="Custom Name")
        name = get_workflow_name(prompt)
        assert name == "PastePrompt - Custom Name.workflow"

    def test_underscore_key(self):
        """Test workflow name with underscored key."""
        prompt = Prompt(key="some_test_prompt", content="content")
        name = get_workflow_name(prompt)
        assert name == "PastePrompt - Some Test Prompt.workflow"

    def test_custom_prefix(self):
        """Test workflow name with custom prefix."""
        prompt = Prompt(key="test", content="content")
        name = get_workflow_name(prompt, prefix="MyPrompts")
        assert name == "MyPrompts - Test.workflow"

    def test_special_characters_removed(self):
        """Test that special characters are replaced."""
        prompt = Prompt(key="test", content="content", display_name="Test/Name:Here")
        name = get_workflow_name(prompt)
        assert "/" not in name
        assert ":" not in name

    def test_include_key_in_name(self):
        """Test workflow name with include_key_in_name enabled."""
        prompt = Prompt(key="investigate", content="content", display_name="Investigate")
        name = get_workflow_name(prompt, include_key_in_name=True)
        assert name == "PastePrompt - [investigate] Investigate.workflow"

    def test_include_key_in_name_with_underscores(self):
        """Test workflow name with include_key_in_name and underscored key."""
        prompt = Prompt(key="save_plan", content="content")
        name = get_workflow_name(prompt, include_key_in_name=True)
        assert name == "PastePrompt - [save_plan] Save Plan.workflow"


class TestGenerateInfoPlist:
    """Tests for generate_info_plist function."""

    def test_basic_plist(self):
        """Test basic Info.plist generation."""
        prompt = Prompt(key="test", content="content", display_name="Test Prompt")
        content = generate_info_plist(prompt)
        assert "<?xml version" in content
        assert "PastePrompt - Test Prompt" in content
        assert "NSServices" in content
        assert "NSStringPboardType" in content

    def test_custom_prefix(self):
        """Test Info.plist with custom prefix."""
        prompt = Prompt(key="test", content="content", display_name="Test")
        content = generate_info_plist(prompt, prefix="MyApp")
        assert "MyApp - Test" in content

    def test_include_key_in_name(self):
        """Test Info.plist with include_key_in_name enabled."""
        prompt = Prompt(key="investigate", content="content", display_name="Investigate")
        content = generate_info_plist(prompt, include_key_in_name=True)
        assert "[investigate] Investigate" in content

    def test_xml_special_characters_escaped(self):
        """Test that XML special characters are properly escaped."""
        prompt = Prompt(key="test", content="content", display_name="Test <&> Prompt")
        content = generate_info_plist(prompt)
        # Should be escaped, not raw
        assert "Test &lt;&amp;&gt; Prompt" in content
        assert "Test <&> Prompt" not in content


class TestGenerateDocumentWflow:
    """Tests for generate_document_wflow function."""

    def test_basic_wflow(self):
        """Test basic document.wflow generation."""
        content = generate_document_wflow("test_key", "/usr/bin/python3")
        assert "<?xml version" in content
        assert "test_key" in content
        assert "/usr/bin/python3" in content
        assert "Run Shell Script" in content

    def test_wflow_with_config_path(self):
        """Test document.wflow with config path."""
        content = generate_document_wflow(
            "test_key", "/usr/bin/python3", config_path=Path("/path/to/config.yaml")
        )
        assert "--config" in content
        assert "/path/to/config.yaml" in content


class TestGenerateWorkflow:
    """Tests for generate_workflow function."""

    def test_generate_workflow_creates_bundle(self):
        """Test that generate_workflow creates the correct bundle structure."""
        prompt = Prompt(key="test", content="Test content")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            workflow_path = generate_workflow(
                prompt=prompt,
                output_dir=output_dir,
                python_path="/usr/bin/python3",
            )

            # Check bundle exists
            assert workflow_path.exists()
            assert workflow_path.is_dir()
            assert workflow_path.name == "PastePrompt - Test.workflow"

            # Check Contents directory
            contents_dir = workflow_path / "Contents"
            assert contents_dir.exists()

            # Check QuickLook directory exists
            quicklook_dir = contents_dir / "QuickLook"
            assert quicklook_dir.exists()

            # Check Info.plist
            info_plist = contents_dir / "Info.plist"
            assert info_plist.exists()
            assert "NSServices" in info_plist.read_text()

            # Check document.wflow
            document_wflow = contents_dir / "document.wflow"
            assert document_wflow.exists()
            assert "test" in document_wflow.read_text()

    def test_generate_workflow_with_include_key(self):
        """Test generate_workflow with include_key_in_name."""
        prompt = Prompt(key="investigate", content="Test content")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            workflow_path = generate_workflow(
                prompt=prompt,
                output_dir=output_dir,
                python_path="/usr/bin/python3",
                include_key_in_name=True,
            )

            # Check bundle name includes key
            assert workflow_path.name == "PastePrompt - [investigate] Investigate.workflow"

            # Check Info.plist contains key in menu name
            info_plist = workflow_path / "Contents" / "Info.plist"
            content = info_plist.read_text()
            assert "[investigate] Investigate" in content


class TestCleanupOldWorkflows:
    """Tests for cleanup_old_workflows function."""

    def test_cleanup_removes_matching_workflows(self):
        """Test that cleanup removes workflows with matching prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create some fake workflow directories
            (output_dir / "PastePrompt - Test1.workflow").mkdir()
            (output_dir / "PastePrompt - Test2.workflow").mkdir()
            (output_dir / "Other - Something.workflow").mkdir()

            removed, failed = cleanup_old_workflows(output_dir, prefix="PastePrompt")

            assert removed == 2
            assert failed == []
            assert not (output_dir / "PastePrompt - Test1.workflow").exists()
            assert not (output_dir / "PastePrompt - Test2.workflow").exists()
            assert (output_dir / "Other - Something.workflow").exists()

    def test_cleanup_nonexistent_dir(self):
        """Test cleanup with nonexistent directory."""
        removed, failed = cleanup_old_workflows(Path("/nonexistent/path"))
        assert removed == 0
        assert failed == []


class TestListInstalledWorkflows:
    """Tests for list_installed_workflows function."""

    def test_list_workflows(self):
        """Test listing installed workflows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create some fake workflow directories
            (output_dir / "PastePrompt - Alpha.workflow").mkdir()
            (output_dir / "PastePrompt - Beta.workflow").mkdir()
            (output_dir / "PastePrompt - Gamma.workflow").mkdir()
            (output_dir / "Other - Something.workflow").mkdir()

            workflows = list_installed_workflows(output_dir)

            assert len(workflows) == 3
            assert "Alpha" in workflows
            assert "Beta" in workflows
            assert "Gamma" in workflows
            # Should be sorted
            assert workflows == ["Alpha", "Beta", "Gamma"]

    def test_list_empty_dir(self):
        """Test listing from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflows = list_installed_workflows(Path(tmpdir))
            assert workflows == []

    def test_list_nonexistent_dir(self):
        """Test listing from nonexistent directory."""
        workflows = list_installed_workflows(Path("/nonexistent/path"))
        assert workflows == []

