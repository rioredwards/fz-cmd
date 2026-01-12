echo "Full history line count: $(atuin history list --format "{command}" | wc -l)"
echo "Full history line count: $(atuin history list --format "{command}" | wc -l)"
echo ""

for args in \
  '--format "{command}"' \
  '--format "{command}"'; do
  echo "Testing: atuin history list $args"
  for i in {1..10}; do
    { time atuin history list $args >/dev/null; } 2>&1
  done | awk '/^real/ { sub(/^0m/, "", $2); sub(/s$/, "", $2); sum+=$2; n++ }
           END { printf "Average: %.3fs\n\n", sum/n }'
done
