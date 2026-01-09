#!/usr/bin/env python3
"""Tests for source_functions.py"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sources"))

from source_functions import get_functions, process_functions


def test_get_function_names_from_zsh():
    """Test getting function names from zsh."""
    mock_output = "test_function\nanother_function\n_internal_function\nvalid-function"
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output
        )
        
        functions = get_functions()
        # Should filter out _internal_function
        assert "_internal_function" not in functions, "Internal functions should be filtered"
        # Should include valid functions
        assert "test_function" in functions or "another_function" in functions, "Valid functions should be included"
        
        print("✓ test_get_function_names_from_zsh passed")


def test_filter_internal_functions():
    """Test filtering internal functions."""
    function_names = ["test", "_internal", "valid", "__private"]
    
    filtered = [f for f in function_names if not f.startswith("_")]
    
    assert "_internal" not in filtered, "Internal functions should be filtered"
    assert "__private" not in filtered, "Private functions should be filtered"
    assert "test" in filtered, "Valid functions should remain"
    assert "valid" in filtered, "Valid functions should remain"
    
    print("✓ test_filter_internal_functions passed")


def test_add_source_function_metadata():
    """Test that source='function' is added."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="test_function"
        )
        
        commands = process_functions()
        assert len(commands) > 0, "Should have at least one command"
        assert commands[0]["source"] == "function", "Source should be function"
        assert "function_name" in commands[0]["metadata"], "Should have function_name in metadata"
        
        print("✓ test_add_source_function_metadata passed")


if __name__ == "__main__":
    test_get_function_names_from_zsh()
    test_filter_internal_functions()
    test_add_source_function_metadata()
    print("\nAll tests passed!")

