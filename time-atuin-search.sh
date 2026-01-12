echo "Full search line count: $(atuin search --cmd-only 2>/dev/null | wc -l)"
echo "Limited search line count: $(atuin search --cmd-only --limit 500 2>/dev/null | wc -l)"
echo ""

for args in \
  '--cmd-only' \
  '--cmd-only --limit 500'; do
  echo "Testing: atuin search $args"
  for i in {1..10}; do
    start=$(date +%s.%N)
    atuin search $args >/dev/null 2>&1
    end=$(date +%s.%N)
    python3 -c "print($end - $start)"
  done | awk '{
           sum += $1
           n++
         }
         END { if (n > 0) printf "Average: %.3fs\n\n", sum/n; else print "No timing data collected" }'
done


