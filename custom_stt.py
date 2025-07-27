"""
Custom STT client for Custom Transcription service
Wraps around ai-lego-bricks STT framework to add custom transcription support
"""

import os
import requests
import time
from typing import Optional, List
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-lego-bricks'))
from stt.stt_types import STTClient, STTConfig, STTResponse, WordTimestamp


class CustomTranscriptionSTTClient(STTClient):
    """
    Client for Custom Transcription service
    """
    
    def __init__(self, config: STTConfig, credential_manager: Optional = None):
        super().__init__(config)
        self.server_url = os.getenv("CUSTOM_TRANSCRIPTION_URL", "http://100.83.40.11:8002")
        self.timeout = 120
        self._languages_cache = None
    
    def speech_to_text(self, audio_file_path: str, **kwargs) -> STTResponse:
        """Convert speech to text using Custom Transcription service"""
        
        # Merge config with kwargs
        language = kwargs.get("language", self.config.language or "auto")
        model = kwargs.get("model", self.config.model or "whisper")
        enable_word_timestamps = kwargs.get("enable_word_timestamps", self.config.enable_word_timestamps)
        temperature = kwargs.get("temperature", self.config.temperature)
        
        if not os.path.isfile(audio_file_path):
            return STTResponse(
                success=False,
                error_message=f"Audio file not found: {audio_file_path}",
                provider="custom_transcription"
            )
        
        try:
            start_time = time.time()
            
            # Prepare the request
            with open(audio_file_path, 'rb') as audio_file:
                files = {'file': audio_file}
                data = {
                    'language': language,
                    'model': model,
                    'temperature': temperature,
                    'response_format': 'json',
                    'timestamp_granularities[]': 'word' if enable_word_timestamps else 'segment'
                }
                
                # Make request to Custom Transcription server
                response = requests.post(
                    f"{self.server_url}/v1/audio/transcriptions",
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
            
            if response.status_code != 200:
                return STTResponse(
                    success=False,
                    error_message=f"Custom Transcription server error: {response.status_code} - {response.text}",
                    provider="custom_transcription"
                )
            
            result = response.json()
            duration_seconds = time.time() - start_time
            
            # Parse word timestamps if available
            word_timestamps = []
            if enable_word_timestamps and 'words' in result:
                for word_info in result.get('words', []):
                    word_timestamps.append(WordTimestamp(
                        word=word_info['word'],
                        start_time=word_info['start'],
                        end_time=word_info['end'],
                        confidence=word_info.get('confidence')
                    ))
            
            return STTResponse(
                success=True,
                transcript=result.get('text', ''),
                language_detected=result.get('language'),
                confidence=result.get('confidence'),
                word_timestamps=word_timestamps,
                duration_seconds=duration_seconds,
                provider="custom_transcription",
                model_used=model,
                metadata={
                    'server_url': self.server_url,
                    'response_format': 'json',
                    'processing_time': duration_seconds
                }
            )
            
        except requests.exceptions.RequestException as e:
            return STTResponse(
                success=False,
                error_message=f"Connection to Custom Transcription server failed: {str(e)}",
                provider="custom_transcription"
            )
        except Exception as e:
            return STTResponse(
                success=False,
                error_message=f"Custom Transcription error: {str(e)}",
                provider="custom_transcription"
            )
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages for Custom Transcription"""
        if self._languages_cache is None:
            try:
                response = requests.get(
                    f"{self.server_url}/languages",
                    timeout=5
                )
                
                if response.status_code == 200:
                    self._languages_cache = response.json()
                else:
                    # Fallback to common languages
                    self._languages_cache = [
                        'auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 
                        'zh', 'ar', 'hi', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi'
                    ]
            except Exception:
                self._languages_cache = [
                    'auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 
                    'zh', 'ar', 'hi', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi'
                ]
        
        return self._languages_cache
    
    def is_available(self) -> bool:
        """Check if Custom Transcription server is available"""
        try:
            response = requests.get(
                f"{self.server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            try:
                response = requests.get(
                    f"{self.server_url}/",
                    timeout=5
                )
                return response.status_code == 200
            except Exception:
                return False


def create_custom_transcription_stt_service(**kwargs):
    """Create Custom Transcription STT service"""
    from stt.stt_types import STTConfig
    from stt.stt_service import STTService
    
    config = STTConfig(
        provider="custom_transcription",
        language=kwargs.get("language", "auto"),
        model=kwargs.get("model", "whisper"),
        enable_word_timestamps=kwargs.get("enable_word_timestamps", False),
        enable_speaker_diarization=kwargs.get("enable_speaker_diarization", False),
        temperature=kwargs.get("temperature", 0.0),
        beam_size=kwargs.get("beam_size", 5),
        extra_params=kwargs.get("extra_params", {})
    )
    
    client = CustomTranscriptionSTTClient(config)
    return STTService(client)