"""
Audio Pipeline: Async audio capture and Voice Activity Detection.
Handles real-time microphone input with chunking and VAD filtering.
"""
import asyncio
import pyaudio
import numpy as np
import webrtcvad
from typing import AsyncGenerator
from config import AUDIO_CONFIG
import logging

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    Captures audio from microphone in real-time using PyAudio.
    Applies WebRTC Voice Activity Detection (VAD) to filter silence.
    
    Yields: tuple(audio_bytes, is_speech) where:
      - audio_bytes: 20ms chunk of 16-bit PCM audio
      - is_speech: bool indicating if chunk likely contains speech
    """
    
    def __init__(self, sample_rate: int = AUDIO_CONFIG.SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * AUDIO_CONFIG.CHUNK_DURATION_MS / 1000)  # Samples per chunk
        self.channels = AUDIO_CONFIG.CHANNELS
        self.sample_width = AUDIO_CONFIG.SAMPLE_WIDTH
        
        # PyAudio stream
        self.pa = pyaudio.PyAudio()
        self.stream = None
        
        # VAD detector (20ms frames required)
        self.vad = webrtcvad.Vad(int(AUDIO_CONFIG.VAD_THRESHOLD * 3))  # 0-3 aggressiveness
        
        # Silence tracking
        self.silence_frames = 0
        self.silence_threshold_frames = int(
            AUDIO_CONFIG.SILENCE_DURATION_S * 1000 / AUDIO_CONFIG.CHUNK_DURATION_MS
        )
        
        logger.info(
            f"AudioCapture initialized: {sample_rate}Hz, "
            f"{self.chunk_size} samples/chunk, VAD threshold {AUDIO_CONFIG.VAD_THRESHOLD}"
        )
    
    async def start_capture(self) -> AsyncGenerator[tuple[bytes, bool], None]:
        """
        Start capturing audio from microphone and yield chunks.
        
        Yields:
            (audio_chunk_bytes, is_speech: bool)
        """
        try:
            # List available audio devices
            info = self.pa.get_device_count()
            logger.info(f"Found {info} audio devices")
            
            # Open input stream
            self.stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("✅ Audio stream opened (microphone ready)")
            
            while True:
                try:
                    # Read chunk from microphone (blocking, but running in async context)
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Run VAD detection in thread pool to avoid blocking event loop
                    loop = asyncio.get_event_loop()
                    is_speech = await loop.run_in_executor(
                        None, 
                        self.vad.is_speech, 
                        data, 
                        self.sample_rate
                    )
                    
                    # Track silence for end-of-speech detection
                    if not is_speech:
                        self.silence_frames += 1
                    else:
                        self.silence_frames = 0  # Reset silence counter on speech
                    
                    yield data, is_speech
                    
                    # Allow other tasks to run
                    await asyncio.sleep(0)
                    
                except Exception as e:
                    logger.error(f"Error reading audio chunk: {e}")
                    await asyncio.sleep(0.01)
        finally:
            self.stop_capture()
    
    def stop_capture(self):
        """Stop audio stream and cleanup."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            logger.info("✅ Audio stream closed")
        self.pa.terminate()
    
    def is_speech_end_detected(self) -> bool:
        """Check if silence threshold has been exceeded (speech ended)."""
        return self.silence_frames >= self.silence_threshold_frames
    
    def reset_silence_counter(self):
        """Reset silence counter (e.g., when new recording starts)."""
        self.silence_frames = 0


class AudioPlayback:
    """
    Handles audio playback from speaker asynchronously.
    Supports streaming playback (start playing while still receiving chunks).
    """
    
    def __init__(self, sample_rate: int = AUDIO_CONFIG.SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.channels = AUDIO_CONFIG.CHANNELS
        self.sample_width = AUDIO_CONFIG.SAMPLE_WIDTH
        
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self._is_playing = False
        
        logger.info(f"AudioPlayback initialized: {sample_rate}Hz")
    
    async def open_stream(self):
        """Open audio output stream."""
        loop = asyncio.get_event_loop()
        
        def _open():
            self.stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.sample_rate // 20  # 50ms buffer
            )
        
        await loop.run_in_executor(None, _open)
        logger.info("✅ Audio playback stream opened")
    
    async def play_audio_chunk(self, audio_chunk: bytes):
        """
        Play a single audio chunk asynchronously.
        Non-blocking playback.
        """
        if not self.stream:
            await self.open_stream()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.stream.write, audio_chunk)
    
    async def close_stream(self):
        """Close audio output stream."""
        if self.stream:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.stream.stop_stream)
            await loop.run_in_executor(None, self.stream.close)
            logger.info("✅ Audio playback stream closed")
        self.pa.terminate()
    
    async def play_audio_chunks_stream(self, chunk_generator: AsyncGenerator[bytes, None]):
        """
        Play audio chunks as they arrive (streaming).
        Useful for TTS streaming where chunks arrive one-by-one.
        """
        if not self.stream:
            await self.open_stream()
        
        self._is_playing = True
        try:
            async for chunk in chunk_generator:
                await self.play_audio_chunk(chunk)
        finally:
            self._is_playing = False


if __name__ == "__main__":
    # Test: Capture 5 seconds of audio and print stats
    import logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_capture():
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
                if elapsed >= 5:  # 5 seconds
                    break
        
        finally:
            capture.stop_capture()
        
        print(f"\n📊 Capture Test Results:")
        print(f"  Total frames: {frames_total}")
        print(f"  Speech frames: {frames_with_speech}")
        print(f"  Speech ratio: {frames_with_speech / frames_total * 100:.1f}%")
    
    asyncio.run(test_capture())
