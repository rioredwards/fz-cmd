echo "Full list line count: $(atuin history list --format "{command}" --reverse=false --print0 2>/dev/null | wc -l)"
echo ""

for args in \
  '--format "{command}" --reverse=false --print0'; do
  echo "Testing: atuin history list $args"
  for i in {1..10}; do
    start=$(date +%s.%N)
    eval "atuin history list $args" >/dev/null 2>&1
    end=$(date +%s.%N)
    python3 -c "print($end - $start)"
  done | awk '{
           sum += $1
           n++
         }
         END { if (n > 0) printf "Average: %.3fs\n\n", sum/n; else print "No timing data collected" }'
done


