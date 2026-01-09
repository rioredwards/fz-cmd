#!/bin/zsh
# Performance test for fz-cmd

FZ_CMD_DIR="$HOME/.dotfiles/zsh/fz-cmd"
cd "$FZ_CMD_DIR"

echo "=== Performance Test ==="

# Ensure caches are fresh
echo "Refreshing caches..."
zsh scripts/refresh_cache.sh > /dev/null 2>&1

# Test startup time (excluding fzf UI)
echo "Measuring pipeline execution time..."

# Use Perl for high-resolution timing (available on macOS)
start=$(perl -MTime::HiRes -e 'print Time::HiRes::time()')

# Simulate the pipeline that runs before fzf launches
python3 utils/merge_commands.py \
    cache/commands.json \
    cache/aliases.json \
    cache/functions.json \
    cache/history.json \
    > /tmp/perf_merged.json

python3 utils/limit_commands.py /tmp/perf_merged.json \
    --limit curated:1000 \
    --limit alias:100 \
    --limit function:100 \
    --limit history:200 \
    > /tmp/perf_limited.json

python3 utils/format_for_fzf.py /tmp/perf_limited.json \
    > /tmp/perf_formatted.txt

end=$(perl -MTime::HiRes -e 'print Time::HiRes::time()')

elapsed=$(echo "$end - $start" | bc)
elapsed_ms=$(echo "$elapsed * 1000" | bc)

echo "Pipeline execution time: ${elapsed}s (${elapsed_ms}ms)"

# Check target (< 100ms ideal, < 200ms acceptable)
if (( $(echo "$elapsed < 0.1" | bc -l) )); then
    echo "✅ Performance excellent: < 100ms"
elif (( $(echo "$elapsed < 0.2" | bc -l) )); then
    echo "✓ Performance acceptable: < 200ms"
else
    echo "⚠️  Performance warning: ${elapsed}s exceeds 200ms target"
    echo "Consider reducing data limits or optimizing Python scripts"
fi

# Show cache sizes
echo ""
echo "Cache file sizes:"
du -h cache/*.json | awk '{printf "  %s: %s\n", $2, $1}'

# Show command counts
echo ""
echo "Command counts after limiting:"
python3 -c "
import json
data = json.load(open('/tmp/perf_limited.json'))
from collections import Counter
sources = Counter(cmd['source'] for cmd in data['commands'])
for source, count in sorted(sources.items()):
    print(f'  {source}: {count}')
print(f'  TOTAL: {len(data[\"commands\"])}')
"

# Cleanup
rm -f /tmp/perf_*.json /tmp/perf_*.txt

echo ""
echo "✓ Performance test complete"
