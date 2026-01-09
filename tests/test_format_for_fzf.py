#!/usr/bin/env python3
"""Tests for format_for_fzf.py"""

import json
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from format_for_fzf import format_command, format_commands


def test_format_single_command1():
    """Test formatting a single command."""
    cmd = {
      "command": "git add -A",
      "description": "Stage all changes including deletions",
      "tags": ["git", "add", "stage", "all", "changes"],
      "examples": ["git add -A", "git add -A && git commit -m 'message'"],
      "source": "curated",
      "metadata": {}
    }
    
    result = format_command(cmd)
    parts = result.split("\t")
    
    assert len(parts) == 5, f"Expected 5 parts, got {len(parts)}"
    assert parts[1] == "git add -A", f"Command mismatch: {parts[1]}"
    assert parts[2] == "Stage all changes including deletions", f"Description mismatch: {parts[2]}"
    assert "git" in parts[3], f"Tags missing: {parts[3]}"
    
    print("✓ test_format_single_command passed")

def test_format_single_command2():
    """Test formatting a single command."""
    cmd = {
        "command": "git status",
        "description": "Show git status",
        "tags": ["git", "status"],
        "examples": ["git status", "git status -s"],
        "source": "curated"
    }
    
    result = format_command(cmd)
    parts = result.split("\t")
    
    assert len(parts) == 5, f"Expected 5 parts, got {len(parts)}"
    assert parts[1] == "git status", f"Command mismatch: {parts[1]}"
    assert parts[2] == "Show git status", f"Description mismatch: {parts[2]}"
    assert "git" in parts[3], f"Tags missing: {parts[3]}"
    
    print("✓ test_format_single_command passed")


def test_handle_missing_fields():
    """Test handling missing fields gracefully."""
    cmd = {
        "command": "ls"
    }
    
    result = format_command(cmd)
    parts = result.split("\t")
    
    assert len(parts) == 5, f"Expected 5 parts, got {len(parts)}"
    assert parts[1] == "ls", f"Command mismatch: {parts[1]}"
    assert parts[2] == "", f"Description should be empty: {parts[2]}"
    
    print("✓ test_handle_missing_fields passed")


def test_sort_by_recent():
    """Test sorting by recent usage."""
    commands = [
        {"command": "git status", "source": "curated"},
        {"command": "ls", "source": "curated"},
        {"command": "pwd", "source": "curated"},
    ]
    
    recent = ["pwd", "git status"]  # pwd most recent, then git status
    
    formatted = format_commands(commands, recent)
    
    # Check order: pwd should be first, then git status, then ls
    first_cmd = formatted[0].split("\t")[1]
    second_cmd = formatted[1].split("\t")[1]
    
    assert first_cmd == "pwd", f"Expected pwd first, got {first_cmd}"
    assert second_cmd == "git status", f"Expected git status second, got {second_cmd}"
    
    print("✓ test_sort_by_recent passed")


if __name__ == "__main__":
    test_format_single_command1()
    test_format_single_command2()
    test_handle_missing_fields()
    test_sort_by_recent()
    print("\nAll tests passed!")

