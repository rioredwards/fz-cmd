#!/usr/bin/env python3
"""Tests for limit_commands.py"""

import json
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from limit_commands import limit_commands


def test_limit_commands_per_source():
    """Test limiting commands per source."""
    commands = [
        {"command": "cmd1", "source": "curated"},
        {"command": "cmd2", "source": "curated"},
        {"command": "cmd3", "source": "curated"},
        {"command": "cmd4", "source": "history"},
        {"command": "cmd5", "source": "history"},
    ]
    
    limits = {"curated": 2, "history": 1}
    limited = limit_commands(commands, limits)
    
    # Should have 2 curated + 1 history = 3 total
    assert len(limited) == 3, f"Expected 3 commands, got {len(limited)}"
    
    curated_count = sum(1 for c in limited if c["source"] == "curated")
    history_count = sum(1 for c in limited if c["source"] == "history")
    
    assert curated_count == 2, f"Expected 2 curated, got {curated_count}"
    assert history_count == 1, f"Expected 1 history, got {history_count}"
    
    print("✓ test_limit_commands_per_source passed")


def test_handle_empty_sources():
    """Test handling empty sources."""
    commands = [
        {"command": "cmd1", "source": "curated"},
    ]
    
    limits = {"curated": 10, "history": 5}
    limited = limit_commands(commands, limits)
    
    assert len(limited) == 1, f"Expected 1 command, got {len(limited)}"
    assert limited[0]["source"] == "curated"
    
    print("✓ test_handle_empty_sources passed")


def test_preserve_source_priority_when_limiting():
    """Test that source priority is preserved when limiting."""
    commands = [
        {"command": "cmd1", "source": "tldr"},
        {"command": "cmd2", "source": "history"},
        {"command": "cmd3", "source": "curated"},
    ]
    
    limits = {"curated": 1, "history": 1, "tldr": 1}
    limited = limit_commands(commands, limits)
    
    # Should be sorted by priority: curated first, then history, then tldr
    assert len(limited) == 3, f"Expected 3 commands, got {len(limited)}"
    assert limited[0]["source"] == "curated", "Curated should be first"
    assert limited[1]["source"] == "history", "History should be second"
    assert limited[2]["source"] == "tldr", "tldr should be third"
    
    print("✓ test_preserve_source_priority_when_limiting passed")


if __name__ == "__main__":
    test_limit_commands_per_source()
    test_handle_empty_sources()
    test_preserve_source_priority_when_limiting()
    print("\nAll tests passed!")

