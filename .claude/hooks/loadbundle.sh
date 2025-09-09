#!/bin/bash

# Claude Code Hook: Load Context Bundle
# Restores agent state from a previous context bundle session

set -e

# Get the current project directory
CLAUDE_PROJECT_DIR=${CLAUDE_PROJECT_DIR:-$(pwd)}
BUNDLE_DIR="$CLAUDE_PROJECT_DIR/bundles"

# Extract bundle path from user prompt (expecting "/loadbundle path/to/bundle.yml")
BUNDLE_PATH=""

# Parse arguments - look for bundle path in user prompt
if [[ -n "${CLAUDE_USER_PROMPT}" ]]; then
    # Extract path after /loadbundle command
    BUNDLE_PATH=$(echo "$CLAUDE_USER_PROMPT" | sed -n 's|.*/loadbundle[[:space:]]*\([^[:space:]]*\).*|\1|p')
fi

# If no path specified, try to use current session
if [[ -z "$BUNDLE_PATH" ]]; then
    BUNDLE_PATH="$BUNDLE_DIR/current-session.yml"
    echo "No bundle path specified, using current session: $BUNDLE_PATH"
fi

# Make path absolute if it's relative
if [[ ! "$BUNDLE_PATH" =~ ^/ ]]; then
    BUNDLE_PATH="$CLAUDE_PROJECT_DIR/$BUNDLE_PATH"
fi

# Check if bundle file exists
if [[ ! -f "$BUNDLE_PATH" ]]; then
    echo "❌ Bundle file not found: $BUNDLE_PATH"
    echo "Available bundles:"
    ls -la "$BUNDLE_DIR"/*.yml 2>/dev/null || echo "  (no bundles found)"
    exit 1
fi

echo "📦 Loading context bundle: $BUNDLE_PATH"
echo ""

# Parse and display bundle information
SESSION_ID=$(grep "session_id:" "$BUNDLE_PATH" | cut -d'"' -f2)
TIMESTAMP=$(grep "timestamp:" "$BUNDLE_PATH" | cut -d'"' -f2)
DESCRIPTION=$(grep "description:" "$BUNDLE_PATH" | cut -d'"' -f2)

echo "🔍 Bundle Information:"
echo "  Session ID: $SESSION_ID"
echo "  Created: $TIMESTAMP"
echo "  Description: $DESCRIPTION"
echo ""

# Count different operation types
READ_COUNT=$(grep -c "type: \"read\"" "$BUNDLE_PATH" 2>/dev/null || echo 0)
WRITE_COUNT=$(grep -c "type: \"write\"" "$BUNDLE_PATH" 2>/dev/null || echo 0)
PRIME_COUNT=$(grep -c "type: \"prime\"" "$BUNDLE_PATH" 2>/dev/null || echo 0)

echo "📊 Bundle Statistics:"
echo "  Read operations: $READ_COUNT"
echo "  Write operations: $WRITE_COUNT"
echo "  Prime operations: $PRIME_COUNT"
echo "  Total actions: $((READ_COUNT + WRITE_COUNT + PRIME_COUNT))"
echo ""

# Create a context summary for the agent
CONTEXT_FILE="$BUNDLE_DIR/restored-context.md"

cat > "$CONTEXT_FILE" << EOF
# Restored Context from Bundle: $SESSION_ID

**Bundle Path:** $BUNDLE_PATH
**Created:** $TIMESTAMP
**Description:** $DESCRIPTION

## Session Summary
This context has been restored from a previous Claude Code session. The agent previously:
- Performed $READ_COUNT read operations
- Performed $WRITE_COUNT write operations
- Had $PRIME_COUNT initialization events

## Key Files Accessed
EOF

# Extract unique file paths from the bundle
echo "" >> "$CONTEXT_FILE"
echo "### Files Read:" >> "$CONTEXT_FILE"
grep -A1 "type: \"read\"" "$BUNDLE_PATH" | grep "file_path:" | cut -d'"' -f2 | sort -u | while read -r file; do
    echo "- \`$file\`" >> "$CONTEXT_FILE"
done

echo "" >> "$CONTEXT_FILE"
echo "### Files Modified:" >> "$CONTEXT_FILE"
grep -A1 "type: \"write\"" "$BUNDLE_PATH" | grep "file_path:" | cut -d'"' -f2 | sort -u | while read -r file; do
    echo "- \`$file\`" >> "$CONTEXT_FILE"
done

echo "" >> "$CONTEXT_FILE"
echo "## Recent Actions" >> "$CONTEXT_FILE"
echo "The following actions were performed in the previous session:" >> "$CONTEXT_FILE"
echo "" >> "$CONTEXT_FILE"

# Extract last 10 actions with timestamps
tail -n 50 "$BUNDLE_PATH" | grep -A4 "- type:" | while read -r line; do
    if [[ $line =~ type:.*\"(.*)\" ]]; then
        echo "**${BASH_REMATCH[1]}:**" >> "$CONTEXT_FILE"
    elif [[ $line =~ timestamp:.*\"(.*)\" ]]; then
        echo "  - Time: ${BASH_REMATCH[1]}" >> "$CONTEXT_FILE"
    elif [[ $line =~ summary:.*\"(.*)\" ]]; then
        echo "  - Summary: ${BASH_REMATCH[1]}" >> "$CONTEXT_FILE"
        echo "" >> "$CONTEXT_FILE"
    fi
done

echo "✅ Context bundle loaded successfully!"
echo "📄 Context summary written to: $CONTEXT_FILE"
echo ""
echo "The agent can now continue from where the previous session left off."
echo "Previous session state and file operations have been restored."

# Set this bundle as the current session for future operations
ln -sf "$(basename "$BUNDLE_PATH")" "$BUNDLE_DIR/current-session.yml"
echo "🔗 Set as current session for future logging."