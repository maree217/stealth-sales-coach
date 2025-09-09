# 🚀 Quick Start Guide - Stealth Sales Coach

## ✅ Setup Complete!

Your Stealth Sales Coach is now installed and ready to use! Here's what has been configured:

### 🔑 **Authentication**
- ✅ HuggingFace token configured: `hf_zpxr...sAuY`
- ✅ Environment variables set in `.env`

### 📦 **Models Downloaded**
- ✅ **Whisper base model** (142MB) - for speech transcription
- ✅ **Phi-3.5-mini-instruct** (2.5GB) - for AI coaching analysis
- ✅ **Silero VAD** - for voice activity detection

### 🎧 **Audio Setup**
- ✅ **BlackHole 2ch detected** - Perfect for capturing system audio
- ✅ Available devices:
  - `iPhone Microphone` (if connected)
  - `BlackHole 2ch` - **Recommended for calls** 
  - `MacBook Air Microphone` - Basic fallback
  - `System + BlackHole` - Multi-output device

## 🎯 **How to Use**

### **1. For Video/Voice Calls:**
```bash
cd "/Users/rammaree/sales coach"
source venv/bin/activate
export HF_TOKEN=your_huggingface_token_here
python -m sales_coach.cli start --interactive
```

### **2. Test Audio Setup:**
```bash
python -m sales_coach.cli test-audio
```

### **3. List Available Commands:**
```bash
python -m sales_coach.cli --help
```

## 🎨 **What You'll See**

When running the interactive coach, you'll get a live dashboard showing:

```
┌─ Stealth Sales Coach - Session: 00:05:23 ─┐
│                                             │
├─ Live Conversation ──────┬─ AI Coach ──────┤
│ [15:30:45] YOU: Hello,    │ Priority: HIGH  │
│ thank you for joining     │ Category: RAPPORT│
│ today's call...          │                 │
│                          │ 💡 Insight:     │
│ [15:30:52] CUSTOMER:     │ Great opening!   │
│ Thanks for having me...  │ Now transition  │
│                          │ to discovery    │
│                          │                 │
│                          │ 🎯 Action:      │
│                          │ Ask about their │
│                          │ current challenges│
└──────────────────────────┴─────────────────┘
│ Turns: 8 | Coaching: 3 | Audio chunks: 127   │
└─────────────────────────────────────────────┘
```

## 🔧 **Audio Configuration Tips**

### **For Best Results:**
1. **Use BlackHole 2ch** - Already detected on your system
2. **Set as input device** in your video call app (Zoom, Teams, etc.)
3. **The coach will hear both sides** of the conversation

### **Quick Audio Test:**
```bash
python -m sales_coach.cli test-audio --duration 5
```
*Speak and play audio - you should see activity levels*

## 📖 **Available Commands**

| Command | Description |
|---------|-------------|
| `start` | Start the coaching session |
| `devices` | List audio devices |
| `test-audio` | Test audio capture |
| `status` | Show system status |
| `setup-guide` | Detailed setup instructions |
| `config-init` | Create custom config file |

## 🎭 **Demo Mode (Without Calls)**

Want to test without a real call?

```bash
# Start the coach
python -m sales_coach.cli start --interactive

# In another terminal, play audio files or speak into mic
# The coach will analyze whatever audio it captures
```

## 🚨 **Troubleshooting**

### **If CLI command not found:**
```bash
# Use Python module directly:
python -m sales_coach.cli start --interactive
```

### **If models fail to load:**
```bash
# Re-download models:
python scripts/download_models.py
```

### **If audio doesn't work:**
```bash
# Test audio setup:
python scripts/setup_audio.py
```

## 🎉 **You're Ready!**

Your Stealth Sales Coach is fully operational:

- **100% Local** - No data leaves your machine
- **Real-time Analysis** - Coaching appears during calls  
- **Privacy First** - No recordings stored
- **Production Ready** - Optimized for your M3 MacBook Air

**Start your first coaching session:**
```bash
cd "/Users/rammaree/sales coach"
source venv/bin/activate
export HF_TOKEN=your_huggingface_token_here
python -m sales_coach.cli start --interactive
```

Happy coaching! 🎯