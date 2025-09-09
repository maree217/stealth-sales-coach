# Changelog

All notable changes to the Stealth Sales Coach project will be documented in this file.

## [1.1.0] - 2024-09-09

### 🔧 Fixed
- **LLM coaching system now works properly** - Fixed empty response issue that was preventing coaching advice generation
- **Improved JSON parsing** - Robust extraction of coaching advice from LLM responses with multiple fallback strategies
- **Speaker validation bug** - Fixed Speaker.UNKNOWN validation error in conversation turns

### 🎯 Improved  
- **Enhanced prompt engineering** - Switched to Phi-3.5 instruction format (`<|system|>`, `<|user|>`, `<|assistant|>`) for better response quality
- **Better stop tokens** - Using proper Phi-3.5 stop tokens for cleaner response generation
- **Noise filtering** - Added noise gate (0.01 threshold) to prevent processing of very quiet audio chunks
- **Energy-based VAD** - Increased minimum threshold to 0.05 to reduce false positive voice detection

### 🛠️ Added
- **Debug tools** - `debug_coach.py` with simplified interface and real-time feedback
- **LLM testing** - `test_llm.py` to verify model loading and prompt compatibility  
- **Coaching testing** - `test_coaching.py` to verify end-to-end coaching pipeline
- **Enhanced logging** - Better debugging output with raw LLM response logging

### 📚 Documentation
- Updated README with troubleshooting section
- Added debug tools usage instructions  
- Documented common issues and solutions
- Updated architecture documentation to reflect actual models used

### ⚙️ Technical Changes
- Switched from complex JSON prompts to Phi-3.5 instruction format
- Added multiple JSON extraction strategies (code blocks, brace matching, full response)
- Improved error handling and fallback mechanisms
- Enhanced VAD with noise gate filtering
- Added debug logging throughout the coaching pipeline

## [1.0.0] - 2024-09-08

### 🎉 Initial Release
- Real-time sales coaching system
- Local-only processing (no cloud dependencies)
- Whisper transcription support  
- Phi-3.5-mini LLM integration
- Rich terminal UI
- Speaker diarization capabilities
- Voice activity detection
- Privacy-first design