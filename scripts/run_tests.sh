#!/bin/zsh
# Run all unit tests for fz-cmd

FZ_CMD_DIR="$HOME/.dotfiles/zsh/fz-cmd"
TESTS_DIR="$FZ_CMD_DIR/tests"

cd "$FZ_CMD_DIR"

echo "Running fz-cmd unit tests..."
echo ""

# Counters
passed=0
failed=0

test_files=("$TESTS_DIR"/test_*.py)

# Remove current directory prefix from test_files paths for pretty printing
short_test_files=()
for file in "${test_files[@]}"; do
    relative_path="${file#$FZ_CMD_DIR/}"
    short_test_files+=("$relative_path")
		echo "Test file: $relative_path"
done

echo ""

# Run each test file
# Use set +e to prevent early exit, then check exit code explicitly
for test_file in "${test_files[@]}"; do
    test_name=$(basename "$test_file")
    echo "=== Running $test_name ==="
    
    set +e
    python3 "$test_file" 2>&1
    exit_code=$?
    set +e  # Keep it disabled for the rest of the script
    
    if [ $exit_code -eq 0 ]; then
        echo "✓ $test_name passed"
        ((passed++))
    else
        echo "✗ $test_name failed"
        ((failed++))
    fi
    echo ""
done

# Summary
echo "=========================================="
echo "Test Summary:"
echo "  Passed: $passed"
echo "  Failed: $failed"
echo "  Total:  $((passed + failed))"
echo "=========================================="

if [ $failed -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi

