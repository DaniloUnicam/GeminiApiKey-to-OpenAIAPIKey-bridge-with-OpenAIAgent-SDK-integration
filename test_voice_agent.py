"""
Voice Agent Component Testing
=============================
Unit and integration tests for audio pipeline, STT, TTS, and Agent.

Run individual tests with: python test_voice_agent.py <test_name>
"""

import asyncio
import logging
from config import validate_config, AUDIO_CONFIG, GOOGLE_CLOUD_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_audio_capture():
    """Test: Capture 3 seconds of audio and detect speech."""
    print("\n" + "="*60)
    print("TEST 1: Audio Capture + VAD")
    print("="*60)
    print("🎙️ Recording for 3 seconds... Speak now!\n")
    
    from audio_pipeline import AudioCapture
    
    capture = AudioCapture()
    frames_with_speech = 0
    frames_total = 0
    
    try:
        start_time = asyncio.get_event_loop().time()
        async for chunk, is_speech in capture.start_capture():
            frames_total += 1
            if is_speech:
                frames_with_speech += 1
            
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= 3:
                break
    finally:
        capture.stop_capture()
    
    print(f"\n✅ Results:")
    print(f"   Total frames: {frames_total}")
    print(f"   Speech frames: {frames_with_speech}")
    print(f"   Speech ratio: {frames_with_speech / frames_total * 100:.1f}%")


