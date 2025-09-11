# Stealth Sales Coach

A completely local, privacy-first AI-powered sales coaching system that provides real-time insights during sales calls without any recording or cloud dependencies.

## ✨ Features

- 🎯 **Real-time coaching** - Get AI-powered insights during live calls
- 🔒 **100% local** - No data leaves your machine, complete privacy
- 🧠 **Smart analysis** - Context-aware coaching advice based on conversation flow
- 📊 **Resource efficient** - Optimized for modern laptops (tested on MacBook Air M3)
- 🚫 **No recordings** - Processes audio in real-time, no storage required
- 💪 **Production ready** - Stable system with process isolation and crash resistance

## Quick Start

### 1. **Installation**
```bash
# Clone the repository
git clone https://github.com/maree217/stealth-sales-coach.git
cd stealth-sales-coach

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. **Model Setup**
The system uses Microsoft Phi-3.5-mini (2.3GB) and OpenAI Whisper:
```bash
# Models are automatically downloaded on first run
# Or manually download to models_cache/ folder
```

### 3. **Start the Coach**
```bash
# Primary entry point (recommended)
python main.py

# Alternative: Run directly
python final_integrated_coach.py

# Test mode (verify setup)
python main.py --test
```

### 4. **Usage Options**
```bash
# Custom audio settings
python main.py --audio-threshold 0.005 --chunk-duration 5

# Show help
python main.py --help

# Run test suite
python -m tests.test_automation
```

## System Architecture

```
sales_coach/
├── main.py                    # 🚀 Primary entry point
├── final_integrated_coach.py  # 🎯 Core coach implementation  
├── run_sales_coach.py         # 🔄 Alternative runner
├── sales_coach/               # 📦 Core package
│   ├── src/
│   │   ├── audio/             # 🎤 Audio processing
│   │   ├── llm/               # 🧠 AI coaching
│   │   └── models/            # 📋 Data models
├── tests/                     # 🧪 Test suite
│   ├── test_audio.py          # Audio pipeline tests
│   ├── test_llm.py            # LLM coaching tests
│   ├── test_integration.py    # End-to-end tests
│   └── test_automation.py     # Automated test runner
├── config/                    # ⚙️ Configuration
│   └── default.yaml           # Default settings
└── docs/                      # 📚 Documentation
    ├── examples/              # Example outputs
    └── development/           # Development notes
```

## How It Works

1. **Audio Capture**: Captures 3-second audio chunks from your microphone
2. **Speech Recognition**: Uses OpenAI Whisper to transcribe speech locally
3. **AI Analysis**: Processes conversation context with Phi-3.5-mini
4. **Coaching Advice**: Provides real-time coaching suggestions
5. **Fallback System**: Uses rule-based coaching if AI encounters issues

## Configuration

Edit `config/default.yaml` to customize:

```yaml
models:
  llm_context_length: 8192      # Context window size
  llm_temperature: 0.3          # Response creativity
  
audio:
  sample_rate: 16000            # Audio sample rate
  chunk_duration: 3             # Processing interval
  threshold: 0.01               # Audio detection sensitivity
```

## Testing

The project includes a comprehensive test suite:

```bash
# Run all tests
python -m tests.test_automation

# Individual test categories
python -m tests.test_audio      # Audio pipeline
python -m tests.test_llm        # LLM coaching
python -m tests.test_display    # UI/display
python -m tests.test_integration # End-to-end
```

## Performance

**Tested Configuration:**
- **Hardware**: MacBook Air M3, 16GB RAM
- **Stability**: 10+ minutes continuous operation without crashes
- **Latency**: 1-2 seconds for transcription + coaching
- **Accuracy**: >90% transcription accuracy in quiet environments

## Privacy & Security

- **100% Local Processing**: No cloud APIs, no internet required
- **No Data Storage**: Audio processed in real-time, not saved
- **No Telemetry**: No usage data collected or transmitted
- **Open Source**: Full transparency, audit the code yourself

## Troubleshooting

### Common Issues

1. **No audio detected**: Check microphone permissions and adjust `--audio-threshold`
2. **LLM crashes**: System automatically falls back to rule-based coaching
3. **High CPU usage**: Reduce `llm_context_length` in config

### Debug Mode
```bash
# Test audio detection
python -m tests.test_audio

# Check system status
python main.py --test

# View detailed logs
tail -f logs/sales_coach.log
```

## Development

### Project Structure
- **Production Code**: `main.py`, `final_integrated_coach.py`
- **Core Package**: `sales_coach/` - Modular components
- **Tests**: `tests/` - Comprehensive test suite
- **Documentation**: `docs/` - Examples and development notes
- **Archive**: Development history preserved in `archive/`

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Run tests: `python -m tests.test_automation`
4. Submit pull request

## License

MIT License - see LICENSE file for details.

## Version History

- **v1.2** (Current) - Refactored architecture, comprehensive testing
- **v1.1** - Process isolation, stability improvements
- **v1.0** - Initial release with basic coaching

---

**Made with ❤️ for sales professionals who value privacy and performance.**