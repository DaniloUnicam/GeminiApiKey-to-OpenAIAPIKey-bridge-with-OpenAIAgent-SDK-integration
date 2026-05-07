# Voice Call Agent - Architecture & Design Documentation

## Executive Summary

This document describes the **Voice Call Agent** - a real-time voice conversation system that integrates:
- **Google Gemini** (LLM) via OpenAI-compatible API
- **Google Cloud Speech-to-Text** (STT) for real-time transcription
- **Google Cloud Text-to-Speech** (TTS) for voice synthesis
- **PyAudio** for hardware audio I/O
- **AsyncIO** for concurrent non-blocking operations

**Target Latency**: < 1 second end-to-end (realistic: 800-1200ms)

---

## System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                 VOICE CALL AGENT LOOP                   │
└─────────────────────────────────────────────────────────┘

    INPUT PIPELINE:
    ┌──────────────┐       ┌──────────────┐       ┌────────────┐
    │🎙️ Microphone │──────▶│📝 STT Stream │──────▶│🤖 Agent    │
    │ (PyAudio)    │       │(Google Cloud)│       │(Gemini)    │
    └──────────────┘       └──────────────┘       └────────────┘
                                 ▲                      │
                                 │                      │
                          VAD Detection           Response Text
                         (WebRTC VAD)                    │
                                                        ▼
    OUTPUT PIPELINE:                            ┌────────────┐
    ┌──────────────┐◀─────────────────────────────│🔊 TTS     │
    │🔈 Speaker    │       Audio Chunks          │(Streaming) │
    │ (PyAudio)    │                            │(Google     │
    └──────────────┘                            │ Cloud)    │
                                                └────────────┘
```

### Component Breakdown

#### 1. **Audio Pipeline** (`audio_pipeline.py`)
Handles real-time audio capture and playback with Voice Activity Detection.

**Key Classes:**
- `AudioCapture`: Streams 20ms chunks from microphone at 16kHz mono
  - Uses PyAudio for hardware access
  - Integrates WebRTC VAD for speech detection
  - Yields: `(audio_bytes, is_speech_detected)`
  
- `AudioPlayback`: Streams audio chunks to speaker
  - Non-blocking async playback
  - Supports streaming mode (start playing while chunks arrive)

**Latency Impact:**
- Chunk duration: 20ms (industry standard for VAD)
- Hardware latency: ~20-50ms (OS dependent)
- **Total: ~40-70ms per cycle**

---

#### 2. **Speech-to-Text** (`google_stt_streaming.py`)
Real-time transcription with streaming recognition.

**Key Classes:**
- `GoogleSTTStreamer`: Async wrapper for Google Cloud Speech API
  - Streaming recognition config with `interim_results=True`
  - Uses "latest_long" model for accuracy
  - Non-blocking audio queue for chunk submission
  
- `STTWithVAD`: High-level orchestrator
  - Captures audio until silence detected
  - Coordinates streaming transcription
  - Returns final transcript

**Latency Breakdown:**
- Network roundtrip: ~100-200ms
- Streaming processing: ~200-300ms (per utterance)
- VAD silence detection: depends on content
- **Total: ~300-500ms average**

**Optimization Strategies:**
- `interim_results=True` for progressive feedback (not used in v1 but available)
- VAD filters empty chunks (reduces API calls)
- Single utterance mode avoids early termination

---

#### 3. **Gemini Agent** (`VoiceAgentMain.py`)
LLM processing layer with function call support.

**Key Classes:**
- `VoiceAgent`: Wrapper around openai-agents SDK
  - Uses AsyncOpenAI client pointing to Google's endpoint
  - Wraps Gemini model via `OpenAIChatCompletionsModel`
  - Supports tool/function calls (passthrough)
  - Truncates responses for TTS efficiency

**Latency Breakdown:**
- API network roundtrip: ~100-200ms
- Model inference: ~100-600ms (depends on complexity)
- Prompt processing: ~50-100ms
- **Total: ~250-900ms (typically ~400-600ms)**

**Optimizations:**
- Uses `gemini-2.5-flash` (fastest Gemini model)
- Response truncated to 500 chars (keeps TTS < 10s)
- Single synchronous execution per turn (no streaming in v1)

---

#### 4. **Text-to-Speech** (`google_tts_streaming.py`)
Speech synthesis with streaming output for low latency.

**Key Classes:**
- `GoogleTTSStreamer`: Async wrapper for Google Cloud TTS API
  - Splits text into sentences for parallel synthesis
  - Uses "it-IT-Neural2-A" voice (Italian, natural, fast)
  - Non-blocking synthesis via executor
  
- `TTSWithStreaming`: High-level orchestrator
  - Synthesizes while playing audio chunks
  - Pipelined latency: start playback before synthesis complete

**Latency Breakdown:**
- Sentence splitting: ~10ms
- API call per sentence: ~200-400ms each
- Audio generation: ~20-100ms per sentence
- Playback: concurrent with next synthesis
- **Total: ~400-600ms (with pipelining benefit)**

**Optimizations:**
- Parallel sentence synthesis (up to 3-5 sentences)
- LINEAR16 encoding (minimal compression, faster playback)
- Streaming playback (don't buffer entire response)
- SSML support available for future prosody control

---

#### 5. **Voice Call Orchestrator** (`voice_call_agent.py`)
Main event loop coordinating all components.

**Architecture:**
```python
async def run_conversation_loop():
    while is_running:
        # STEP 1: Capture & Transcribe
        user_text = await stt_vad.transcribe_until_silence()
        
        # STEP 2: LLM Processing
        agent_response = await agent.chat(user_text)
        
        # STEP 3: Synthesize & Play
        await tts.speak_text_streaming(agent_response, audio_playback)
