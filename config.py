"""
Configuration module for Voice Call Agent.
Centralized settings for audio, Google Cloud APIs, and LLM.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AudioConfig:
    """Audio capture/playback parameters."""
    SAMPLE_RATE: int = 16000  # Hz - Google Cloud STT standard
    CHUNK_DURATION_MS: int = 20  # ms per chunk (320 samples at 16kHz)
    CHANNELS: int = 1  # Mono
    SAMPLE_WIDTH: int = 2  # 16-bit = 2 bytes
    VAD_THRESHOLD: float = 0.3  # WebRTC VAD sensitivity (0.0-1.0, higher = more aggressive)
    SILENCE_DURATION_S: float = 1.0  # Seconds of silence to trigger speech_end
    MAX_RECORDING_S: float = 30.0  # Max recording length before force-stop


@dataclass
class GoogleCloudConfig:
    """Google Cloud authentication and API settings."""
    CREDENTIALS_PATH: str = os.getenv("GOOGLE_CLOUD_CREDENTIALS", "")
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")
    LANGUAGE_CODE: str = "it-IT"  # Italian (can be configured per-user)
    STT_ENCODING: str = "LINEAR16"  # Linear PCM
    TTS_VOICE_NAME: str = "it-IT-Neural2-A"  # Italian female voice (Google Cloud)
    TTS_AUDIO_ENCODING: str = "LINEAR16"  # Raw audio (more efficient for streaming)
    TTS_SPEAKING_RATE: float = 1.0  # Normal speed
    TTS_PITCH: float = 0.0  # Neutral pitch


@dataclass
class AgentConfig:
    """LLM Agent settings."""
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY_env", "")
    AGENT_NAME: str = "Voice Assistant"
    AGENT_INSTRUCTIONS: str = (
        "You are a helpful Italian voice assistant. "
        "Keep responses concise (1-2 sentences) and natural for speech. "
        "Speak in Italian."
    )
    AGENT_MODEL: str = "gemini-2.5-flash"  # Fast Gemini model for low latency
    OPENAI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    ENABLE_TOOLS: bool = True  # Enable function calls
    MAX_RESPONSE_LENGTH: int = 500  # Characters - keeps TTS time reasonable


@dataclass
class LatencyConfig:
    """Latency optimization thresholds."""
    STT_TIMEOUT_S: float = 10.0  # Max wait for STT result
    LLM_TIMEOUT_S: float = 15.0  # Max wait for LLM response
    TTS_TIMEOUT_S: float = 10.0  # Max wait for TTS generation
    END_TO_END_TARGET_MS: float = 1000.0  # Target latency (for monitoring)


# Main config instances
AUDIO_CONFIG = AudioConfig()
GOOGLE_CLOUD_CONFIG = GoogleCloudConfig()
AGENT_CONFIG = AgentConfig()
LATENCY_CONFIG = LatencyConfig()


def validate_config() -> bool:
    """Validate that all required configurations are set."""
    errors = []
    
    if not AGENT_CONFIG.GEMINI_API_KEY:
        errors.append("❌ GEMINI_API_KEY_env not set in .env")
    
    if not GOOGLE_CLOUD_CONFIG.CREDENTIALS_PATH:
        errors.append("❌ GOOGLE_CLOUD_CREDENTIALS not set in .env (path to service account JSON)")
    
    if not os.path.exists(GOOGLE_CLOUD_CONFIG.CREDENTIALS_PATH):
        errors.append(f"❌ Google Cloud credentials file not found: {GOOGLE_CLOUD_CONFIG.CREDENTIALS_PATH}")
    
    if errors:
        print("\n".join(errors))
        return False
    
    print("✅ Configuration validated successfully")
    return True


if __name__ == "__main__":
    print("🔍 Voice Agent Configuration")
    print(f"  Audio: {AUDIO_CONFIG.SAMPLE_RATE}Hz, {AUDIO_CONFIG.CHANNELS}ch")
    print(f"  Language: {GOOGLE_CLOUD_CONFIG.LANGUAGE_CODE}")
    print(f"  Agent: {AGENT_CONFIG.AGENT_MODEL}")
    print(f"  Target latency: {LATENCY_CONFIG.END_TO_END_TARGET_MS}ms")
    validate_config()
