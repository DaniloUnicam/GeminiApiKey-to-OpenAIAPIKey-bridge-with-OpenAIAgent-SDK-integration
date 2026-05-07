"""
Google Cloud Speech-to-Text Streaming Module.
Real-time speech recognition with streaming input and partial/final results.
"""
import asyncio
import os
import queue  # Thread-safe queue for sync/async bridge
from typing import AsyncGenerator, Optional
from google.cloud import speech_v1
from google.api_core import gapic_v1
from config import GOOGLE_CLOUD_CONFIG, AUDIO_CONFIG, LATENCY_CONFIG
import logging
import time
import threading

logger = logging.getLogger(__name__)

# Set Google Cloud credentials from env
if GOOGLE_CLOUD_CONFIG.CREDENTIALS_PATH:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_CONFIG.CREDENTIALS_PATH


class GoogleSTTStreamer:
    """
    Streams audio chunks to Google Cloud Speech-to-Text API.
    Returns partial transcriptions in real-time, with final result when speech ends.
    
    Designed for low-latency, interactive voice conversations.
    Uses a thread-safe queue as bridge between async context and sync Google Cloud API.
    """
    
    def __init__(
        self,
        language_code: str = GOOGLE_CLOUD_CONFIG.LANGUAGE_CODE,
        encoding: str = speech_v1.RecognitionConfig.AudioEncoding.LINEAR16
    ):
        self.language_code = language_code
        self.encoding = encoding
        self.client = speech_v1.SpeechClient()
        
        # Config for streaming recognition
        self.config = speech_v1.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=AUDIO_CONFIG.SAMPLE_RATE,
            language_code=language_code,
            enable_automatic_punctuation=True,
            model="latest_long",
            use_enhanced=True,
        )
        
        # Streaming config for real-time results
        self.streaming_config = speech_v1.StreamingRecognitionConfig(
            config=self.config,
            interim_results=True,
            single_utterance=False
        )
        
        # Thread-safe queue for audio buffering (bridge between async and sync)
        self.audio_queue = queue.Queue(maxsize=100)
        self._transcription_buffer = ""
        self._is_streaming = False
        
        logger.info(f"GoogleSTTStreamer initialized ({language_code})")
    
    def _audio_generator(self):
        """
        Synchronous generator that yields streaming recognize requests.
        Consumes audio chunks from the thread-safe queue.
        Used by Google Cloud API (which expects sync generators).
        """
        try:
            while self._is_streaming:
                try:
                    # Get audio chunk from queue with timeout
                    audio_chunk = self.audio_queue.get(timeout=0.2)
                    
                    # Empty chunk signals end of stream
                    if not audio_chunk:
                        break
                    
                    # Wrap audio in StreamingRecognizeRequest
                    request = speech_v1.StreamingRecognizeRequest(audio_content=audio_chunk)
                    yield request
                
                except queue.Empty:
                    # No chunk available yet, continue waiting
                    continue
        except Exception as e:
            logger.warning(f"Error in _audio_generator: {e}")
    
    async def stream_transcription(self) -> AsyncGenerator[dict, None]:
        """
        Start streaming speech recognition.
        
        Yields:
            {"text": str, "is_final": bool, "confidence": float, "duration_ms": float}
        """
        self._is_streaming = True
        self._transcription_buffer = ""
        start_time = time.time()
        
        try:
            # Run blocking Google Cloud API call in thread pool
            loop = asyncio.get_event_loop()
            
            def _call_streaming_api():
                """Synchronous call to Google Cloud STT API."""
                responses = self.client.streaming_recognize(
                    self.streaming_config,
                    self._audio_generator()
                )
                return list(responses)  # Collect all responses
            
            # Execute in executor to avoid blocking event loop
            responses = await loop.run_in_executor(None, _call_streaming_api)
            
            # Process responses
            for response in responses:
                if not response.results:
                    continue
                
                result = response.results[0]
                elapsed_ms = (time.time() - start_time) * 1000
                
                if result.alternatives:
                    transcript = result.alternatives[0].transcript
                    confidence = result.alternatives[0].confidence if result.alternatives else 0.0
                    
                    yield {
                        "text": transcript,
                        "is_final": result.is_final,
                        "confidence": confidence,
                        "duration_ms": elapsed_ms
                    }
                    
                    if result.is_final:
                        self._transcription_buffer = transcript
                        logger.debug(f"Final: {transcript} (conf: {confidence:.2f})")
                    else:
                        logger.debug(f"Interim: {transcript}")
        
        except asyncio.CancelledError:
            logger.info("STT stream cancelled")
        except Exception as e:
            logger.error(f"Error in stream_transcription: {e}")
        finally:
            self._is_streaming = False
    
    async def send_audio_chunk(self, chunk: bytes):
        """
        Queue an audio chunk for transcription.
        Non-blocking (runs in executor since queue.Queue can block).
        """
        if self._is_streaming:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.audio_queue.put_nowait, chunk)
            except queue.Full:
                logger.warning("STT audio queue full, dropping chunk")
    
    async def stop_streaming(self):
        """Signal end of streaming and cleanup."""
        self._is_streaming = False
        
        # Send empty chunk to signal end-of-stream
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.audio_queue.put_nowait, b"")
        except queue.Full:
            pass
    
    def get_final_transcript(self) -> str:
        """Get the final transcription buffer."""
        return self._transcription_buffer


