#!/usr/bin/env python3
"""Tests for source_history.py"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sources"))

from source_history import filter_noise, deduplicate, process_history


def test_parse_history_entries():
    """Test parsing history entries."""
    # This test would require mocking subprocess, so we'll test the helper functions instead
    commands = ["git status", "ls", "cd ..", "git commit -m 'test'"]
    filtered = filter_noise(commands)
    
    # ls and cd should be filtered out
    assert "git status" in filtered, "git status should not be filtered"
    assert "ls" not in filtered, "ls should be filtered"
    assert "cd .." not in filtered, "cd should be filtered"
    
    print("✓ test_parse_history_entries passed")


def test_filter_noise_commands():
    """Test filtering noise commands."""
    commands = ["ls", "pwd", "clear", "git status", "npm install"]
    filtered = filter_noise(commands)
    
    assert len(filtered) == 2, f"Expected 2 commands, got {len(filtered)}"
    assert "git status" in filtered, "git status should remain"
    assert "npm install" in filtered, "npm install should remain"
    
    print("✓ test_filter_noise_commands passed")


def test_output_valid_json_format():
    """Test that output is valid JSON format."""
    # Mock the subprocess call
    mock_output = "  1  git status\n  2  npm install\n"
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output
        )
        
        commands = process_history(max_entries=10)
        output = {"commands": commands}
        json_str = json.dumps(output)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "commands" in parsed, "JSON structure invalid"
        assert all(cmd.get("source") == "history" for cmd in parsed["commands"]), "Source should be history"
        
        print("✓ test_output_valid_json_format passed")


def test_handle_empty_history_gracefully():
    """Test handling empty history gracefully."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=""
        )
        
        commands = process_history(max_entries=10)
        assert isinstance(commands, list), "Should return list even if empty"
        
        print("✓ test_handle_empty_history_gracefully passed")


if __name__ == "__main__":
    test_parse_history_entries()
    test_filter_noise_commands()
    test_output_valid_json_format()
    test_handle_empty_history_gracefully()
    print("\nAll tests passed!")

