import base64
import io
import os
import tempfile
from typing import Optional
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
import openai
from dotenv import load_dotenv

load_dotenv()


class TTSService:
    """Text-to-Speech service with multiple provider support"""
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        if provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception as e:
                print(f"OpenAI TTS client initialization failed: {e}")
                self.client = None
    
    def text_to_speech(self, text: str, voice: str = "alloy", speed: float = 1.0) -> bytes:
        """Convert text to speech audio bytes"""
        try:
            if self.provider == "openai":
                return self._openai_tts(text, voice, speed)
            else:
                return self._gtts_tts(text)
        except Exception as e:
            print(f"TTS Error: {e}")
            # Fallback to gTTS
            return self._gtts_tts(text)
    
    def _openai_tts(self, text: str, voice: str = "alloy", speed: float = 1.0) -> bytes:
        """OpenAI TTS implementation"""
        response = self.client.audio.speech.create(
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
        """Convert text to base64 encoded audio"""
        audio_bytes = self.text_to_speech(text, voice, speed)
        return base64.b64encode(audio_bytes).decode('utf-8')


class ASRService:
    """Automatic Speech Recognition service"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"OpenAI ASR client initialization failed: {e}")
            self.openai_client = None
    
    def audio_to_text(self, audio_data: bytes, provider: str = "openai") -> str:
        """Convert audio bytes to text"""
        try:
            if provider == "openai":
                return self._openai_asr(audio_data)
            else:
                return self._google_asr(audio_data)
        except Exception as e:
            print(f"ASR Error: {e}")
            # Fallback to Google Speech Recognition
            return self._google_asr(audio_data)
    
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
        """Google Speech Recognition implementation (fallback)"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()
            
            try:
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                os.unlink(temp_file.name)
                return text
            except sr.UnknownValueError:
                os.unlink(temp_file.name)
                return "Sorry, I couldn't understand the audio."
            except sr.RequestError as e:
                os.unlink(temp_file.name)
                return f"Could not request results; {e}"
    
    def base64_audio_to_text(self, base64_audio: str, provider: str = "openai") -> str:
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
        """Convert audio from one format to another"""
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=input_format)
            
            # Ensure proper format for speech recognition
            if output_format == "wav":
                audio = audio.set_frame_rate(16000)  # 16kHz sample rate
                audio = audio.set_channels(1)  # Mono
                audio = audio.set_sample_width(2)  # 16-bit
            
            output_buffer = io.BytesIO()
            audio.export(output_buffer, format=output_format)
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"Audio conversion error: {e}")
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
tts_service = TTSService(provider=os.getenv("TTS_PROVIDER", "gtts"))
asr_service = ASRService()
audio_processor = AudioProcessor()
