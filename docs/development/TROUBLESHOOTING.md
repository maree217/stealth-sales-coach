# Context Bundle System - Troubleshooting Guide

## ❌ "Not Working" - Common Issues & Solutions

### Issue 1: Hooks Not Executing Automatically

**Symptom**: `/prime` and `/loadbundle` commands don't work, no automatic logging of read/write operations.

**Solutions**:

#### Option A: Configure Global Claude Code Settings
1. Open/create `~/.claude/settings.json`
2. Add the hook configuration:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/rammaree/testbun/.claude/hooks/log-read.sh"
          }
        ]
      },
      {
        "matcher": "Write|Edit|MultiEdit", 
        "hooks": [
          {
            "type": "command",
            "command": "/Users/rammaree/testbun/.claude/hooks/log-write.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "/prime",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/rammaree/testbun/.claude/hooks/prime.sh"
          }
        ]
      },
      {
        "matcher": "/loadbundle",
        "hooks": [
          {
            "type": "command", 
            "command": "/Users/rammaree/testbun/.claude/hooks/loadbundle.sh"
          }
        ]
      }
    ]
  }
}
```

#### Option B: Use Absolute Paths in Project Settings
1. Edit `.claude/settings.json` in this directory
2. Replace `$(pwd)` with absolute paths:

```bash
sed -i '' 's|$(pwd)|/Users/rammaree/testbun|g' .claude/settings.json
```

### Issue 2: Permission Errors

**Symptom**: "Permission denied" errors when hooks try to execute.

**Solution**:
```bash
chmod +x .claude/hooks/*.sh
```

### Issue 3: Bundle Directory Missing

**Symptom**: Hooks fail with "No such file or directory" for bundles.

**Solution**:
```bash
mkdir -p bundles
```

### Issue 4: Environment Variables Not Set

**Symptom**: Hooks can't find the right paths or files.

**Solution**: All scripts have been updated to use `$(pwd)` instead of environment variables.

## ✅ Manual Testing

You can test each component manually to verify they work:

### Test Prime Script:
```bash
./.claude/hooks/prime.sh
```

### Test Write Logging:
```bash
CLAUDE_TOOL_NAME="Write" CLAUDE_TOOL_ARGS_file_path="/Users/rammaree/testbun/test.txt" ./.claude/hooks/log-write.sh
```

### Test Read Logging:
```bash
CLAUDE_TOOL_ARGS_file_path="/Users/rammaree/testbun/README.md" ./.claude/hooks/log-read.sh
```

### Test Load Bundle:
```bash
CLAUDE_USER_PROMPT="/loadbundle bundles/session-20250909-070317.yml" ./.claude/hooks/loadbundle.sh
```

## 🔧 Setup Verification

1. **Check directory structure**:
```bash
ls -la .claude/hooks/
ls -la bundles/
```

2. **Verify hook permissions**:
```bash
ls -la .claude/hooks/*.sh
```

3. **Check settings file**:
```bash
cat .claude/settings.json
```

## 📞 Still Not Working?

If the system still doesn't work after these steps:

1. **Check Claude Code version**: Make sure you're using a version that supports hooks
2. **Restart Claude Code**: After changing settings, restart the application
3. **Check logs**: Look for error messages in Claude Code output
4. **Try manual testing**: Use the manual test commands above to isolate the issue

## 🚨 Last Resort: Alternative Setup

If hooks still don't work, you can use the system manually:

1. **Start session**: `./.claude/hooks/prime.sh`
2. **After work**: `./.claude/hooks/loadbundle.sh` (edit script to specify bundle path)
3. **Manual logging**: Use the CLAUDE_TOOL_* environment variables shown in manual testing

The core functionality works - it's just a matter of getting Claude Code to execute the hooks automatically.