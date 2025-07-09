#!/usr/bin/env python3
"""
Simple audio processing script that takes a filename parameter
and processes it through the voice orchestration workflow
"""

import sys
import os
from pathlib import Path
from voice_orchestration_agent import VoiceOrchestrationAgent

def process_audio_file(audio_file_path: str):
    """Process an audio file through the voice orchestration workflow"""
    # Validate input
    if not audio_file_path:
        print("❌ Error: No audio file path provided")
        print("Usage: python process_audio.py <audio_file_path>")
        return False
    
    # Check if file exists
    if not os.path.exists(audio_file_path):
        print(f"❌ Error: Audio file not found: {audio_file_path}")
        return False
    
    # Initialize agent
    try:
        print("🤖 Initializing voice orchestration agent...")
        agent = VoiceOrchestrationAgent()
        print("✅ Agent ready!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False
    
    # Process the audio file
    try:
        print(f"🎵 Processing audio file: {audio_file_path}")
        print("-" * 50)
        
        result = agent.process_audio_file(audio_file_path)
        output = agent.format_output(result)
        
        print(output)
        
        return result["success"] if "success" in result else False
        
    except Exception as e:
        print(f"❌ Error processing audio: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function that handles command line arguments"""
    if len(sys.argv) != 2:
        print("Voice Orchestration Agent - Audio Processor")
        print("=" * 50)
        print("Usage: python process_audio.py <audio_file_path>")
        print()
        print("Example:")
        print("  python process_audio.py my_question.wav")
        print("  python process_audio.py /path/to/audio.mp3")
        print()
        print("Supported audio formats: WAV, MP3, M4A, FLAC, OGG")
        sys.exit(1)
    
    audio_file_path = sys.argv[1]
    success = process_audio_file(audio_file_path)
    
    if success:
        print("\n✅ Audio processing completed successfully!")
    else:
        print("\n❌ Audio processing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()