import whisper
import torch
from gtts import gTTS
import io
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from threading import Lock

class VoiceHandler:
    """Handles speech-to-text and text-to-speech operations"""
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Whisper model for speech recognition"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model on {self.device}...")
        self.whisper_model = whisper.load_model("base", device=self.device)
        print("Whisper model loaded successfully")
    
    def transcribe_audio(self, audio_path: str) -> Tuple[str, Optional[str]]:
        """Transcribe audio file to text using Whisper"""
        try:
            result = self.whisper_model.transcribe(
                audio_path,
                language="en",
                fp16=(self.device == "cuda")
            )
            return result["text"].strip(), None
        except Exception as e:
            error_msg = f"Transcription error: {str(e)}"
            print(error_msg)
            return "", error_msg
    
    def text_to_speech(self, text: str, lang: str = "en") -> Tuple[Optional[bytes], Optional[str]]:
        """Convert text to speech using gTTS"""
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer.read(), None
        except Exception as e:
            error_msg = f"TTS error: {str(e)}"
            print(error_msg)
            return None, error_msg

# Singleton instance
voice_handler = VoiceHandler()