"""
Audio Service - Handles audio processing and transcription
"""
import io
import base64
from typing import Optional, Tuple
from services.openai_service import openai_service


class AudioService:
    """Service class for audio processing"""
    
    SUPPORTED_FORMATS = ['webm', 'wav', 'mp3', 'ogg', 'm4a', 'flac']
    
    async def transcribe_audio(
        self,
        audio_data: str,
        audio_format: str = "webm",
        prompt: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Transcribe audio from base64 encoded data
        
        Returns:
            Tuple of (success, text, error)
        """
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Transcribe using OpenAI
            result = await openai_service.transcribe_audio(
                audio_bytes,
                prompt=prompt
            )
            
            return result["success"], result["text"], result.get("error")
            
        except Exception as e:
            return False, "", str(e)
    
    def validate_audio_format(self, audio_format: str) -> bool:
        """Check if audio format is supported"""
        return audio_format.lower() in self.SUPPORTED_FORMATS
    
    def convert_to_wav(self, audio_data: bytes, input_format: str) -> Optional[bytes]:
        """
        Convert audio to WAV format for better compatibility
        Note: Requires pydub and ffmpeg
        """
        try:
            from pydub import AudioSegment
            
            audio_file = io.BytesIO(audio_data)
            audio = AudioSegment.from_file(audio_file, format=input_format)
            
            # Convert to mono, 16kHz for Whisper
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            output = io.BytesIO()
            audio.export(output, format="wav")
            return output.getvalue()
            
        except Exception as e:
            print(f"Audio conversion error: {e}")
            return None
    
    def get_audio_duration(self, audio_data: bytes, audio_format: str) -> Optional[float]:
        """Get duration of audio in seconds"""
        try:
            from pydub import AudioSegment
            
            audio_file = io.BytesIO(audio_data)
            audio = AudioSegment.from_file(audio_file, format=audio_format)
            return len(audio) / 1000.0  # Convert to seconds
            
        except Exception as e:
            print(f"Duration calculation error: {e}")
            return None


# Create singleton instance
audio_service = AudioService()