async def test_stt_single():
    """Test: Transcribe 5 seconds of audio."""
    print("\n" + "="*60)
    print("TEST 2: Speech-to-Text (STT)")
    print("="*60)
    print("🎙️ Recording for up to 5 seconds... Speak now (silence to stop)\n")
    
    from audio_pipeline import AudioCapture
    from google_stt_streaming import STTWithVAD
    
    audio_capture = AudioCapture()
    stt_vad = STTWithVAD()
    
    try:
        result = await stt_vad.transcribe_until_silence(audio_capture, max_duration_s=5)
        print(f"\n✅ Transcribed: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        audio_capture.stop_capture()


async def test_tts_single():
    """Test: Synthesize Italian text to speech."""
    print("\n" + "="*60)
    print("TEST 3: Text-to-Speech (TTS)")
    print("="*60)
    
    text = "Ciao! Sono l'assistente vocale. Questo è un test della sintesi vocale."
    print(f"📝 Synthesizing: {text}\n")
    
    from audio_pipeline import AudioPlayback
    from google_tts_streaming import TTSWithStreaming
    
    tts_wrapper = TTSWithStreaming()
    audio_playback = AudioPlayback()
    
    try:
        print("🔊 Playing audio...")
        duration = await tts_wrapper.speak_text_streaming(text, audio_playback)
        print(f"\n✅ Playback completed in {duration:.2f}s")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await audio_playback.close_stream()


async def test_agent_single():
    """Test: Agent response to text input."""
    print("\n" + "="*60)
    print("TEST 4: Agent Response")
    print("="*60)
    
    test_input = "Ciao! Come stai? Che giorno è oggi?"
    print(f"👤 User input: {test_input}\n")
    
    from VoiceAgentMain import VoiceAgentFactory
    
    try:
        agent = await VoiceAgentFactory.get_agent()
        print("🤖 Agent processing...")
        response = await agent.chat(test_input)
        print(f"\n✅ Agent response: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_config():
    """Test: Validate configuration."""
    print("\n" + "="*60)
    print("TEST 0: Configuration Validation")
    print("="*60 + "\n")
    
    print("🔍 Configuration status:")
    print(f"   GEMINI_API_KEY: {'✅ Set' if GOOGLE_CLOUD_CONFIG.PROJECT_ID else '❌ Missing'}")
    print(f"   Google Cloud credentials: {'✅ Set' if GOOGLE_CLOUD_CONFIG.CREDENTIALS_PATH else '❌ Missing'}")
    print(f"   Audio sample rate: {AUDIO_CONFIG.SAMPLE_RATE} Hz")
    print(f"   Language: {GOOGLE_CLOUD_CONFIG.LANGUAGE_CODE}")
    
    valid = validate_config()
    if valid:
        print("\n✅ Configuration valid!")
    else:
        print("\n❌ Configuration incomplete - check .env file")
    
    return valid


async def run_all_tests():
    """Run all tests sequentially."""
    print("\n" + "#"*60)
    print("# VOICE AGENT COMPONENT TESTS")
    print("#"*60)
    
    # Configuration first
    config_ok = await test_config()
    if not config_ok:
        print("\n❌ Cannot proceed without valid configuration")
        return
    
    tests = [
        ("Audio Capture", test_audio_capture),
        ("STT", test_stt_single),
        ("TTS", test_tts_single),
        ("Agent", test_agent_single),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            logger.error(f"❌ Test '{name}' failed: {e}")
            failed += 1
    
    # Summary
    print("\n" + "#"*60)
    print(f"# TEST SUMMARY: {passed} passed, {failed} failed")
    print("#"*60 + "\n")


async def benchmark_latency():
    """Benchmark: Measure end-to-end latency."""
    print("\n" + "="*60)
    print("BENCHMARK: End-to-End Latency")
    print("="*60)
    print("🎙️ Testing full pipeline latency...\n")
    
    from audio_pipeline import AudioCapture, AudioPlayback
    from google_stt_streaming import STTWithVAD
    from google_tts_streaming import TTSWithStreaming
    from VoiceAgentMain import VoiceAgentFactory
    import time
    
    audio_capture = AudioCapture()
    audio_playback = AudioPlayback()
    stt_vad = STTWithVAD()
    tts_wrapper = TTSWithStreaming()
    agent = await VoiceAgentFactory.get_agent()
    
    latencies = {"stt": [], "agent": [], "tts": [], "total": []}
    
    num_rounds = 3
    print(f"Running {num_rounds} rounds...\n")
    
    try:
        for i in range(num_rounds):
            print(f"Round {i+1}/{num_rounds}:")
            
            # STT
            print("  🎙️ STT...", end="", flush=True)
            t_start = time.time()
            user_text = await stt_vad.transcribe_until_silence(audio_capture, max_duration_s=5)
            t_stt = time.time() - t_start
            latencies["stt"].append(t_stt)
            print(f" {t_stt*1000:.0f}ms")
            
            if not user_text:
                print("  ⚠️ No speech detected, skipping round")
                continue
            
            # Agent
            print("  🤖 Agent...", end="", flush=True)
            t_start = time.time()
            response = await agent.chat(user_text)
            t_agent = time.time() - t_start
            latencies["agent"].append(t_agent)
            print(f" {t_agent*1000:.0f}ms")
            
            # TTS
            print("  🔊 TTS...", end="", flush=True)
            t_start = time.time()
            await tts_wrapper.speak_text_streaming(response, audio_playback)
            t_tts = time.time() - t_start
            latencies["tts"].append(t_tts)
            print(f" {t_tts*1000:.0f}ms")
            
            total = t_stt + t_agent + t_tts
            latencies["total"].append(total)
            print(f"  ⏱️  Total: {total*1000:.0f}ms\n")
    
    finally:
        audio_capture.stop_capture()
        await audio_playback.close_stream()
    
    # Summary
    print("📊 Latency Summary:")
    for component in ["stt", "agent", "tts", "total"]:
        times = latencies[component]
        if times:
            avg = sum(times) / len(times)
            print(f"  {component.upper()}: {avg*1000:.0f}ms (samples: {len(times)})")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        tests = {
            "config": test_config,
            "audio": test_audio_capture,
            "stt": test_stt_single,
            "tts": test_tts_single,
            "agent": test_agent_single,
            "all": run_all_tests,
            "benchmark": benchmark_latency,
        }
        
        if test_name in tests:
            asyncio.run(tests[test_name]())
        else:
            print(f"❌ Unknown test: {test_name}")
            print(f"Available: {', '.join(tests.keys())}")
    else:
        # Default: run all tests
        asyncio.run(run_all_tests())
