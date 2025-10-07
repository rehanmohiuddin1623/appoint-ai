import base64
import io
import os
import tempfile
from typing import Optional
from gtts import gTTS
import openai
from dotenv import load_dotenv
from deepgram import DeepgramClient, SpeakOptions
import asyncio
import httpx
import time

load_dotenv()


class TTSService:
    """Text-to-Speech service with multiple provider support"""
    
    def __init__(self, provider: str = "deepgram"):
        self.provider = provider
        
        # Initialize Deepgram client
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        if self.deepgram_api_key:
            try:
                self.deepgram = DeepgramClient(self.deepgram_api_key)
            except Exception as e:
                print(f"Deepgram TTS client initialization failed: {e}")
                self.deepgram = None
        else:
            self.deepgram = None
            
        # Initialize OpenAI client
        if provider == "openai":
            try:
                import openai
                self.openai_client = openai.OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    timeout=30.0  # Add explicit timeout
                )
            except Exception as e:
                print(f"OpenAI TTS client initialization failed: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
    
    def text_to_speech(self, text: str, voice: str = "alloy", speed: float = 1.0) -> bytes:
        """Convert text to speech audio bytes with timeout handling"""
        start_time = time.time()
        
        try:
            print(f"Starting TTS generation with {self.provider} for text: {text[:50]}...")
            
            if self.provider == "deepgram" and self.deepgram:
                result = self._deepgram_tts(text, voice)
                print(f"Deepgram TTS completed in {time.time() - start_time:.2f} seconds")
                return result
            elif self.provider == "openai" and self.openai_client:
                result = self._openai_tts(text, voice, speed)
                print(f"OpenAI TTS completed in {time.time() - start_time:.2f} seconds")
                return result
            else:
                print(f"Falling back to gTTS for provider {self.provider}")
                result = self._gtts_tts(text)
                print(f"gTTS completed in {time.time() - start_time:.2f} seconds")
                return result
        except Exception as e:
            print(f"TTS Error after {time.time() - start_time:.2f} seconds: {e}")
            # Ultra-fast fallback to gTTS
            try:
                print("Attempting gTTS fallback...")
                return self._gtts_tts(text)
            except Exception as fallback_e:
                print(f"Fallback TTS also failed: {fallback_e}")
                raise e
    
    def _deepgram_tts(self, text: str, voice: str = "aura-asteria-en") -> bytes:
        """Deepgram TTS implementation with optimized settings"""
        try:
            options = SpeakOptions(
                model=voice,
                encoding="linear16",
                sample_rate=16000,
                channels=1
            )
            
            # Use sync API for faster response
            response = self.deepgram.speak.v("1").save(
                text,
                options=options
            )
            
            return response
            
        except Exception as e:
            print(f"Deepgram TTS error: {e}")
            raise
    
    def _openai_tts(self, text: str, voice: str = "alloy", speed: float = 1.0) -> bytes:
        """OpenAI TTS implementation"""
        response = self.openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=speed
        )
        return response.content
    
    def _gtts_tts(self, text: str, lang: str = "en") -> bytes:
        """Google TTS implementation (fallback)"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(temp_file.name)
            
            with open(temp_file.name, "rb") as f:
                audio_bytes = f.read()
            
            os.unlink(temp_file.name)
            return audio_bytes
    
    def text_to_base64_audio(self, text: str, voice: str = "alloy", speed: float = 1.0) -> str:
        """Convert text to base64 encoded audio with error handling"""
        try:
            # For Deepgram, use the configured voice from environment
            if self.provider == "deepgram":
                voice = os.getenv("TTS_VOICE", "aura-asteria-en")
            
            audio_bytes = self.text_to_speech(text, voice, speed)
            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error in text_to_base64_audio: {e}")
            raise


class ASRService:
    """Automatic Speech Recognition service"""
    
    def __init__(self):
        try:
            import openai
            self.openai_client = openai.OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=30.0  # Add explicit timeout
            )
        except Exception as e:
            print(f"OpenAI ASR client initialization failed: {e}")
            self.openai_client = None
            
        # Initialize Deepgram client
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        if self.deepgram_api_key:
            try:
                from deepgram import DeepgramClient, PrerecordedOptions
                self.deepgram = DeepgramClient(self.deepgram_api_key)
                self.PrerecordedOptions = PrerecordedOptions
            except Exception as e:
                print(f"Deepgram ASR client initialization failed: {e}")
                self.deepgram = None
        else:
            self.deepgram = None
    
    def audio_to_text(self, audio_data: bytes, provider: str = "deepgram") -> str:
        """Convert audio bytes to text"""
        try:
            if provider == "deepgram" and self.deepgram:
                return self._deepgram_asr(audio_data)
            elif provider == "openai" and self.openai_client:
                return self._openai_asr(audio_data)
            else:
                # Fallback to OpenAI if available
                if self.openai_client:
                    return self._openai_asr(audio_data)
                else:
                    return "Speech recognition service not available."
        except Exception as e:
            print(f"ASR Error: {e}")
            # Fallback to OpenAI if Deepgram fails
            if provider != "openai" and self.openai_client:
                try:
                    return self._openai_asr(audio_data)
                except:
                    pass
            return "Sorry, I couldn't process the audio."
    
    def _deepgram_asr(self, audio_data: bytes) -> str:
        """Deepgram ASR implementation"""
        try:
            # Configure Deepgram options
            options = self.PrerecordedOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                punctuate=True
            )
            
            # Create payload with audio data
            payload = {"buffer": audio_data}
            
            # Send request to Deepgram
            response = self.deepgram.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )
            
            # Extract transcript
            if response.results and response.results.channels:
                alternatives = response.results.channels[0].alternatives
                if alternatives and len(alternatives) > 0:
                    return alternatives[0].transcript.strip()
            
            return "No speech detected."
            
        except Exception as e:
            print(f"Deepgram ASR error: {e}")
            raise
    
    def _openai_asr(self, audio_data: bytes) -> str:
        """OpenAI Whisper ASR implementation"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()
            
            with open(temp_file.name, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            os.unlink(temp_file.name)
            return transcript.strip()
    
    def _google_asr(self, audio_data: bytes) -> str:
        """Fallback ASR implementation - returns a message since speech_recognition is not compatible with Python 3.13"""
        return "Speech recognition fallback not available. Please use OpenAI Whisper."
    
    def base64_audio_to_text(self, base64_audio: str, provider: str = "deepgram") -> str:
        """Convert base64 encoded audio to text"""
        try:
            audio_bytes = base64.b64decode(base64_audio)
            return self.audio_to_text(audio_bytes, provider)
        except Exception as e:
            print(f"Base64 decode error: {e}")
            return "Sorry, I couldn't process the audio."


class AudioProcessor:
    """Utility class for audio processing"""
    
    @staticmethod
    def convert_audio_format(audio_data: bytes, input_format: str, output_format: str = "wav") -> bytes:
        """Convert audio from one format to another - simplified for Python 3.13 compatibility
        
        Note: This simplified version returns the original audio data since OpenAI Whisper
        and Deepgram can handle various audio formats directly.
        """
        # Since we're using OpenAI Whisper and Deepgram which support multiple formats,
        # we can return the original data without conversion
        return audio_data
    
    @staticmethod
    def validate_audio_data(audio_data: bytes, max_size_mb: int = 25) -> bool:
        """Validate audio data size and format"""
        size_mb = len(audio_data) / (1024 * 1024)
        return size_mb <= max_size_mb
    
    @staticmethod
    def base64_to_audio_bytes(base64_audio: str) -> bytes:
        """Convert base64 string to audio bytes"""
        try:
            return base64.b64decode(base64_audio)
        except Exception as e:
            print(f"Base64 decode error: {e}")
            return b""
    
    @staticmethod
    def audio_bytes_to_base64(audio_bytes: bytes) -> str:
        """Convert audio bytes to base64 string"""
        return base64.b64encode(audio_bytes).decode('utf-8')


# Service instances
tts_service = TTSService(provider=os.getenv("TTS_PROVIDER", "deepgram"))
asr_service = ASRService()
audio_processor = AudioProcessor()
