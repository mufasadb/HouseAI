#!/usr/bin/env python3
"""
Raspberry Pi Voice Orchestration Agent
Lightweight version optimized for Pi 4 deployment
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QuestionClassification(BaseModel):
    category: str
    confidence: float
    reasoning: str

class PiVoiceAgent:
    """Lightweight voice orchestration agent for Raspberry Pi"""
    
    def __init__(self):
        # Configuration from environment
        self.ollama_url = os.getenv("OLLAMA_URL", "http://100.83.40.11:11434")
        self.stt_url = os.getenv("FASTER_WHISPER_URL", "http://100.83.40.11:8003")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        print(f"🤖 Pi Voice Agent initializing...")
        print(f"🎤 STT Service: {self.stt_url}")
        print(f"🧠 LLM Service: {self.ollama_url}")
        
        # Test connections
        self._test_connections()
        
    def _test_connections(self):
        """Test connections to remote services"""
        # Test STT service
        try:
            response = requests.get(f"{self.stt_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ STT service connected")
            else:
                print("⚠️ STT service not responding")
        except Exception as e:
            print(f"❌ STT service error: {e}")
            
        # Test Ollama service
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama service connected")
            else:
                print("⚠️ Ollama service not responding")
        except Exception as e:
            print(f"❌ Ollama service error: {e}")
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio using remote STT service"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                files = {"file": audio_file}
                response = requests.post(
                    f"{self.stt_url}/transcribe",
                    files=files,
                    timeout=60
                )
                
            if response.status_code == 200:
                result = response.json()
                return result.get("transcription", "")
            else:
                raise Exception(f"STT failed: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Transcription failed: {e}")
    
    def classify_question(self, text: str) -> Dict[str, Any]:
        """Classify question using remote Ollama"""
        prompt = f"""You are a question classifier. Classify this question into one of these categories:
- 'japanese': Japanese language, culture, anime, manga, travel, food, customs
- 'home_assistant': Smart home, IoT, lights, thermostats, Home Assistant
- 'general': Everything else (science, programming, general knowledge)

Question: {text}

Respond with JSON containing: category, confidence (0-1), reasoning

JSON:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # Parse the JSON response from Ollama
                import json
                classification = json.loads(result["response"])
                return classification
            else:
                # Fallback classification
                return {
                    "category": "general",
                    "confidence": 0.5,
                    "reasoning": "Classification service unavailable"
                }
                
        except Exception as e:
            print(f"⚠️ Classification error: {e}")
            return {
                "category": "general", 
                "confidence": 0.5,
                "reasoning": "Classification failed"
            }
    
    def get_response(self, text: str, category: str) -> str:
        """Get response from appropriate handler using remote Ollama"""
        
        # Build system prompt based on category
        if category == "japanese":
            system_prompt = """You are a helpful Japanese language assistant. When users ask Japanese questions, respond with very simple Japanese and include English explanations. Keep responses basic and educational."""
        elif category == "home_assistant":
            system_prompt = """You are a Home Assistant expert. You can help with smart home automation, controlling lights, thermostats, and other IoT devices. Provide practical advice for home automation."""
        else:  # general
            system_prompt = """You are a knowledgeable general assistant with expertise across many domains including programming, science, mathematics, technology, history, and more. Provide accurate, well-reasoned responses."""
        
        prompt = f"System: {system_prompt}\n\nUser: {text}\n\nAssistant:"
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["response"].strip()
            else:
                return f"Sorry, I couldn't process your {category} question right now."
                
        except Exception as e:
            return f"Error generating response: {e}"
    
    def process_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """Complete audio-to-response pipeline"""
        try:
            print(f"🎵 Processing: {audio_file_path}")
            
            # Step 1: Transcribe
            print("🎤 Transcribing...")
            transcript = self.transcribe_audio(audio_file_path)
            print(f"📝 Transcribed: {transcript}")
            
            # Step 2: Classify
            print("🔍 Classifying...")
            classification = self.classify_question(transcript)
            category = classification["category"]
            confidence = classification["confidence"]
            reasoning = classification["reasoning"]
            
            print(f"🎯 Category: {category} ({confidence:.2f} confidence)")
            print(f"💭 Reasoning: {reasoning}")
            
            # Step 3: Generate response
            print(f"💬 Generating {category} response...")
            response = self.get_response(transcript, category)
            
            return {
                "success": True,
                "transcript": transcript,
                "category": category,
                "confidence": confidence,
                "reasoning": reasoning,
                "response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file": audio_file_path
            }

def main():
    """Main CLI interface"""
    if len(sys.argv) != 2:
        print("Usage: python pi_voice_agent.py <audio_file>")
        print("Example: python pi_voice_agent.py recording.m4a")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        sys.exit(1)
    
    # Initialize agent
    agent = PiVoiceAgent()
    
    # Process audio
    result = agent.process_audio(audio_file)
    
    if result["success"]:
        print("\n" + "="*50)
        print("📋 RESULT")
        print("="*50)
        print(f"📝 Transcript: {result['transcript']}")
        print(f"🎯 Category: {result['category']}")
        print(f"📊 Confidence: {result['confidence']:.2f}")
        print(f"💭 Reasoning: {result['reasoning']}")
        print(f"\n📖 Response:\n{result['response']}")
        print("="*50)
        print("✅ Processing complete!")
    else:
        print(f"❌ Error: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()