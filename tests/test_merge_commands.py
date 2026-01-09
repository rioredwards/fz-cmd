#!/usr/bin/env python3
"""Tests for merge_commands.py"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from merge_commands import merge_commands, load_commands


def test_merge_two_files_with_overlap():
    """Test merging 2 files with overlapping commands."""
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
        json.dump({
            "commands": [
                {"command": "git status", "description": "Status", "source": "curated"},
                {"command": "ls", "description": "List", "source": "curated"},
            ]
        }, f1)
        file1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
        json.dump({
            "commands": [
                {"command": "git status", "description": "Git status", "source": "history"},
                {"command": "pwd", "description": "Print dir", "source": "history"},
            ]
        }, f2)
        file2 = f2.name
    
    try:
        merged = merge_commands([file1, file2])
        
        # Should have 3 unique commands
        assert len(merged) == 3, f"Expected 3 commands, got {len(merged)}"
        
        # git status should come from curated (higher priority)
        git_status = next((c for c in merged if c["command"] == "git status"), None)
        assert git_status is not None, "git status not found"
        assert git_status["source"] == "curated", f"Expected curated, got {git_status['source']}"
        
        # ls and pwd should both be present
        commands = [c["command"] for c in merged]
        assert "ls" in commands, "ls not found"
        assert "pwd" in commands, "pwd not found"
        
        print("✓ test_merge_two_files_with_overlap passed")
    finally:
        os.unlink(file1)
        os.unlink(file2)


def test_handle_empty_files():
    """Test handling empty files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
        json.dump({"commands": []}, f1)
        file1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
        json.dump({"commands": [{"command": "test", "source": "curated"}]}, f2)
        file2 = f2.name
    
    try:
        merged = merge_commands([file1, file2])
        assert len(merged) == 1, f"Expected 1 command, got {len(merged)}"
        assert merged[0]["command"] == "test"
        print("✓ test_handle_empty_files passed")
    finally:
        os.unlink(file1)
        os.unlink(file2)


def test_preserve_source_priority():
    """Test that source priority is preserved (curated > alias > function > history > tldr)."""
    sources = ["tldr", "history", "function", "alias", "curated"]
    
    files = []
    for i, source in enumerate(sources):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "commands": [{"command": "same_command", "source": source}]
            }, f)
            files.append(f.name)
    
    try:
        merged = merge_commands(files)
        assert len(merged) == 1, f"Expected 1 command, got {len(merged)}"
        assert merged[0]["source"] == "curated", f"Expected curated (highest priority), got {merged[0]['source']}"
        print("✓ test_preserve_source_priority passed")
    finally:
        for f in files:
            os.unlink(f)


def test_handle_missing_files():
    """Test handling missing files."""
    merged = merge_commands(["/nonexistent/file.json"])
    assert len(merged) == 0, f"Expected 0 commands, got {len(merged)}"
    print("✓ test_handle_missing_files passed")


if __name__ == "__main__":
    test_merge_two_files_with_overlap()
    test_handle_empty_files()
    test_preserve_source_priority()
    test_handle_missing_files()
    print("\nAll tests passed!")

