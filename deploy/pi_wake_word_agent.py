#!/usr/bin/env python3
"""
Raspberry Pi Wake Word Voice Agent
Continuous microphone listening with wake word detection
"""

import os
import sys
import time
import wave
import threading
import pyaudio
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile
from pi_voice_agent import PiVoiceAgent
from dotenv import load_dotenv

load_dotenv()

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    print("⚠️ Porcupine not available. Install with: pip install pvporcupine")

try:
    import openwakeword
    from openwakeword import Model
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    print("⚠️ OpenWakeWord not available. Install with: pip install openwakeword")


class WakeWordDetector:
    """Base wake word detector interface"""
    
    def __init__(self, sensitivity: float = 0.5):
        self.sensitivity = sensitivity
        self.sample_rate = 16000
        self.frame_length = 512
        
    def process_audio(self, audio_frame: bytes) -> bool:
        """Process audio frame and return True if wake word detected"""
        raise NotImplementedError


class PorcupineDetector(WakeWordDetector):
    """Porcupine wake word detector"""
    
    def __init__(self, wake_word: str = "porcupine", sensitivity: float = 0.5):
        super().__init__(sensitivity)
        
        if not PORCUPINE_AVAILABLE:
            raise ImportError("Porcupine not available")
            
        # Available keywords: porcupine, alexa, computer, hey google, etc.
        self.wake_word = wake_word.lower()
        
        try:
            # Get built-in keyword path
            keyword_paths = [pvporcupine.KEYWORD_PATHS[self.wake_word]]
            sensitivities = [sensitivity]
            
            self.porcupine = pvporcupine.create(
                keyword_paths=keyword_paths,
                sensitivities=sensitivities
            )
            
            self.sample_rate = self.porcupine.sample_rate
            self.frame_length = self.porcupine.frame_length
            
            print(f"✅ Porcupine initialized with wake word: '{wake_word}'")
            
        except Exception as e:
            raise Exception(f"Failed to initialize Porcupine: {e}")
    
    def process_audio(self, audio_frame) -> bool:
        """Process audio frame and return True if wake word detected"""
        try:
            keyword_index = self.porcupine.process(audio_frame)
            return keyword_index >= 0
        except Exception:
            return False
    
    def __del__(self):
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()


class OpenWakeWordDetector(WakeWordDetector):
    """OpenWakeWord detector"""
    
    def __init__(self, model_name: str = "alexa", sensitivity: float = 0.5):
        super().__init__(sensitivity)
        
        if not OPENWAKEWORD_AVAILABLE:
            raise ImportError("OpenWakeWord not available")
            
        try:
            self.model = Model(wakeword_models=[model_name])
            print(f"✅ OpenWakeWord initialized with model: '{model_name}'")
        except Exception as e:
            raise Exception(f"Failed to initialize OpenWakeWord: {e}")
    
    def process_audio(self, audio_frame) -> bool:
        """Process audio frame and return True if wake word detected"""
        try:
            # OpenWakeWord expects numpy array
            import numpy as np
            audio_array = np.frombuffer(audio_frame, dtype=np.int16)
            
            # Get prediction
            prediction = self.model.predict(audio_array)
            
            # Check if any wake word exceeded threshold
            for wake_word, score in prediction.items():
                if score > self.sensitivity:
                    return True
            return False
        except Exception:
            return False


