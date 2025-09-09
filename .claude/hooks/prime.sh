#!/bin/bash

# Claude Code Hook: Initialize Context Bundle
# Creates a new context bundle session for tracking agent work

set -e

# Get the current project directory
CLAUDE_PROJECT_DIR=${CLAUDE_PROJECT_DIR:-$(pwd)}
BUNDLE_DIR="$CLAUDE_PROJECT_DIR/bundles"

# Create bundles directory if it doesn't exist
mkdir -p "$BUNDLE_DIR"

# Generate session ID with timestamp
SESSION_ID="session-$(date +%Y%m%d-%H%M%S)"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create the new bundle file
BUNDLE_FILE="$BUNDLE_DIR/$SESSION_ID.yml"

# Get the user prompt if available
USER_PROMPT="${CLAUDE_USER_PROMPT:-Initialize new context bundle session}"

# Create the bundle header
cat > "$BUNDLE_FILE" << EOF
session_id: "$SESSION_ID"
timestamp: "$TIMESTAMP"
description: "Context bundle session initialized"
actions:
  - type: "prime"
    timestamp: "$TIMESTAMP"
    prompt: "$USER_PROMPT"
EOF

# Create/update symlink to current session
ln -sf "$SESSION_ID.yml" "$BUNDLE_DIR/current-session.yml"

# Output success message
echo "🚀 Initialized new context bundle: $SESSION_ID"
echo "📁 Bundle file: bundles/$SESSION_ID.yml"
echo "🔗 Current session symlink: bundles/current-session.yml"
echo ""
echo "All read/write operations will now be logged to this bundle."
echo "Use /loadbundle bundles/$SESSION_ID.yml to restore this session state."

# Optional: Show bundle directory contents
echo ""
echo "Available bundles:"
ls -la "$BUNDLE_DIR"/*.yml 2>/dev/null | grep -v current-session || echo "  (none yet)"