class STTWithVAD:
    """
    High-level wrapper: Speech-to-Text with Voice Activity Detection.
    
    Captures audio until silence is detected, then returns final transcription.
    Optimized for < 1s latency when possible.
    """
    
    def __init__(self):
        self.stt = GoogleSTTStreamer()
        self._final_result = ""
    
    async def transcribe_until_silence(
        self,
        audio_capture,
        max_duration_s: float = AUDIO_CONFIG.MAX_RECORDING_S
    ) -> str:
        """
        Capture and transcribe until silence detected or timeout.
        
        Args:
            audio_capture: AudioCapture instance
            max_duration_s: Max recording duration
        
        Returns:
            Final transcription text
        """
        audio_capture.reset_silence_counter()
        self._final_result = ""
        
        # Start STT streaming in background
        transcription_task = asyncio.create_task(self.stt.stream_transcription())
        
        # Capture audio until silence or max duration
        capture_task = asyncio.create_task(
            self._capture_and_send(audio_capture, max_duration_s)
        )
        
        try:
            # Wait for either silence detection or max duration
            await asyncio.wait_for(capture_task, timeout=max_duration_s)
        except asyncio.TimeoutError:
            logger.info("Max recording duration reached")
        finally:
            await self.stt.stop_streaming()
        
        # Collect remaining transcription
        try:
            async for partial in transcription_task:
                if partial["is_final"]:
                    self._final_result = partial["text"]
        except asyncio.CancelledError:
            pass
        
        transcription_task.cancel()
        
        logger.info(f"Transcription complete: {self._final_result}")
        return self._final_result
    
    async def _capture_and_send(self, audio_capture, max_duration_s: float):
        """Internal: capture audio and send to STT until silence."""
        start_time = asyncio.get_event_loop().time()
        
        async for chunk, is_speech in audio_capture.start_capture():
            # Send to STT
            await self.stt.send_audio_chunk(chunk)
            
            # Check for silence
            if audio_capture.is_speech_end_detected():
                logger.info("Silence detected - ending recording")
                break
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > max_duration_s:
                logger.info("Max duration reached")
                break
            
            await asyncio.sleep(0)


if __name__ == "__main__":
    # Test: Record audio and transcribe
    import logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_stt():
        from audio_pipeline import AudioCapture
        
        print("🎙️ Starting STT test (speak now, silence to stop)...")
        
        audio_capture = AudioCapture()
        stt_vad = STTWithVAD()
        
        try:
            result = await stt_vad.transcribe_until_silence(audio_capture)
            print(f"\n📝 Transcribed: {result}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            audio_capture.stop_capture()
    
    asyncio.run(test_stt())
