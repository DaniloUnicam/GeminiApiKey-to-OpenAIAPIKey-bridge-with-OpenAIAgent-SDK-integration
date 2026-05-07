# 🎙️ Voice Call Agent - End-to-End Voice Conversation System

Transform your text-based Gemini agent into a **real-time voice assistant** powered by:
- **Gemini 2.5 Flash** (LLM)
- **Google Cloud Speech-to-Text** (STT)
- **Google Cloud Text-to-Speech** (TTS)
- **PyAudio** (Hardware I/O)

**Live conversation latency: ~1-1.5 seconds end-to-end** (optimized from 2-3s)

---

## 🎯 Quick Start (5 min)

### 1. **Install Dependencies**

```bash
# Using uv (recommended)
uv add google-cloud-speech google-cloud-texttospeech pyaudio numpy webrtcvad

# Or using pip
pip install -r requirements.txt
```

### 2. **Setup Google Cloud**

```bash
# Create service account with permissions for:
# - Speech-to-Text API
# - Text-to-Speech API
# Download JSON key and set path in .env
```

### 3. **Configure Environment**

```bash
# Copy and edit .env
cp .env.example .env

# Add your credentials:
# GEMINI_API_KEY_env=<your-key>
# GOOGLE_CLOUD_CREDENTIALS=/path/to/service-account.json
```

### 4. **Validate Setup**

```bash
python setup_voice_agent.py
```

Expected output:
```
✅ Python 3.10
✅ google.cloud.speech
✅ google.cloud.texttospeech
✅ pyaudio
✅ .env configured
✅ Found 2 audio devices
```

### 5. **Run Agent**

```bash
python voice_call_agent.py

# Output:
# ============================================================
# 🎙️ VOICE CALL AGENT STARTED
# ============================================================
# 📢 Speak now... (Press Ctrl+C to exit)
# 
# --- Turn 1 ---
# 🎙️ Listening for speech...
# 📝 Transcribed: Ciao, come stai?
# 🤖 Agent processing...
# 💬 Response: Ciao! Sto bene, grazie per aver chiesto. Come posso aiutarti?
# 🔊 Synthesizing speech...
# ⏱️ Total latency: 1250ms
```

**Speak into your microphone, wait for the response, repeat!**

---

## 📚 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         VOICE CALL AGENT PIPELINE               │
├─────────────────────────────────────────────────┤
│ 🎙️ Microphone                                   │
│ ↓ (AudioCapture + WebRTC VAD)                   │
│ 📝 Google Cloud Speech-to-Text                  │
│ ↓ (Streaming recognition)                       │
│ 🤖 Gemini Agent (OpenAI-compatible API)         │
│ ↓ (LLM reasoning)                               │
│ 🔊 Google Cloud Text-to-Speech                  │
│ ↓ (Streaming synthesis)                         │
│ 🔈 Speaker (AudioPlayback)                      │
│ ↓ (loop back)                                   │
└─────────────────────────────────────────────────┘
```

**Key Components:**
- `audio_pipeline.py` - Microphone capture + speaker playback + VAD
- `google_stt_streaming.py` - Real-time speech recognition
- `google_tts_streaming.py` - Real-time voice synthesis  
- `VoiceAgentMain.py` - Gemini agent wrapper
- `voice_call_agent.py` - Main orchestrator + event loop

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

---

## 🧪 Testing & Validation

### Run All Tests
```bash
python test_voice_agent.py all
```

### Test Individual Components
```bash
# Configuration
python test_voice_agent.py config

# Microphone capture (record 3 sec)
python test_voice_agent.py audio

# Speech-to-text (speak, transcribe)
python test_voice_agent.py stt

# Text-to-speech (synthesize & play)
python test_voice_agent.py tts

# LLM agent response
python test_voice_agent.py agent

