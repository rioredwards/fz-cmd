# Source OMZ history library to make omz_history function available
source ~/.oh-my-zsh/lib/history.zsh 2>/dev/null || {
  echo "Error: Could not source OMZ history library" >&2
  exit 1
}

# Load history file
fc -R 2>/dev/null

echo "Full history line count: $(omz_history 2>/dev/null | wc -l)"
echo ""

echo "Testing: omz_history"
for i in {1..10}; do
  start=$(date +%s.%N)
  omz_history >/dev/null 2>&1
  end=$(date +%s.%N)
  python3 -c "print($end - $start)"
done | awk '{
           sum += $1
           n++
         }
         END { if (n > 0) printf "Average: %.3fs\n\n", sum/n; else print "No timing data collected" }'