```

**Key Features:**
- Sequential but optimized pipeline (no parallel STT/TTS)
- Metrics collection for latency monitoring
- Graceful shutdown with resource cleanup
- Error recovery with retry logic

---

## Latency Analysis & Optimization

### End-to-End Latency Breakdown

| Component | Best Case | Typical | Worst Case |
|-----------|-----------|---------|-----------|
| STT       | 200ms     | 350ms   | 600ms     |
| Agent     | 250ms     | 500ms   | 1000ms    |
| TTS       | 300ms     | 450ms   | 800ms     |
| **Total** | **750ms** | **1300ms** | **2400ms** |

### Current Optimizations (v1)

1. **Audio Chunking**: 20ms frames enable real-time VAD
2. **Streaming APIs**: Both STT and TTS support streaming
3. **VAD Filtering**: Skip empty audio (reduces STT calls)
4. **Model Selection**: Fast Gemini model (gemini-2.5-flash)
5. **Response Truncation**: 500 char limit keeps TTS < 10s
6. **Parallel Synthesis**: Multiple sentences synthesized concurrently

### Future Optimizations (v2+)

1. **Streamed Agent Response**: Start TTS while LLM generates text (pipelined latency)
2. **Connection Pooling**: Reuse HTTP connections to APIs
3. **Local Caching**: Cache frequent responses (greetings, facts)
4. **Edge Deployment**: Deploy STT/TTS locally (tradeoff: accuracy)
5. **WebRTC Integration**: Use LiveKit/Vapi for lower-level audio optimization
6. **Streaming Text Mode**: Send partial tokens to TTS as generated
7. **Wake Word Detection**: Eliminate always-listening latency

---

## AsyncIO Architecture

### Event Loop Design

```python
# Main event loop runs single-threaded
asyncio.run(voice_call_agent.run_conversation_loop())

# Within loop:
# - Blocking PyAudio calls → run_in_executor (thread pool)
# - Blocking Google APIs → run_in_executor (thread pool)
# - Async tasks → awaited directly
```

### Task Execution Model

| Task | Type | Executor |
|------|------|----------|
| Audio capture (pyaudio) | Blocking I/O | Thread Pool |
| STT API call | Blocking I/O | Thread Pool |
| Agent chat | CPU-bound | Thread Pool |
| TTS API call | Blocking I/O | Thread Pool |
| Audio playback | Blocking I/O | Thread Pool |
| Main loop | Async | Event Loop |

**Key Principle**: Keep event loop free for coordination; delegate blocking ops to executors.

---

## Configuration Management (`config.py`)

Centralized configuration with dataclasses:

```python
AudioConfig          # Sample rate, chunk size, VAD threshold
GoogleCloudConfig    # API endpoints, language, voice selection
AgentConfig          # Model, instructions, truncation
LatencyConfig        # Timeout values, target latency
```

**Environment Variables** (required in `.env`):
- `GEMINI_API_KEY_env` - Gemini API key
- `GOOGLE_CLOUD_CREDENTIALS` - Path to service account JSON
- `GOOGLE_CLOUD_PROJECT_ID` - GCP project ID (optional)

---

## Error Handling & Resilience

### Graceful Degradation

1. **Audio Capture Fails**: Log error, continue loop (retry microphone)
2. **STT Timeout**: Return empty string, prompt user to retry
3. **Agent Error**: Return fallback response in Italian
4. **TTS Fails**: Log error, skip audio playback

### Recovery Strategies

- Exponential backoff for API retries (not implemented in v1)
- Timeout thresholds for each component (configurable)
- Resource cleanup on shutdown (close streams, terminate PA)

---

## Performance Metrics Collection

The agent collects latency metrics during runtime:

```
Turn 1:
  STT latency: 425ms
  Agent latency: 620ms
  TTS latency: 380ms
  Total latency: 1425ms (⚠️ exceeds 1000ms target)