# End-to-end latency benchmark (3 rounds)
python test_voice_agent.py benchmark
```

### Expected Results
```
✅ Audio Capture: Detects speech with VAD
✅ STT: Transcribes Italian speech accurately (< 500ms)
✅ TTS: Synthesizes Italian speech naturally (< 600ms)
✅ Agent: Responds to queries in Italian
✅ Latency: Average < 1300ms end-to-end
```

---

## ⚙️ Configuration

### Audio Settings (`config.py` → `AudioConfig`)
```python
SAMPLE_RATE = 16000          # Hz (Google Cloud standard)
CHUNK_DURATION_MS = 20       # ms per chunk (VAD frame)
CHANNELS = 1                 # Mono
VAD_THRESHOLD = 0.3          # Sensitivity (0-1, higher = more aggressive)
SILENCE_DURATION_S = 1.0     # Seconds to detect end of speech
MAX_RECORDING_S = 30.0       # Max recording before force-stop
```

### Google Cloud Settings (`config.py` → `GoogleCloudConfig`)
```python
LANGUAGE_CODE = "it-IT"                  # Italian
STT_ENCODING = "LINEAR16"                # Audio format
TTS_VOICE_NAME = "it-IT-Neural2-A"      # Neural Italian voice
TTS_SPEAKING_RATE = 1.0                  # Normal speed
TTS_AUDIO_ENCODING = "LINEAR16"          # Output format
```

### Agent Settings (`config.py` → `AgentConfig`)
```python
AGENT_MODEL = "gemini-2.5-flash"         # Fast model
AGENT_INSTRUCTIONS = "..."               # System prompt
MAX_RESPONSE_LENGTH = 500                # Chars (keeps TTS < 10s)
```

### Latency Targets (`config.py` → `LatencyConfig`)
```python
END_TO_END_TARGET_MS = 1000              # Target total latency
STT_TIMEOUT_S = 10.0                     # Max wait for transcription
LLM_TIMEOUT_S = 15.0                     # Max wait for agent response
TTS_TIMEOUT_S = 10.0                     # Max wait for synthesis
```

---

## 🔍 Troubleshooting

### "No module named 'google'"
```bash
pip install google-cloud-speech google-cloud-texttospeech
```

### "Audio device error" or "No input devices"
**Install PortAudio** (system library for PyAudio):

- **macOS**: `brew install portaudio`
- **Ubuntu**: `sudo apt-get install portaudio19-dev`
- **Windows**: Download from http://www.portaudio.com/ or use binary installer

### "Google Cloud authentication failed"
```bash
# Verify credentials file exists
ls /path/to/service-account.json

# Verify .env has correct path
cat .env | grep GOOGLE_CLOUD_CREDENTIALS
```

### "STT timeout" or "Connection refused"
- Check internet connection
- Verify Google Cloud project has **Speech-to-Text API enabled**
- Try `python test_voice_agent.py stt` to isolate issue

### "Agent response very slow"
```bash
# Profile latency
python test_voice_agent.py benchmark

# Check which component is slow:
# - STT slow? (network/accuracy issue)
# - Agent slow? (LLM load or complex query)
# - TTS slow? (synthesis time or text length)
```

### "Agent response is gibberish"
- Language model may be receiving corrupted audio
- Try: `python test_voice_agent.py stt` to verify transcription accuracy
- Check VAD threshold (may be excluding speech)

---

## 🚀 Usage Examples

### Example 1: Simple Greeting
```
You:   "Ciao!"
Agent: "Ciao! Come stai? Sono qui per aiutarti."
```

### Example 2: Information Query
```
You:   "Qual è la capitale dell'Italia?"
Agent: "La capitale dell'Italia è Roma, situata nel Lazio, nel centro del paese."
```

### Example 3: Multi-turn Conversation
```
Turn 1:
You:   "Mi racconti una barzelletta?"
Agent: "Perchè il libro di matematica si è suicidato? Perché aveva troppi problemi!"

Turn 2:
You:   "Non è divertente!"
Agent: "Mi scusi! Proverò a fare di meglio. Vuoi sentire un'altra?"
```

### Example 4: Tool/Function Call (future)
```
You:   "Apri il browser"
Agent: [Opens browser] "Ho aperto il browser per te."
```

---

## 📊 Performance Metrics

### Typical Latency Breakdown
| Component | Time |
|-----------|------|
| Speech Recognition (STT) | 300-500ms |
| LLM Processing (Agent) | 300-800ms |
| Speech Synthesis (TTS) | 300-500ms |
| Audio I/O + Network | 100-200ms |
| **Total** | **~1000-2000ms** |

### Optimization Tips
1. **Shorter responses**: Agent truncates to 500 chars automatically
2. **Faster model**: Using `gemini-2.5-flash` (not `gemini-pro`)
3. **Streaming**: TTS starts playing while agent still responding
4. **Local VAD**: Reduces empty STT calls significantly
5. **Connection pooling**: Reuse Google Cloud connections (future)

### Monitoring
The agent logs latency for every turn:
```
Turn 1:
  🎙️ STT latency: 425ms
  🤖 Agent latency: 620ms
  🔊 TTS latency: 380ms
  ⏱️ Total latency: 1425ms

