# Stealth Sales Coach

A completely local, privacy-first AI-powered sales coaching system that provides real-time insights during sales calls without any recording or cloud dependencies.

## ✨ Recent Updates (v1.1)

- 🔧 **Fixed LLM coaching system** - Now properly generates coaching advice
- 🎯 **Improved prompt engineering** - Using Phi-3.5 instruction format for better responses
- 🔇 **Enhanced audio filtering** - Noise gate to reduce phantom audio detection
- 🐛 **Robust error handling** - Better JSON parsing and fallback mechanisms
- 🛠️ **Debug tools added** - Easy testing and troubleshooting utilities

## Features

- 🎯 **Real-time coaching** - Get insights during live calls
- 🔒 **100% local** - No data leaves your machine
- 👤 **Speaker separation** - Distinguishes between you and customer
- 🧠 **Smart analysis** - Detects conversation stages and provides contextual advice
- 📊 **Resource efficient** - Optimized for MacBook Air M3 (16GB RAM)
- 🚫 **No recordings** - Processes audio in real-time, no storage
- 🎚️ **Noise filtering** - Advanced VAD with noise gate to prevent false triggers

## Quick Start

1. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

2. **Download the Phi-3.5-mini model (2.3GB):**
   ```bash
   # Download manually to models_cache/ or the system will auto-detect
   # Compatible with Hugging Face Phi-3.5-mini-instruct-Q4_K_M.gguf
   ```

3. **Test the system first (recommended):**
   ```bash
   # Test LLM coaching system
   python test_coaching.py
   
   # Debug with simplified interface
   python debug_coach.py
   ```

4. **Run the main coach:**
   ```bash
   # Using config file (recommended)
   python -m sales_coach.cli start --config config/default.yaml --interactive
   
   # Or simple start
   python -m sales_coach.cli start
   ```

## System Requirements

- macOS 12+ (Monterey or later)
- 16GB RAM recommended (8GB minimum)
- M1/M2/M3 chip for optimal performance
- Python 3.9+

## Architecture

- **Audio capture**: CoreAudio/BlackHole for system + microphone audio
- **Voice Activity Detection**: Silero VAD with energy-based fallback and noise gate
- **Speech-to-text**: OpenAI Whisper (local inference, base model)
- **Speaker diarization**: Pyannote.audio (fallback mode for unsupported environments)
- **LLM**: Microsoft Phi-3.5-mini (Q4_K_M quantized, ~2.3GB, local inference)
- **Interface**: Rich terminal UI with real-time updates + debug tools

## Troubleshooting & Debug Tools

### Quick Tests

```bash
# Test LLM coaching system
python test_coaching.py

# Test LLM model directly  
python test_llm.py

# Debug with simplified interface
python debug_coach.py
```

### Common Issues

**LLM not generating responses:**
- Ensure Phi-3.5-mini model is in `models_cache/` directory
- Check that the model file is ~2.3GB and ends with `.gguf`
- Run `python test_llm.py` to verify model works

**Audio not detected:**
- Check audio device in config: `config/default.yaml`
- For system audio: Use BlackHole 2ch or similar virtual audio device
- For mic only: Use "MacBook Air Microphone" or your default input
- Run `debug_coach.py` to see real-time audio levels

**Phantom language detection:**
- Increase VAD threshold in config (default: 0.3)
- Check noise gate settings (prevents processing very quiet audio)
- Use energy-based VAD if Silero VAD unavailable

### Debug Mode

The debug coach provides real-time feedback with simple print output:

```bash
python debug_coach.py

# Shows:
# - Component initialization status
# - Real-time audio levels
# - Voice segment detection  
# - Transcription results
# - Coaching advice generation
# - Session statistics
```

## Privacy & Security

All processing happens locally on your machine. No audio, transcripts, or insights are ever sent to external servers or stored persistently (unless explicitly configured).

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](LICENSE) file.