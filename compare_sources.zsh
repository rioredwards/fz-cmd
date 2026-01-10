#!/bin/zsh
# Compare old vs new approach for gathering functions and aliases
# Run this script interactively: source compare_sources.zsh

OUTDIR="$HOME/.dotfiles/zsh/fz-cmd/comparison"
mkdir -p "$OUTDIR"

echo "Gathering data for comparison..."

# ========== OLD APPROACH (from my-old-app/functions-aliases.zsh) ==========
echo "  - Old approach: functions..."
print -l ${(k)functions} 2>/dev/null | grep -E '^[a-zA-Z_][a-zA-Z0-9_]*$' | sort -u > "$OUTDIR/old_functions.txt"

echo "  - Old approach: aliases..."
alias 2>/dev/null | sed -E "s/alias //" | sort -u > "$OUTDIR/old_aliases.txt"

# ========== NEW APPROACH (current Python scripts) ==========
echo "  - New approach: functions..."
python3 "$HOME/.dotfiles/zsh/fz-cmd/sources/source_functions.py" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); [print(c['command']) for c in d['commands']]" | \
  sort -u > "$OUTDIR/new_functions.txt"

echo "  - New approach: aliases..."
python3 "$HOME/.dotfiles/zsh/fz-cmd/sources/source_aliases.py" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); [print(c['command']) for c in d['commands']]" | \
  sort -u > "$OUTDIR/new_aliases.txt"

# ========== SUMMARY ==========
echo ""
echo "=== RESULTS ==="
echo "Files saved to: $OUTDIR"
echo ""
echo "Functions:"
echo "  Old: $(wc -l < "$OUTDIR/old_functions.txt") entries"
echo "  New: $(wc -l < "$OUTDIR/new_functions.txt") entries"
echo ""
echo "Aliases:"
echo "  Old: $(wc -l < "$OUTDIR/old_aliases.txt") entries"
echo "  New: $(wc -l < "$OUTDIR/new_aliases.txt") entries"
echo ""
echo "To compare, run:"
echo "  diff $OUTDIR/old_functions.txt $OUTDIR/new_functions.txt"
echo "  diff $OUTDIR/old_aliases.txt $OUTDIR/new_aliases.txt"
echo ""
echo "Or view side-by-side:"
echo "  code --diff $OUTDIR/old_functions.txt $OUTDIR/new_functions.txt"
