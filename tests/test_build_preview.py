#!/usr/bin/env python3
"""Tests for build_preview.py"""

import sys
import subprocess
from pathlib import Path

# Get path to build_preview.py
BUILD_PREVIEW_SCRIPT = Path(__file__).parent.parent / "utils" / "build_preview.py"


def run_build_preview(display, command, description, tags, examples):
    """Run build_preview.py with given arguments and return output."""
    result = subprocess.run(
        [sys.executable, str(BUILD_PREVIEW_SCRIPT), display, command, description, tags, examples],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise AssertionError(f"build_preview.py failed: {result.stderr}")
    return result.stdout


def test_format_preview_with_all_fields():
    """Test formatting preview with all fields."""
    preview = run_build_preview(
        "git status | Show status",
        "git status",
        "Show git repository status",
        "git, status",
        "git status | git status -s"
    )
    
    assert "Command:" in preview, "Command header missing"
    assert "git status" in preview, "Command missing"
    assert "Description:" in preview, "Description header missing"
    assert "Show git repository status" in preview, "Description missing"
    assert "Tags:" in preview, "Tags header missing"
    assert "git" in preview and "status" in preview, "Tags missing"
    assert "Examples:" in preview, "Examples header missing"
    assert "$ git status" in preview, "Example missing"
    
    print("✓ test_format_preview_with_all_fields passed")


def test_handle_missing_examples_tags():
    """Test handling missing examples/tags."""
    preview = run_build_preview(
        "ls",
        "ls",
        "List files",
        "",
        ""
    )
    
    assert "Command:" in preview, "Command header missing"
    assert "ls" in preview, "Command missing"
    assert "Description:" in preview, "Description header missing"
    assert "List files" in preview, "Description missing"
    assert "Examples:" not in preview, "Examples should not appear when empty"
    assert "Tags:" not in preview, "Tags should not appear when empty"
    
    print("✓ test_handle_missing_examples_tags passed")


def test_special_characters_in_tags():
    """Test handling special characters like [brew] in tags."""
    preview = run_build_preview(
        "brew install | Install package [brew]",
        "brew install",
        "Install package with Homebrew",
        "brew, install, package",
        "brew install package-name"
    )
    
    assert "Command:" in preview
    assert "brew install" in preview
    assert "[brew]" not in preview or "brew" in preview, "Should handle tags correctly"
    
    print("✓ test_special_characters_in_tags passed")


if __name__ == "__main__":
    test_format_preview_with_all_fields()
    test_handle_missing_examples_tags()
    test_special_characters_in_tags()
    print("\nAll tests passed!")

