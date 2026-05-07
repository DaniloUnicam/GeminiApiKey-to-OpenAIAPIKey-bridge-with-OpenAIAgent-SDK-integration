"""
Google Cloud Text-to-Speech Streaming Module.
Converts text responses to speech with streaming audio output for low latency.
"""
import asyncio
import os
from typing import AsyncGenerator, List
from google.cloud import texttospeech_v1
from config import GOOGLE_CLOUD_CONFIG, AUDIO_CONFIG, LATENCY_CONFIG
import logging

logger = logging.getLogger(__name__)

# Set Google Cloud credentials from env
if GOOGLE_CLOUD_CONFIG.CREDENTIALS_PATH:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_CONFIG.CREDENTIALS_PATH


class GoogleTTSStreamer:
    """
    Streams text-to-speech synthesis from Google Cloud.
    Returns audio chunks as they become available (streaming synthesis).
    
    Optimized for low-latency voice responses.
    """
    
    def __init__(
        self,
        voice_name: str = GOOGLE_CLOUD_CONFIG.TTS_VOICE_NAME,
        language_code: str = GOOGLE_CLOUD_CONFIG.LANGUAGE_CODE,
        audio_encoding: str = texttospeech_v1.AudioEncoding.LINEAR16
    ):
        self.client = texttospeech_v1.TextToSpeechClient()
        self.voice_name = voice_name
        self.language_code = language_code
        self.audio_encoding = audio_encoding
        
        # Voice configuration
        self.voice = texttospeech_v1.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=texttospeech_v1.SsmlVoiceGender.FEMALE
        )
        
        # Audio config
        self.audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=audio_encoding,
            sample_rate_hertz=AUDIO_CONFIG.SAMPLE_RATE,
            speaking_rate=GOOGLE_CLOUD_CONFIG.TTS_SPEAKING_RATE,
            pitch=GOOGLE_CLOUD_CONFIG.TTS_PITCH
        )
        
        logger.info(f"GoogleTTSStreamer initialized ({voice_name})")
    
    async def synthesize_text_stream(
        self,
        text: str,
        chunk_size: int = 100  # Characters per request for streaming effect
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize text to speech with streaming chunks.
        
        Strategy: Break text into sentences, synthesize each in parallel,
        and stream back audio as it arrives.
        
        Args:
            text: Text to synthesize
            chunk_size: Max characters per synthesis request (for streaming effect)
        
        Yields:
            Audio chunks (LINEAR16 PCM format)
        """
        if not text or not text.strip():
            logger.warning("Empty text for TTS")
            return
        
        # Truncate if too long (TTS has limits and we want fast responses)
        max_chars = GOOGLE_CLOUD_CONFIG.MAX_RESPONSE_LENGTH
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            logger.warning(f"TTS text truncated to {max_chars} chars")
        
        # Split text into sentences for streaming
        sentences = self._split_sentences(text)
        
        # Create tasks for parallel synthesis
        synthesis_tasks = [
            self._synthesize_chunk(sentence)
            for sentence in sentences
        ]
        
        # Yield audio as each task completes (not necessarily in order)
        # For better UX, maintain order instead
        try:
            for audio_bytes in await asyncio.gather(*synthesis_tasks, return_exceptions=False):
                if audio_bytes:
                    yield audio_bytes
        except Exception as e:
            logger.error(f"Error in synthesize_text_stream: {e}")
    
    async def _synthesize_chunk(self, text: str) -> bytes:
        """
        Synthesize a single text chunk to speech (async wrapper).
        """
        if not text.strip():
            return b""
        
        loop = asyncio.get_event_loop()
        
        def _synthesize():
            try:
                # Create synthesis request
                input_text = texttospeech_v1.SynthesisInput(text=text)
                
                # Call Google Cloud API (blocking)
                response = self.client.synthesize_speech(
                    input=input_text,
                    voice=self.voice,
                    audio_config=self.audio_config,
                    timeout=LATENCY_CONFIG.TTS_TIMEOUT_S
                )
                
                return response.audio_content
            except Exception as e:
                logger.error(f"Error in TTS synthesis: {e}")
                return b""
        
        # Run blocking API call in executor to avoid blocking async loop
        return await asyncio.wait_for(
            loop.run_in_executor(None, _synthesize),
            timeout=LATENCY_CONFIG.TTS_TIMEOUT_S
        )
    
    def _split_sentences(self, text: str, max_chars: int = 200) -> List[str]:
        """
        Split text into sentences for streaming synthesis.
        
        Simple heuristic: split on '.', '!', '?', but keep chunks reasonable.
        """
        import re
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Recombine short sentences to avoid too many API calls
        combined = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chars:
                current_chunk += (" " if current_chunk else "") + sentence
            else:
                if current_chunk:
                    combined.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            combined.append(current_chunk)
        
        return [s.strip() for s in combined if s.strip()]
    
    async def synthesize_full(self, text: str) -> bytes:
        """
        Synthesize complete text to full audio (non-streaming).
        Useful if you want to buffer entire response before playback.
        """
        audio_chunks = []
        async for chunk in self.synthesize_text_stream(text):
            audio_chunks.append(chunk)
        
        return b"".join(audio_chunks)


class TTSWithStreaming:
    """
    High-level wrapper: Text-to-Speech with automatic streaming.
    
    Starts playback while synthesis is happening (pipelined latency).
    """
    
    def __init__(self):
        self.tts = GoogleTTSStreamer()
    
    async def speak_text_streaming(
        self,
        text: str,
        audio_playback
    ) -> float:
        """
        Synthesize text and play audio chunks as they arrive.
        
        Args:
            text: Text to speak
            audio_playback: AudioPlayback instance for playback
        
        Returns:
            Total synthesis + playback duration in seconds
        """
        import time
        
        start_time = time.time()
        
        try:
            # Stream TTS chunks and play them immediately
            await audio_playback.play_audio_chunks_stream(
                self.tts.synthesize_text_stream(text)
            )
        except Exception as e:
            logger.error(f"Error in speak_text_streaming: {e}")
        
        elapsed = time.time() - start_time
        logger.info(f"TTS playback completed in {elapsed:.2f}s")
        
        return elapsed


if __name__ == "__main__":
    # Test: Synthesize Italian text
    import logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_tts():
        from audio_pipeline import AudioPlayback
        
        text = "Ciao! Questo è un test della sintesi vocale. Come stai oggi?"
        print(f"🔊 Synthesizing: {text}")
        
        tts_wrapper = TTSWithStreaming()
        audio_playback = AudioPlayback()
        
        try:
            duration = await tts_wrapper.speak_text_streaming(text, audio_playback)
            print(f"\n✅ Playback completed in {duration:.2f}s")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await audio_playback.close_stream()
    
    asyncio.run(test_tts())
