#!/bin/bash

# Claude Code Hook: Log Read Operations
# Captures file read operations and appends them to the current context bundle

set -e

# Get the current project directory
CLAUDE_PROJECT_DIR=${CLAUDE_PROJECT_DIR:-$(pwd)}
BUNDLE_DIR="$CLAUDE_PROJECT_DIR/bundles"
CURRENT_BUNDLE="$BUNDLE_DIR/current-session.yml"

# Create bundles directory if it doesn't exist
mkdir -p "$BUNDLE_DIR"

# Check if we have a current session bundle
if [[ ! -f "$CURRENT_BUNDLE" ]]; then
    echo "No active bundle found. Run /prime to start a new session." >&2
    exit 0
fi

# Extract file path from Claude tool environment variables
FILE_PATH="${CLAUDE_TOOL_ARGS_file_path:-${CLAUDE_FILE_PATH:-unknown}}"

# Generate timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Generate a simple content hash if file exists
CONTENT_HASH=""
if [[ -f "$FILE_PATH" ]]; then
    CONTENT_HASH=$(shasum -a 256 "$FILE_PATH" 2>/dev/null | cut -d' ' -f1 | head -c 12)
fi

# Extract just the filename for summary
FILENAME=$(basename "$FILE_PATH" 2>/dev/null || echo "unknown")

# Append read operation to bundle
cat >> "$CURRENT_BUNDLE" << EOF
  - type: "read"
    timestamp: "$TIMESTAMP"
    file_path: "$FILE_PATH"
    content_hash: "$CONTENT_HASH"
    summary: "Read $FILENAME"
EOF

echo "Logged read operation: $FILE_PATH" >&2