"""
Custom TTS client for Fish Speech S1
Wraps around ai-lego-bricks TTS framework to add Fish Speech support
"""

import os
import requests
import tempfile
import time
from typing import Optional, Dict, Any
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-lego-bricks'))
from tts.tts_types import TTSClient, TTSConfig, TTSResponse, AudioFormat


class FishSpeechTTSClient(TTSClient):
    """
    Client for Fish Speech S1 local instance
    """
    
    def __init__(self, config: TTSConfig, credential_manager: Optional = None):
        super().__init__(config)
        self.server_url = os.getenv("FISH_SPEECH_URL", "http://100.83.40.11:8080")
        self.timeout = 60
        self.streaming = True
        self._voices_cache = None
        # Default to trained Sonnet 29 voice
        self.trained_voice = "sonnet29"
    
    def text_to_speech(self, text: str, **kwargs) -> TTSResponse:
        """Convert text to speech using Fish Speech S1"""
        
        # Merge config with kwargs - always use trained Sonnet 29 voice
        voice = kwargs.get("voice", self.config.voice or self.trained_voice)
        output_path = kwargs.get("output_path", self.config.output_path)
        
        # Fish Speech parameters with trained voice reference
        request_data = {
            "text": text,
            "reference_audio": "/Users/danielbeach/Code/agent_apps/HouseAI/experimental/fish_speech_tests/sonnet29_reference_optimized.wav",
            "speaker": self.trained_voice
        }
        
        try:
            start_time = time.time()
            
            # Make request to Fish Speech server
            response = requests.post(
                f"{self.server_url}/v1/tts",
                json=request_data,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return TTSResponse(
                    success=False,
                    error_message=f"Fish Speech server error: {response.status_code} - {response.text}",
                    provider="fish_speech",
                    format_used=self.config.output_format.value
                )
            
            # Get audio data
            audio_data = response.content
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Save to file if output_path specified
            file_path = None
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                file_path = os.path.abspath(output_path)
            else:
                # Create temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=f".{self.config.output_format.value}",
                    delete=False
                ) as f:
                    f.write(audio_data)
                    file_path = f.name
            
            return TTSResponse(
                success=True,
                audio_file_path=file_path,
                audio_data=audio_data,
                duration_ms=duration_ms,
                provider="fish_speech",
                voice_used=voice,
                format_used=self.config.output_format.value,
                metadata={
                    "server_url": self.server_url,
                    "streaming": self.streaming,
                    "text_length": len(text)
                }
            )
            
        except requests.exceptions.RequestException as e:
            return TTSResponse(
                success=False,
                error_message=f"Connection to Fish Speech server failed: {str(e)}",
                provider="fish_speech",
                format_used=self.config.output_format.value
            )
        except Exception as e:
            return TTSResponse(
                success=False,
                error_message=f"Fish Speech error: {str(e)}",
                provider="fish_speech",
                format_used=self.config.output_format.value
            )
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get available voices from Fish Speech server"""
        if self._voices_cache is None:
            try:
                response = requests.get(
                    f"{self.server_url}/voices",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    self._voices_cache = response.json()
                else:
                    self._voices_cache = {"default": {"name": "default", "description": "Default Fish Speech voice"}}
            except Exception:
                self._voices_cache = {"default": {"name": "default", "description": "Default Fish Speech voice"}}
        
        return self._voices_cache
    
    def is_available(self) -> bool:
        """Check if Fish Speech server is available"""
        try:
            response = requests.get(
                f"{self.server_url}/",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            try:
                response = requests.get(
                    f"{self.server_url}/json",
                    timeout=5
                )
                return response.status_code == 200
            except Exception:
                return False


def create_fish_speech_tts_service(**kwargs):
    """Create Fish Speech TTS service"""
    from tts.tts_types import TTSConfig, AudioFormat
    from tts.tts_service import TTSService
    
    config = TTSConfig(
        provider="fish_speech",
        voice=kwargs.get("voice", "sonnet29"),
        speed=kwargs.get("speed", 1.0),
        output_format=AudioFormat(kwargs.get("output_format", "wav")),
        extra_params=kwargs.get("extra_params", {})
    )
    
    client = FishSpeechTTSClient(config)
    return TTSService(client)