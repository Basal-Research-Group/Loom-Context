#!/bin/bash
# Loom-Context — 60-second demo
# Run this in any project directory to see Loom in action.
#
# Prerequisites: pip install loom-context

set -e

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
echo "Try: loom bundle 'your specific task' . --stdout | pbcopy"
