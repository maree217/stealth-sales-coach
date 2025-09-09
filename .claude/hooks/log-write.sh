#!/bin/bash

# Claude Code Hook: Log Write Operations  
# Captures file write/edit operations and appends them to the current context bundle

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

# Extract file path and operation type from Claude tool environment variables
FILE_PATH="${CLAUDE_TOOL_ARGS_file_path:-${CLAUDE_FILE_PATH:-unknown}}"
TOOL_NAME="${CLAUDE_TOOL_NAME:-write}"

# Determine operation type
OPERATION="modify"
if [[ "$TOOL_NAME" == "Write" ]]; then
    OPERATION="create"
elif [[ "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "MultiEdit" ]]; then
    OPERATION="modify"
fi

# Generate timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Extract just the filename for summary
FILENAME=$(basename "$FILE_PATH" 2>/dev/null || echo "unknown")

# Create a more descriptive summary based on operation
SUMMARY=""
case $OPERATION in
    "create")
        SUMMARY="Created new file: $FILENAME"
        ;;
    "modify")
        SUMMARY="Modified existing file: $FILENAME"
        ;;
    *)
        SUMMARY="Updated $FILENAME"
        ;;
esac

# Append write operation to bundle
cat >> "$CURRENT_BUNDLE" << EOF
  - type: "write"
    timestamp: "$TIMESTAMP"
    file_path: "$FILE_PATH"
    summary: "$SUMMARY"
    operation: "$OPERATION"
EOF

echo "Logged write operation: $FILE_PATH ($OPERATION)" >&2