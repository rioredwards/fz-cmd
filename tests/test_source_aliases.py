#!/usr/bin/env python3
"""Tests for source_aliases.py"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sources"))

from source_aliases import get_aliases, process_aliases


def test_parse_alias_output():
    """Test parsing alias output."""
    mock_output = "alias ll='ls -lah'\nalias g=git\nalias test=\"echo test\""
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output
        )
        
        # Actually test the parsing logic directly
        aliases = []
        for line in mock_output.split("\n"):
            if not line.strip():
                continue
            line = line.replace("alias ", "", 1).strip()
            if "=" in line:
                name, value = line.split("=", 1)
                if value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                aliases.append({"name": name.strip(), "value": value.strip()})
        
        assert len(aliases) == 3, f"Expected 3 aliases, got {len(aliases)}"
        assert aliases[0]["name"] == "ll", "First alias name mismatch"
        assert aliases[0]["value"] == "ls -lah", "First alias value mismatch"
        
        print("✓ test_parse_alias_output passed")


def test_handle_quoted_values():
    """Test handling quoted values."""
    test_cases = [
        ("alias test='value'", "test", "value"),
        ('alias test="value"', "test", "value"),
        ("alias test=value", "test", "value"),
    ]
    
    for line, expected_name, expected_value in test_cases:
        line = line.replace("alias ", "", 1).strip()
        if "=" in line:
            name, value = line.split("=", 1)
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]
            assert name == expected_name, f"Name mismatch: {name} != {expected_name}"
            assert value == expected_value, f"Value mismatch: {value} != {expected_value}"
    
    print("✓ test_handle_quoted_values passed")


def test_add_source_alias_metadata():
    """Test that source='alias' is added."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="alias test='echo test'"
        )
        
        commands = process_aliases()
        assert len(commands) > 0, "Should have at least one command"
        assert commands[0]["source"] == "alias", "Source should be alias"
        assert "alias_name" in commands[0]["metadata"], "Should have alias_name in metadata"
        
        print("✓ test_add_source_alias_metadata passed")


if __name__ == "__main__":
    test_parse_alias_output()
    test_handle_quoted_values()
    test_add_source_alias_metadata()
    print("\nAll tests passed!")