Average end-to-end latency: 1318ms
✅ Target met! (< 1500ms is acceptable)
```

---

## 🔐 Security & Privacy

### Credentials Management
- Store API keys in `.env` (not in git)
- Service account JSON is local-only
- Add `.env` to `.gitignore`:
  ```bash
  echo ".env" >> .gitignore
  ```

### Audio Privacy
- Audio is buffered in memory, **never written to disk** (v1)
- Google Cloud processes audio per their policies
- No conversation history stored locally

### Future Considerations
- Optional encrypted session history
- Audio filtering/anonymization
- Compliance with GDPR/privacy regulations

---

## 🛠️ Development & Customization

### Changing Language
```python
# config.py → GoogleCloudConfig
LANGUAGE_CODE = "es-ES"  # Spanish
# or
LANGUAGE_CODE = "fr-FR"  # French
# or
LANGUAGE_CODE = "de-DE"  # German
```

### Custom Agent Instructions
```python
# config.py → AgentConfig
AGENT_INSTRUCTIONS = """
You are a helpful Italian restaurant assistant.
Answer questions about our menu, hours, and reservations.
Keep responses concise and friendly.
"""
```

### Adjusting Voice/Prosody
```python
# config.py → GoogleCloudConfig
TTS_VOICE_NAME = "it-IT-Neural2-B"  # Different voice
TTS_SPEAKING_RATE = 0.85             # Slower speech
TTS_PITCH = 0.5                       # Higher pitch
```

### Tweaking Latency
```python
# config.py → LatencyConfig & AudioConfig
SILENCE_DURATION_S = 0.5              # Faster speech end detection
VAD_THRESHOLD = 0.5                   # More aggressive silence filtering
MAX_RESPONSE_LENGTH = 200             # Shorter responses = faster TTS
```

---

## 📚 File Reference

| File | Purpose |
|------|---------|
| `voice_call_agent.py` | 🎯 Main entry point - conversation loop |
| `VoiceAgentMain.py` | 🤖 Gemini agent wrapper with streaming |
| `audio_pipeline.py` | 🎙️ Audio I/O + Voice Activity Detection |
| `google_stt_streaming.py` | 📝 Google Cloud Speech-to-Text |
| `google_tts_streaming.py` | 🔊 Google Cloud Text-to-Speech |
| `config.py` | ⚙️ Centralized configuration |
| `test_voice_agent.py` | 🧪 Component testing & benchmarking |
| `setup_voice_agent.py` | 🚀 Environment validation |
| `ARCHITECTURE.md` | 📖 Detailed design documentation |
| `requirements.txt` | 📦 Python dependencies |
| `.env.example` | 🔑 Environment variable template |

---

## 🔮 Future Enhancements (Roadmap)

### v1.1 (Current)
- ✅ Basic voice conversation
- ✅ Real-time audio I/O
- ✅ Italian language support
- ✅ Latency monitoring

### v2.0 (Next)
- [ ] Streaming agent response (pipelined latency)
- [ ] Function call execution from voice
- [ ] Conversation memory/context
- [ ] Multi-turn state management

### v3.0 (Later)
- [ ] Wake word detection
- [ ] Multi-language support
- [ ] Emotion/prosody control (SSML)
- [ ] Noise cancellation

### v4.0+ (Advanced)
- [ ] WebRTC integration (LiveKit/Vapi)
- [ ] Edge-deployed STT/TTS
- [ ] Real-time speech translation
- [ ] Voice biometric authentication

---

## 📞 Support & Contributing

### Getting Help
1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
2. Run `python setup_voice_agent.py` to validate environment
3. Check logs: `tail -f voice_call_agent.log` (if logging enabled)

### Reporting Issues
When reporting bugs, include:
- OS and Python version: `python --version`
- Error log output
- Environment setup (audio devices, network)
- Results from: `python test_voice_agent.py benchmark`

### Contributing
Areas for contribution:
- Performance optimization (reduce latency)
- Additional language support
- Tool/function call framework
- Testing & benchmarking
- Documentation improvements

---

## 📝 License

This project uses open-source components:
- `openai-agents` - OpenAI License
- `google-cloud-*` - Apache 2.0
- `pyaudio` - MIT
- `webrtcvad` - BSD

---

## 🎓 Learning Resources

### Understanding the Pipeline
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) - detailed design
2. Study `voice_call_agent.py` - orchestration logic
3. Review `audio_pipeline.py` - audio processing

### Customization
1. Modify `config.py` for settings
2. Edit `VoiceAgentMain.py` for agent behavior
3. Adjust `google_*.py` for audio API parameters

### Debugging
1. Enable logging: `logging.basicConfig(level=logging.DEBUG)`
2. Run component tests: `python test_voice_agent.py <component>`
3. Profile latency: `python test_voice_agent.py benchmark`

---

**🎉 Enjoy real-time voice conversations with your Gemini agent!**

---

*Last Updated: May 2025 | Version: 1.0 MVP | For Italian voice AI applications*
