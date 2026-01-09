#!/bin/zsh
# End-to-end test for fz-cmd refactor
set -e

FZ_CMD_DIR="$HOME/.dotfiles/zsh/fz-cmd"
cd "$FZ_CMD_DIR"

echo "=== E2E Test: fz-cmd refactor ==="

# Test 1: Cache refresh
echo "Test 1: Refresh all caches..."
zsh scripts/refresh_cache.sh > /dev/null 2>&1
[ -f cache/commands.json ] || { echo "❌ commands.json not created"; exit 1; }
[ -f cache/aliases.json ] || { echo "❌ aliases.json not created"; exit 1; }
[ -f cache/functions.json ] || { echo "❌ functions.json not created"; exit 1; }
[ -f cache/history.json ] || { echo "❌ history.json not created"; exit 1; }
echo "✓ All cache files created"

# Test 2: Validate JSON format
echo "Test 2: Validate JSON format..."
for cache_file in cache/*.json; do
    python3 -c "import json; json.load(open('$cache_file'))" || {
        echo "❌ Invalid JSON in $cache_file"; exit 1;
    }
done
echo "✓ All cache files are valid JSON"

# Test 3: Merge commands
echo "Test 3: Merge cache files..."
python3 utils/merge_commands.py cache/commands.json cache/aliases.json cache/functions.json cache/history.json > /tmp/merged_e2e.json
[ -s /tmp/merged_e2e.json ] || { echo "❌ Merge failed"; exit 1; }
python3 -c "import json; data=json.load(open('/tmp/merged_e2e.json')); assert len(data['commands']) > 0" || {
    echo "❌ Merged file has no commands"; exit 1;
}
echo "✓ Commands merged successfully"

# Test 4: Apply limits
echo "Test 4: Apply limits..."
python3 utils/limit_commands.py /tmp/merged_e2e.json \
    --limit curated:10 --limit alias:5 --limit function:5 --limit history:20 \
    > /tmp/limited_e2e.json
[ -s /tmp/limited_e2e.json ] || { echo "❌ Limit failed"; exit 1; }
echo "✓ Limits applied successfully"

# Test 5: Format for fzf
echo "Test 5: Format for fzf..."
python3 utils/format_for_fzf.py /tmp/limited_e2e.json > /tmp/formatted_e2e.txt
[ -s /tmp/formatted_e2e.txt ] || { echo "❌ Format failed"; exit 1; }
# Check that output has tab-separated fields (5 fields: formatted_display, command, description, tags, examples)
first_line=$(head -1 /tmp/formatted_e2e.txt)
field_count=$(echo "$first_line" | awk -F'\t' '{print NF}')
[ "$field_count" = "5" ] || { echo "❌ Expected 5 fields, got $field_count"; exit 1; }
echo "✓ Commands formatted successfully"

# Test 6: Build preview
echo "Test 6: Build preview..."
# Extract fields from first formatted line (5 fields: display, command, description, tags, examples)
IFS=$'\t' read -r display_col cmd desc tags examples <<< "$first_line"
preview=$(python3 utils/build_preview.py "$cmd" "$desc" "$tags" "$examples" "curated")
[ -n "$preview" ] || { echo "❌ Preview generation failed"; exit 1; }
echo "✓ Preview generated successfully"

# Test 7: Source main.zsh without errors
echo "Test 7: Source main.zsh..."
zsh -c "source main.zsh && echo 'Loaded'" > /dev/null 2>&1 || {
    echo "❌ main.zsh failed to source"; exit 1;
}
echo "✓ main.zsh sources without errors"

# Test 8: Command extraction (simulate selection)
echo "Test 8: Command extraction from formatted output..."
# Extract command field (field 2 in 5-field format)
extracted_cmd=$(echo "$first_line" | awk -F'\t' 'NF >= 2 {print $2; exit}')
[ -n "$extracted_cmd" ] || { echo "❌ Command extraction failed"; exit 1; }
echo "✓ Command extracted: $extracted_cmd"

# Cleanup
rm -f /tmp/merged_e2e.json /tmp/limited_e2e.json /tmp/formatted_e2e.txt

echo ""
echo "✅ All E2E tests passed!"