class ContinuousListener:
    """Continuous microphone listener with wake word detection"""
    
    def __init__(self, wake_word_detector: WakeWordDetector, voice_agent: PiVoiceAgent):
        self.detector = wake_word_detector
        self.voice_agent = voice_agent
        self.audio = pyaudio.PyAudio()
        self.is_listening = False
        self.is_recording = False
        
        # Audio parameters
        self.chunk = self.detector.frame_length
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = self.detector.sample_rate
        
        print(f"🎤 Audio config: {self.rate}Hz, {self.chunk} samples/frame")
        
    def start_listening(self):
        """Start continuous listening for wake word"""
        if self.is_listening:
            print("⚠️ Already listening")
            return
            
        self.is_listening = True
        
        try:
            # Open microphone stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print("🎤 Listening for wake word...")
            print(f"💬 Say your wake word to activate")
            print("⏹️  Press Ctrl+C to stop")
            
            # Continuous listening loop
            while self.is_listening:
                try:
                    # Read audio frame
                    audio_frame = self.stream.read(self.chunk, exception_on_overflow=False)
                    
                    # Convert to int16 array for wake word detection
                    import struct
                    audio_data = struct.unpack(f'{self.chunk}h', audio_frame)
                    
                    # Check for wake word
                    if self.detector.process_audio(audio_data):
                        print("\n🔥 Wake word detected!")
                        self._handle_wake_word()
                        
                except Exception as e:
                    print(f"⚠️ Audio processing error: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"❌ Failed to start listening: {e}")
        finally:
            self._cleanup()
    
    def _handle_wake_word(self):
        """Handle wake word detection - record and process audio"""
        if self.is_recording:
            return
            
        self.is_recording = True
        
        try:
            print("🎙️  Recording your question... (5 seconds)")
            
            # Record audio for question
            frames = []
            duration = 5  # seconds
            total_frames = int(self.rate / self.chunk * duration)
            
            for _ in range(total_frames):
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
            
            print("🛑 Recording finished")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Write WAV file
                with wave.open(temp_path, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.audio.get_sample_size(self.format))
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(frames))
            
            # Process audio through voice agent
            print("🤖 Processing your question...")
            result = self.voice_agent.process_audio(temp_path)
            
            if result["success"]:
                print("\n" + "="*50)
                print("📝 Question:", result['transcript'])
                print("🎯 Category:", result['category'])
                print("\n📖 Response:")
                print(result['response'])
                print("="*50)
            else:
                print(f"❌ Error processing audio: {result.get('error', 'Unknown error')}")
            
            # Cleanup temp file
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"❌ Error handling wake word: {e}")
        finally:
            self.is_recording = False
            print("\n🎤 Listening for wake word...")
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        self._cleanup()
    
    def _cleanup(self):
        """Cleanup audio resources"""
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()


def create_wake_word_detector(detector_type: str = "porcupine", wake_word: str = "porcupine", sensitivity: float = 0.5) -> WakeWordDetector:
    """Factory function to create wake word detector"""
    
    if detector_type.lower() == "porcupine":
        if not PORCUPINE_AVAILABLE:
            raise ImportError("Porcupine not available. Install with: pip install pvporcupine")
        return PorcupineDetector(wake_word=wake_word, sensitivity=sensitivity)
    
    elif detector_type.lower() == "openwakeword":
        if not OPENWAKEWORD_AVAILABLE:
            raise ImportError("OpenWakeWord not available. Install with: pip install openwakeword")
        return OpenWakeWordDetector(model_name=wake_word, sensitivity=sensitivity)
    
    else:
        raise ValueError(f"Unknown detector type: {detector_type}")


def main():
    """Main function"""
    
    # Configuration from environment or defaults
    detector_type = os.getenv("WAKE_WORD_DETECTOR", "porcupine")  # porcupine or openwakeword
    wake_word = os.getenv("WAKE_WORD", "porcupine")  # porcupine, alexa, computer, hey google
    sensitivity = float(os.getenv("WAKE_WORD_SENSITIVITY", "0.5"))  # 0.0 to 1.0
    
    print("🤖 Pi Wake Word Voice Agent")
    print("="*50)
    print(f"🔧 Detector: {detector_type}")
    print(f"🗣️  Wake word: {wake_word}")
    print(f"📊 Sensitivity: {sensitivity}")
    print("="*50)
    
    try:
        # Initialize wake word detector
        print("🔧 Initializing wake word detector...")
        detector = create_wake_word_detector(detector_type, wake_word, sensitivity)
        
        # Initialize voice agent
        print("🤖 Initializing voice agent...")
        voice_agent = PiVoiceAgent()
        
        # Create continuous listener
        listener = ContinuousListener(detector, voice_agent)
        
        # Start listening
        listener.start_listening()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()