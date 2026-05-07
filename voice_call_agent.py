"""
Voice Call Agent Main Orchestrator
===============================
End-to-end voice conversation loop: Capture → STT → Agent → TTS → Playback

Integrates:
- Audio I/O (microphone + speakers)
- Google Cloud STT (streaming)
- Gemini Agent (voice-enabled)
- Google Cloud TTS (streaming)

Architecture:
    [🎙️ Mic] → [📝 STT] → [🤖 Agent] → [🔊 TTS] → [🔈 Speaker]
                                                        ↓
                                                   (loop back)
"""

import asyncio
import signal
import logging
from datetime import datetime
from typing import Optional
import time

from audio_pipeline import AudioCapture, AudioPlayback
from google_stt_streaming import STTWithVAD
from google_tts_streaming import TTSWithStreaming
from VoiceAgentMain import VoiceAgentFactory
from config import validate_config, AUDIO_CONFIG, LATENCY_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class VoiceCallAgent:
    """
    Main Voice Call Agent orchestrator.
    
    Manages the complete voice conversation loop with latency tracking
    and graceful shutdown.
    """
    
    def __init__(self):
        self.is_running = False
        self.audio_capture: Optional[AudioCapture] = None
        self.audio_playback: Optional[AudioPlayback] = None
        self.stt_vad: Optional[STTWithVAD] = None
        self.tts: Optional[TTSWithStreaming] = None
        self.agent = None
        
        # Metrics
        self.turn_count = 0
        self.latency_times = {
            "stt": [],
            "agent": [],
            "tts": [],
            "total": []
        }
    
    async def initialize(self) -> bool:
        """Initialize all components (STT, TTS, Agent, Audio I/O)."""
        try:
            logger.info("🚀 Initializing Voice Call Agent...")
            
            # Validate configuration
            if not validate_config():
                logger.error("❌ Configuration validation failed")
                return False
            
            # Initialize agent
            self.agent = await VoiceAgentFactory.get_agent()
            
            # Initialize audio pipeline
            self.audio_capture = AudioCapture()
            self.audio_playback = AudioPlayback()
            
            # Initialize speech services
            self.stt_vad = STTWithVAD()
            self.tts = TTSWithStreaming()
            
            logger.info("✅ All components initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def run_conversation_loop(self):
        """
        Main conversation loop: Listen → Transcribe → Respond → Speak → Loop.
        
        Runs until user presses Ctrl+C or error occurs.
        """
        self.is_running = True
        
        logger.info("\n" + "="*60)
        logger.info("🎙️ VOICE CALL AGENT STARTED")
        logger.info("="*60)
        logger.info("📢 Speak now... (Press Ctrl+C to exit)")
        logger.info("="*60 + "\n")
        
        # Give system time to initialize
        await asyncio.sleep(1)
        
        turn = 0
        while self.is_running:
            try:
                turn += 1
                self.turn_count = turn
                
                logger.info(f"\n--- Turn {turn} ---")
                
                # STEP 1: Capture & Transcribe
                logger.info("🎙️ Listening for speech...")
                stt_start = time.time()
                
                user_text = await self.stt_vad.transcribe_until_silence(
                    self.audio_capture,
                    max_duration_s=AUDIO_CONFIG.MAX_RECORDING_S
                )
                
                stt_time = time.time() - stt_start
                self.latency_times["stt"].append(stt_time)
                
                if not user_text or not user_text.strip():
                    logger.warning("⚠️ No speech detected, retrying...")
                    continue
                
                logger.info(f"📝 Transcribed: {user_text}")
                logger.info(f"   STT latency: {stt_time*1000:.0f}ms")
                
                # STEP 2: Agent Processing
                logger.info("🤖 Agent processing...")
                agent_start = time.time()
                
                agent_response = await self.agent.chat(user_text)
                
                agent_time = time.time() - agent_start
                self.latency_times["agent"].append(agent_time)
                
                logger.info(f"💬 Response: {agent_response}")
                logger.info(f"   Agent latency: {agent_time*1000:.0f}ms")
                
                # STEP 3: Synthesize & Play
                logger.info("🔊 Synthesizing speech...")
                tts_start = time.time()
                
                # Stream TTS audio to speakers (non-blocking)
                await self.tts.speak_text_streaming(
                    agent_response,
                    self.audio_playback
                )
                
                tts_time = time.time() - tts_start
                self.latency_times["tts"].append(tts_time)
                
                logger.info(f"   TTS latency: {tts_time*1000:.0f}ms")
                
                # Calculate end-to-end latency
                total_time = stt_time + agent_time + tts_time
                self.latency_times["total"].append(total_time)
                
                logger.info(f"⏱️ Total latency: {total_time*1000:.0f}ms (target: {LATENCY_CONFIG.END_TO_END_TARGET_MS:.0f}ms)")
                
                if total_time > LATENCY_CONFIG.END_TO_END_TARGET_MS / 1000:
                    logger.warning(f"⚠️ Latency exceeded target (target: {LATENCY_CONFIG.END_TO_END_TARGET_MS:.0f}ms)")
                
                # Brief pause before next turn
                await asyncio.sleep(0.5)
            
            except KeyboardInterrupt:
                logger.info("\n⛔ User interrupted (Ctrl+C)")
                break
            except Exception as e:
                logger.error(f"❌ Error in conversation loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def shutdown(self):
        """Graceful shutdown: cleanup resources and print metrics."""
        logger.info("\n🛑 Shutting down Voice Call Agent...")
        
        self.is_running = False
        
        # Close audio streams
        if self.audio_capture:
            self.audio_capture.stop_capture()
        
        if self.audio_playback:
            await self.audio_playback.close_stream()
        
        # Print metrics
        self._print_metrics()
        
        logger.info("✅ Shutdown complete")
    
    def _print_metrics(self):
        """Print latency and performance metrics."""
        if self.turn_count == 0:
            return
        
        logger.info("\n" + "="*60)
        logger.info("📊 PERFORMANCE METRICS")
        logger.info("="*60)
        logger.info(f"Total turns: {self.turn_count}")
        
        for component in ["stt", "agent", "tts", "total"]:
            times = self.latency_times[component]
            if times:
                avg = sum(times) / len(times)
                min_t = min(times)
                max_t = max(times)
                logger.info(
                    f"{component.upper():6} | "
                    f"Avg: {avg*1000:6.0f}ms | "
                    f"Min: {min_t*1000:6.0f}ms | "
                    f"Max: {max_t*1000:6.0f}ms"
                )
        
        avg_total = sum(self.latency_times["total"]) / len(self.latency_times["total"])
        logger.info(f"\n🎯 Average end-to-end latency: {avg_total*1000:.0f}ms")
        
        target = LATENCY_CONFIG.END_TO_END_TARGET_MS / 1000
        if avg_total <= target:
            logger.info(f"✅ Target met ({target:.1f}s)!")
        else:
            logger.warning(f"⚠️ Target not met (target: {target:.1f}s, actual: {avg_total:.1f}s)")
        
        logger.info("="*60)


async def main():
    """Main entry point."""
    agent = VoiceCallAgent()
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler(signum, frame):
        logger.info("Signal received, initiating shutdown...")
        agent.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize
        if not await agent.initialize():
            logger.error("Failed to initialize agent")
            return
        
        # Run conversation loop
        await agent.run_conversation_loop()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    
    finally:
        # Cleanup
        await agent.shutdown()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║                 VOICE CALL AGENT v1.0                      ║
║            Powered by: Gemini + Google Cloud Audio          ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
