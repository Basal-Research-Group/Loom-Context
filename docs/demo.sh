#!/usr/bin/env bash
# Loom-Context — 60-second demo
# Run this in any project directory to see Loom in action.
#
# Prerequisites: pip install loom-context

set -euo pipefail

# Detect the host OS so we can tailor the final clipboard hint.
os_name=$(uname -s)
is_windows=false
copy_tool='pbcopy'

case "$os_name" in
  MINGW*|MSYS*|CYGWIN*)
    is_windows=true
    copy_tool='clip'
    os_label='Windows (Git Bash/Cygwin)'
    ;;
  Linux)
    if grep -qi microsoft /proc/version 2>/dev/null; then
      is_windows=true
      copy_tool='clip'
      os_label='Windows (WSL)'
    else
      os_label='Unix'
    fi
    ;;
  Darwin)
    os_label='macOS'
    ;;
  *)
    os_label=$os_name
    ;;
esac

if [[ "$is_windows" == true ]]; then
  echo "Detected $os_label environment — clipboard helpers will call '$copy_tool'."
  echo "If Loom commands fail, rerun this script from Git Bash or WSL."
  echo ""
else
  echo "Running on $os_label — clipboard helper is '$copy_tool'."
  echo ""
fi

echo "=== Loom-Context Demo ==="
echo ""

# Step 1: Scan and generate context (2s)
echo "Step 1: Scan project..."
loom init .
echo ""

# Step 2: Check health (instant)
echo "Step 2: Health check..."
loom doctor .
echo ""

# Step 3: See metrics (instant)
echo "Step 3: Layer metrics..."
loom metrics .
echo ""

# Step 4: Generate a task bundle (instant)
echo "Step 4: Task-specific bundle..."
loom bundle "refactor authentication" . --compact
echo ""

# Step 5: See prompt sizes
echo "Step 5: Prompt compression..."
echo "--- Full prompt ---"
loom prompt .
echo "--- Compact ---"
loom prompt . --compact
echo "--- Ultra-compact ---"
loom prompt . --ultra-compact
echo ""

# Step 6: Setup agents (interactive or --force)
echo "Step 6: Setup agents..."
loom setup . --preset claude --force
echo ""

echo "=== Demo complete ==="
echo "Try: loom bundle 'your specific task' . --stdout | $copy_tool"
if [[ "$copy_tool" == 'clip' ]]; then
  echo "Use | clip to copy into Windows clipboard or redirect to a file if clip is unavailable."
fi
