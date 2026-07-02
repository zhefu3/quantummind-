#!/usr/bin/env bash
# QuantumMind one-command runner (Claude / Anthropic).
#
# Usage:
#   export ANTHROPIC_API_KEY=sk-ant-...      # set your key first
#   ./run_claude.sh
#
# With no key set, it falls back to mock mode (plumbing check, no real reasoning).

set -e
cd "$(dirname "$0")"

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "!! ANTHROPIC_API_KEY is not set -> running in MOCK mode (placeholder output)."
  echo "   To get real results:  export ANTHROPIC_API_KEY=your_key   then re-run."
  echo
else
  echo ">> ANTHROPIC_API_KEY found -> using Claude."
  echo ">> Installing the anthropic package if needed..."
  python3 -m pip install --quiet anthropic >/dev/null 2>&1 || pip3 install --quiet anthropic
  export QM_BACKEND=anthropic
  export QM_MODEL="${QM_MODEL:-claude-sonnet-4-6}"
  echo ">> Model: $QM_MODEL"
  echo
fi

echo "=== Running the full pipeline on the test set ==="
python3 -m quantummind.run --all

echo
echo "=== Running Layer-1 evaluation ==="
python3 -m quantummind.run --eval

echo
echo "Done. See the outputs/ folder for report_*.md and evaluation.json"
