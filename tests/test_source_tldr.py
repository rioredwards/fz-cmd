#!/usr/bin/env python3
"""Tests for source_tldr.py"""

import json
import tempfile
import os
import sys
import yaml
from pathlib import Path

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sources"))

from source_tldr import parse_tldr_yaml


def test_parse_tldr_commands_yaml():
    """Test parsing tldr-commands.yaml."""
    yaml_content = {
        "commands": [
            {
                "command": "git status",
                "description": "Show git repository status",
                "tags": ["git", "status"],
                "examples": [
                    {"command": "git status"},
                    {"command": "git status -s"}
                ]
            },
            {
                "command": "ls",
                "description": "List files",
                "tags": ["files", "list"],
                "examples": [{"command": "ls -la"}]
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_content, f)
        yaml_file = f.name
    
    try:
        commands = parse_tldr_yaml(yaml_file)
        
        assert len(commands) == 2, f"Expected 2 commands, got {len(commands)}"
        assert commands[0]["command"] == "git status", "First command mismatch"
        assert commands[0]["source"] == "tldr", "Source should be tldr"
        assert "git" in commands[0]["tags"], "Tags missing"
        assert len(commands[0]["examples"]) == 2, "Examples missing"
        
        print("✓ test_parse_tldr_commands_yaml passed")
    finally:
        os.unlink(yaml_file)


def test_handle_missing_file():
    """Test handling missing file gracefully."""
    commands = parse_tldr_yaml("/nonexistent/file.yaml")
    assert len(commands) == 0, f"Expected 0 commands, got {len(commands)}"
    print("✓ test_handle_missing_file passed")


def test_output_valid_json_format():
    """Test that output is valid JSON format."""
    yaml_content = {
        "commands": [
            {
                "command": "test",
                "description": "Test command",
                "tags": ["test"],
                "examples": []
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_content, f)
        yaml_file = f.name
    
    try:
        commands = parse_tldr_yaml(yaml_file)
        output = {"commands": commands}
        json_str = json.dumps(output)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "commands" in parsed, "JSON structure invalid"
        assert len(parsed["commands"]) == 1, "Command count mismatch"
        
        print("✓ test_output_valid_json_format passed")
    finally:
        os.unlink(yaml_file)


if __name__ == "__main__":
    test_parse_tldr_commands_yaml()
    test_handle_missing_file()
    test_output_valid_json_format()
    print("\nAll tests passed!")

