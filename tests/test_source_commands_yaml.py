#!/usr/bin/env python3
"""Tests for source_commands_yaml.py"""

import json
import tempfile
import os
import sys
import yaml
from pathlib import Path

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sources"))

from source_commands_yaml import parse_commands_yaml


def test_parse_commands_yaml():
    """Test parsing commands.yaml."""
    yaml_content = {
        "commands": [
            {
                "command": "git status",
                "description": "Show git repository status",
                "tags": ["git", "status"],
                "examples": [
                    {"description": "", "command": "git status"},
                    {"description": "", "command": "git status -s"}
                ]
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_content, f)
        yaml_file = f.name
    
    try:
        commands = parse_commands_yaml(yaml_file)
        
        assert len(commands) == 1, f"Expected 1 command, got {len(commands)}"
        assert commands[0]["command"] == "git status", "Command mismatch"
        assert commands[0]["source"] == "curated", "Source should be curated"
        assert len(commands[0]["examples"]) == 2, "Examples missing"
        
        print("✓ test_parse_commands_yaml passed")
    finally:
        os.unlink(yaml_file)


def test_handle_invalid_yaml():
    """Test handling invalid YAML."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: [")
        yaml_file = f.name
    
    try:
        commands = parse_commands_yaml(yaml_file)
        # Should return empty list on error
        assert len(commands) == 0, f"Expected 0 commands on error, got {len(commands)}"
        print("✓ test_handle_invalid_yaml passed")
    finally:
        os.unlink(yaml_file)


def test_add_source_curated_metadata():
    """Test that source='curated' is added."""
    yaml_content = {
        "commands": [
            {
                "command": "test",
                "description": "Test"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_content, f)
        yaml_file = f.name
    
    try:
        commands = parse_commands_yaml(yaml_file)
        assert commands[0]["source"] == "curated", "Source should be curated"
        print("✓ test_add_source_curated_metadata passed")
    finally:
        os.unlink(yaml_file)


if __name__ == "__main__":
    test_parse_commands_yaml()
    test_handle_invalid_yaml()
    test_add_source_curated_metadata()
    print("\nAll tests passed!")

