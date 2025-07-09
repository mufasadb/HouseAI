#!/usr/bin/env python3
"""
Raspberry Pi Voice Service
Continuous voice processing service with audio recording
"""

import os
import time
import threading
import queue
from pathlib import Path
from pi_voice_agent import PiVoiceAgent
import subprocess

class PiVoiceService:
    """Voice service that can record and process audio continuously"""
    
    def __init__(self):
        self.agent = PiVoiceAgent()
        self.audio_queue = queue.Queue()
        self.recordings_dir = Path("./recordings")
        self.recordings_dir.mkdir(exist_ok=True)
        
        print("🎙️ Pi Voice Service initialized")
        print(f"📁 Recordings directory: {self.recordings_dir}")
    
    def record_audio(self, duration=5, output_file="temp_recording.wav"):
        """Record audio using arecord (ALSA)"""
        try:
            cmd = [
                "arecord",
                "-f", "cd",  # CD quality
                "-t", "wav",
                "-d", str(duration),
                str(output_file)
            ]
            
            print(f"🎤 Recording for {duration} seconds...")
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ Recording saved: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Recording failed: {e}")
            return None
        except FileNotFoundError:
            print("❌ arecord not found. Install with: sudo apt install alsa-utils")
            return None
    
    def process_audio_file(self, audio_file):
        """Process a single audio file"""
        try:
            result = self.agent.process_audio(audio_file)
            
            if result["success"]:
                print(f"\n🎯 '{result['transcript']}' → {result['category']}")
                print(f"📖 Response: {result['response'][:100]}...")
                
                # Optional: Save result to file
                self.save_result(result)
                
            else:
                print(f"❌ Processing failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error processing {audio_file}: {e}")
    
    def save_result(self, result):
        """Save processing result to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        result_file = self.recordings_dir / f"result_{timestamp}.txt"
        
        with open(result_file, "w") as f:
            f.write(f"Transcript: {result['transcript']}\n")
            f.write(f"Category: {result['category']}\n")
            f.write(f"Confidence: {result['confidence']}\n")
            f.write(f"Response: {result['response']}\n")
    
    def continuous_recording_mode(self, record_duration=5, pause_duration=2):
        """Continuous voice recording and processing"""
        print(f"🔄 Starting continuous mode (record {record_duration}s, pause {pause_duration}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                # Record audio
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                audio_file = self.recordings_dir / f"recording_{timestamp}.wav"
                
                recorded_file = self.record_audio(record_duration, audio_file)
                
                if recorded_file:
                    # Process in background thread
                    thread = threading.Thread(
                        target=self.process_audio_file,
                        args=(recorded_file,)
                    )
                    thread.daemon = True
                    thread.start()
                
                # Wait before next recording
                time.sleep(pause_duration)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping continuous mode")
    
    def watch_directory_mode(self, watch_dir="./audio_input"):
        """Watch directory for new audio files"""
        watch_path = Path(watch_dir)
        watch_path.mkdir(exist_ok=True)
        
        print(f"👀 Watching directory: {watch_path}")
        print("Drop audio files here to process them")
        
        processed_files = set()
        
        try:
            while True:
                # Check for new audio files
                audio_files = list(watch_path.glob("*.wav")) + \
                            list(watch_path.glob("*.m4a")) + \
                            list(watch_path.glob("*.mp3"))
                
                for audio_file in audio_files:
                    if audio_file not in processed_files:
                        print(f"📁 New file detected: {audio_file.name}")
                        self.process_audio_file(audio_file)
                        processed_files.add(audio_file)
                
                time.sleep(1)  # Check every second
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping directory watch")

def main():
    """Main service interface"""
    import sys
    
    service = PiVoiceService()
    
    if len(sys.argv) < 2:
        print("Pi Voice Service")
        print("================")
        print("Usage:")
        print("  python pi_service.py file <audio_file>     - Process single file")
        print("  python pi_service.py record <duration>     - Record and process")
        print("  python pi_service.py continuous           - Continuous recording")
        print("  python pi_service.py watch <directory>    - Watch directory")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "file":
        if len(sys.argv) < 3:
            print("❌ Please specify audio file")
            sys.exit(1)
        audio_file = sys.argv[2]
        service.process_audio_file(audio_file)
        
    elif command == "record":
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        audio_file = service.record_audio(duration)
        if audio_file:
            service.process_audio_file(audio_file)
    
    elif command == "continuous":
        service.continuous_recording_mode()
    
    elif command == "watch":
        watch_dir = sys.argv[2] if len(sys.argv) > 2 else "./audio_input"
        service.watch_directory_mode(watch_dir)
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()