Turn 2:
  STT latency: 320ms
  Agent latency: 540ms
  TTS latency: 350ms
  Total latency: 1210ms

Average: 1318ms (recommendation: optimize agent response)
```

**Latency targets** are printed at startup and summarized on shutdown.

---

## Testing Strategy

### Unit Tests (`test_voice_agent.py`)

1. **Audio Capture**: Verify microphone input and VAD detection
2. **STT**: Transcribe known audio, validate accuracy
3. **TTS**: Synthesize text, verify audio output
4. **Agent**: Query with known input, verify response format
5. **Latency Benchmark**: Measure end-to-end times across 3 rounds

### Integration Tests

- Full conversation loop (manual speech test)
- Multi-turn conversation (context retention)
- Tool/function call invocation
- Shutdown and resource cleanup

---

## Deployment Considerations

### Single Machine (Local)
- Run `voice_call_agent.py` directly
- Microphone + speakers connected to same machine
- Good for development and testing

### Remote Audio (Future)
- Stream audio over WebRTC (LiveKit)
- Deploy agent logic on server
- Lower latency for remote users

### Production Hardening
- Add logging to cloud (Cloud Logging)
- Monitor error rates and latency (Cloud Monitoring)
- Rate limiting for API calls
- Circuit breaker for API failures

---

## Security & Privacy

### Credentials Management
- Service account JSON stored locally (not in git)
- API keys in environment variables
- No credential logging in debug output

### Audio Privacy
- Audio buffered in memory (not persisted)
- No audio recording to disk in v1
- Google Cloud APIs process audio per their policies

### Data Retention
- No conversation history stored locally (v1)
- Agent doesn't learn from interactions (stateless)
- Future: Optional session history with encryption

---

## Files & Dependencies

### Core Modules
| File | Purpose | Lines |
|------|---------|-------|
| `voice_call_agent.py` | Main orchestrator | ~300 |
| `audio_pipeline.py` | Audio I/O + VAD | ~200 |
| `google_stt_streaming.py` | STT API wrapper | ~250 |
| `google_tts_streaming.py` | TTS API wrapper | ~200 |
| `VoiceAgentMain.py` | Agent wrapper | ~150 |
| `config.py` | Configuration | ~100 |

### Dependencies
- `openai` - AsyncOpenAI client
- `openai-agents` - Agent SDK
- `google-cloud-speech` - STT API
- `google-cloud-texttospeech` - TTS API
- `pyaudio` - Audio hardware
- `numpy` - Audio buffer math
- `webrtcvad` - Voice detection
- `python-dotenv` - Env config

---

## Future Roadmap (v2, v3, ...)

### v2: Streaming Response
- [ ] Stream agent response tokens to TTS in real-time
- [ ] Pipelined latency: start speaking while LLM still generating
- [ ] Target: sub-500ms latency for typical responses

### v3: Tools & Function Calls
- [ ] Voice-native tool invocation
- [ ] Async tool execution feedback
- [ ] Long-running tool support (streaming results)

### v4: Advanced Audio
- [ ] Wake word detection (eliminate latency cost)
- [ ] Emotion/prosody control (SSML)
- [ ] Multi-speaker support
- [ ] Noise cancellation

### v5: WebRTC Integration
- [ ] LiveKit agent mode
- [ ] Vapi compatibility
- [ ] Low-latency remote deployment

---

## Debugging & Profiling

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Latency Profiling
```bash
python test_voice_agent.py benchmark
# Measures STT, Agent, TTS latencies across 3 rounds
```

### Component Testing
```bash
python test_voice_agent.py config  # Validate configuration
python test_voice_agent.py audio   # Test microphone
python test_voice_agent.py stt     # Test transcription
python test_voice_agent.py tts     # Test speech synthesis
python test_voice_agent.py agent   # Test LLM
```

---

## References

- **Google Cloud Speech-to-Text**: https://cloud.google.com/speech-to-text/docs
- **Google Cloud Text-to-Speech**: https://cloud.google.com/text-to-speech/docs
- **OpenAI Agents SDK**: https://github.com/openai/agents-python
- **PyAudio Documentation**: https://www.pyaudio.org/
- **WebRTC VAD**: https://github.com/wiseman/py-webrtcvad

---

**Last Updated**: 2025-05-07
**Version**: 1.0 (MVP - Voice Conversation Loop)
**Target Users**: Italian-speaking voice AI applications
