"""
Quick Setup & Usage Guide for Voice Call Agent
===============================================

This script validates the environment and helps with initial setup.
Run this BEFORE attempting to run the main agent.
"""

import os
import sys
import subprocess
from pathlib import Path

# Force UTF-8 encoding for stdout on Windows to support emojis and box-drawing characters
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


def check_python_version():
    """Check Python version (3.9+)."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ required (you have {version.major}.{version.minor})")
        return False
    print(f"✅ Python {version.major}.{version.minor}")
    return True


def check_dependencies():
    """Check if all required packages are installed."""
    required_packages = [
        "openai",
        "google.cloud.speech",
        "google.cloud.texttospeech",
        "pyaudio",
        "numpy",
        "webrtcvad",
        "agents",
        "dotenv",
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Install missing packages:")
        print(f"   uv add {' '.join(missing)}")
        return False
    
    return True


def check_env_file():
    """Check .env file for required credentials."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("📝 Create a .env file with:")
        print("   GEMINI_API_KEY_env=your_gemini_api_key")
        print("   GOOGLE_CLOUD_CREDENTIALS=/path/to/service-account.json")
        print("   GOOGLE_CLOUD_PROJECT_ID=your_project_id")
        return False
    
    env_vars = {}
    with open(".env", "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    
    required_vars = ["GEMINI_API_KEY_env", "GOOGLE_CLOUD_CREDENTIALS", "GOOGLE_CLOUD_PROJECT_ID"]
    missing_vars = [v for v in required_vars if not env_vars.get(v)]
    
    if missing_vars:
        print(f"❌ Missing in .env: {', '.join(missing_vars)}")
        return False
    
    print("✅ .env configured")
    
    # Check credentials file
    creds_path = env_vars.get("GOOGLE_CLOUD_CREDENTIALS", "")
    if not Path(creds_path).exists():
        print(f"❌ Google Cloud credentials file not found: {creds_path}")
        return False
    
    print(f"✅ Google Cloud credentials file found")
    return True


def check_audio_devices():
    """Check if audio input/output devices are available."""
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        
        num_devices = pa.get_device_count()
        if num_devices == 0:
            print("❌ No audio devices found")
            pa.terminate()
            return False
        
        print(f"✅ Found {num_devices} audio devices:")
        
        for i in range(num_devices):
            info = pa.get_device_info_by_index(i)
            has_input = info["maxInputChannels"] > 0
            has_output = info["maxOutputChannels"] > 0
            if has_input and has_output:
                device_type = "Input/Output"
            elif has_input:
                device_type = "Input"
            elif has_output:
                device_type = "Output"
            else:
                device_type = "Unknown"
            print(f"   [{i}] {device_type}: {info['name']}")
        
        pa.terminate()
        return True
    
    except Exception as e:
        print(f"❌ Error checking audio devices: {e}")
        print("   (You may need to install PortAudio system library)")
        print("   On macOS: brew install portaudio")
        print("   On Ubuntu: sudo apt-get install portaudio19-dev")
        print("   On Windows: Install from http://www.portaudio.com/")
        return False


def print_usage_guide():
    """Print usage guide."""
    guide = """
╔════════════════════════════════════════════════════════════╗
║           VOICE CALL AGENT - USAGE GUIDE                   ║
╚════════════════════════════════════════════════════════════╝

🚀 QUICK START:
   python voice_call_agent.py

🧪 TESTING INDIVIDUAL COMPONENTS:
   python test_voice_agent.py config    # Check configuration
   python test_voice_agent.py audio     # Test microphone capture
   python test_voice_agent.py stt       # Test speech-to-text
   python test_voice_agent.py tts       # Test text-to-speech
   python test_voice_agent.py agent     # Test LLM agent
   python test_voice_agent.py all       # Run all tests
   python test_voice_agent.py benchmark # Measure latency

📊 ARCHITECTURE:

    [🎙️ Microphone]
            ↓ (Audio Stream)
    [📝 Google Cloud STT]
            ↓ (Transcribed Text)
    [🤖 Gemini Agent]
            ↓ (Response Text)
    [🔊 Google Cloud TTS]
            ↓ (Audio Stream)
    [🔈 Speaker]
            ↓
        (loop back to microphone)

⚙️ CONFIGURATION:
   - Audio parameters: config.py (AUDIO_CONFIG)
   - Google Cloud settings: config.py (GOOGLE_CLOUD_CONFIG)
   - Agent behavior: config.py (AGENT_CONFIG)
   - Latency targets: config.py (LATENCY_CONFIG)

🔧 TROUBLESHOOTING:

   Q: "No module named 'google'"
   A: pip install google-cloud-speech google-cloud-texttospeech

   Q: "Audio device error" or "No input devices"
   A: Install PortAudio system library (see setup_voice_agent.py)

   Q: "Google Cloud authentication failed"
   A: Verify GOOGLE_CLOUD_CREDENTIALS path points to valid JSON file

   Q: "STT not working (timeout)"
   A: Check internet connection, ensure Google Cloud project has
      Speech-to-Text API enabled

   Q: "Agent response very slow"
   A: Check API latency with: python test_voice_agent.py benchmark
      Consider using faster model or check network connection

📚 FILES OVERVIEW:

   voice_call_agent.py         - Main entry point (conversation loop)
   VoiceAgentMain.py           - Agent wrapper (Gemini + tools)
   audio_pipeline.py           - Audio I/O + VAD
   google_stt_streaming.py     - Speech-to-Text
   google_tts_streaming.py     - Text-to-Speech
   config.py                   - Configuration & validation
   test_voice_agent.py         - Component tests

📞 EXAMPLE INTERACTION:

   Agent: "Ascolta! Sono pronto. Parla quando vuoi."
   You:   "Qual è la capitale dell'Italia?"
   Agent: "La capitale dell'Italia è Roma, situata nel Lazio."
   You:   "Mi piace! E dove si trova?"
   Agent: "Roma si trova nel centro dell'Italia, sul fiume Tevere..."

🎯 PERFORMANCE TARGETS:

   - STT latency:     < 500ms (speech to text)
   - Agent latency:   < 800ms (LLM processing)
   - TTS latency:     < 600ms (text to speech)
   - Total latency:   < 1000ms (end-to-end, ideally)

   Monitor with: python test_voice_agent.py benchmark

💡 TIPS FOR BETTER PERFORMANCE:

   1. Use faster Gemini model: "gemini-2.5-flash" (already set)
   2. Keep agent responses short (max 500 chars)
   3. Use local VAD to reduce empty STT calls
   4. Stream TTS chunks while LLM still processing
   5. Cache frequent responses
   6. Use regional Google Cloud endpoints

🔐 SECURITY:
   - Keep .env file out of git (add to .gitignore)
   - Don't commit service account JSON to repo
   - Rotate Gemini API keys regularly
   - Use IAM roles with minimal permissions for service account

📱 NEXT STEPS (Future Enhancements):

   1. Add function call support (tool execution via voice)
   2. Integrate with LiveKit for WebRTC
   3. Add emotion/prosody to TTS (SSML)
   4. Implement conversation memory
   5. Multi-language support
   6. Wake word detection
   7. Real-time metrics dashboard

"""
    print(guide)


def main():
    """Run setup checks."""
    print("""
╔════════════════════════════════════════════════════════════╗
║       VOICE CALL AGENT - SETUP VALIDATOR                   ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Config", check_env_file),
        ("Audio Devices", check_audio_devices),
    ]
    
    print()
    results = {}
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        print("-" * 40)
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        print("\n🚀 Ready to run: python voice_call_agent.py")
    else:
        print(f"⚠️ Some checks failed ({passed}/{total})")
        print("\nFix the issues above, then run setup again.")
    
    print("="*60)
    
    # Show usage guide
    print_usage_guide()


if __name__ == "__main__":
    main()
