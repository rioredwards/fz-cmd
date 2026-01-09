#!/usr/bin/env python3
"""Integration tests for fz-cmd Python pipeline"""

import json
import tempfile
import sys
from pathlib import Path

# Add utils to path
FZ_CMD_DIR = Path.home() / ".dotfiles" / "zsh" / "fz-cmd"
sys.path.insert(0, str(FZ_CMD_DIR / "utils"))

from merge_commands import merge_commands
from format_for_fzf import format_commands
from limit_commands import limit_commands


def test_full_pipeline():
    """Test complete pipeline: merge → limit → format"""

    # Create test data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
        json.dump({
            "commands": [
                {
                    "command": "cmd1",
                    "description": "Desc 1",
                    "source": "curated",
                    "tags": ["tag1"],
                    "examples": ["example1"]
                },
                {
                    "command": "cmd2",
                    "description": "Desc 2",
                    "source": "curated",
                    "tags": [],
                    "examples": []
                },
            ]
        }, f1)
        file1 = f1.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
        json.dump({
            "commands": [
                {
                    "command": "cmd3",
                    "description": "Desc 3",
                    "source": "alias",
                    "tags": [],
                    "examples": []
                },
            ]
        }, f2)
        file2 = f2.name

    # Step 1: Merge (returns List[Dict])
    merged_commands = merge_commands([file1, file2])
    assert isinstance(merged_commands, list)
    assert len(merged_commands) == 3

    # Step 2: Limit (takes List[Dict], returns List[Dict])
    limited_commands = limit_commands(merged_commands, {"curated": 1, "alias": 10})
    assert len(limited_commands) == 2  # 1 curated + 1 alias

    # Step 3: Format (takes List[Dict], returns List[str])
    formatted_lines = format_commands(limited_commands)
    assert len(formatted_lines) == 2

    # Verify format (5 fields: formatted_display \t command \t description \t tags \t examples)
    for line in formatted_lines:
        parts = line.split('\t')
        assert len(parts) == 5, f"Expected 5 fields, got {len(parts)}: {line}"

    print("✓ test_full_pipeline passed")


def test_deduplication_priority():
    """Test that deduplication respects source priority"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
        json.dump({
            "commands": [
                {
                    "command": "duplicate",
                    "description": "From curated",
                    "source": "curated",
                    "tags": [],
                    "examples": []
                },
            ]
        }, f1)
        file1 = f1.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
        json.dump({
            "commands": [
                {
                    "command": "duplicate",
                    "description": "From history",
                    "source": "history",
                    "tags": [],
                    "examples": []
                },
            ]
        }, f2)
        file2 = f2.name

    merged_commands = merge_commands([file1, file2])

    assert len(merged_commands) == 1, "Duplicate should be removed"
    assert merged_commands[0]["source"] == "curated", "Curated should win priority"
    assert merged_commands[0]["description"] == "From curated"

    print("✓ test_deduplication_priority passed")


def test_error_handling():
    """Test error handling for malformed data"""

    # Test with non-existent file (merge_commands returns empty list for missing files)
    merged = merge_commands(["/nonexistent/file.json"])
    assert merged == []

    # Test with empty commands list
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"commands": []}, f)
        fname = f.name

    merged = merge_commands([fname])
    assert merged == []

    print("✓ test_error_handling passed")


if __name__ == "__main__":
    test_full_pipeline()
    test_deduplication_priority()
    test_error_handling()
    print("\n✅ All integration tests passed!")
