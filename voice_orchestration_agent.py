#!/usr/bin/env python3
"""
Voice Orchestration Agent - Complete voice-to-response system
Handles audio transcription, question classification, and routing to specialized handlers
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# Add the ai-lego-bricks directory to the path
ai_lego_path = Path(__file__).parent / "ai-lego-bricks"
sys.path.insert(0, str(ai_lego_path))

# Set environment variables for Ollama
os.environ['OLLAMA_URL'] = 'http://100.83.40.11:11434'
os.environ['OLLAMA_DEFAULT_MODEL'] = 'qwen2.5:7b'

from agent_orchestration.orchestrator import AgentOrchestrator
from agent_orchestration.models import WorkflowConfig
from credentials import CredentialManager
from stt.stt_factory import create_stt_service
from llm.llm_factory import create_text_client, create_structured_client
from pydantic import BaseModel
import openai
import requests

class QuestionClassification(BaseModel):
    category: str
    confidence: float
    reasoning: str

class VoiceOrchestrationAgent:
    """Voice orchestration agent that handles audio-to-response workflow"""
    
    def __init__(self):
        # Load .env explicitly first
        from dotenv import load_dotenv
        load_dotenv()
        
        # Create credential manager
        self.creds = CredentialManager({
            "OLLAMA_URL": "http://100.83.40.11:11434"
        }, load_env=True)
        
        # Initialize STT service - use direct API call to Faster Whisper at 100.83.40.11:8003
        self.faster_whisper_url = "http://100.83.40.11:8003"
        self.use_faster_whisper = False
        self.use_openai_whisper = False
        
        # Test Faster Whisper service
        try:
            print(f"🎤 Testing Faster Whisper at {self.faster_whisper_url}")
            response = requests.get(f"{self.faster_whisper_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Faster Whisper STT service ready!")
                self.use_faster_whisper = True
            else:
                raise Exception(f"Health check failed with status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Faster Whisper STT service not available: {e}")
            print("   Trying OpenAI Whisper fallback...")
            
            # Fallback to OpenAI if available
            openai_api_key = self.creds.get_credential("OPENAI_API_KEY")
            if openai_api_key:
                print("✅ Using OpenAI Whisper for transcription")
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                self.use_openai_whisper = True
            else:
                print("❌ No STT service available")
        
        # Use the currently running model
        current_model = "qwen2.5:7b"
        
        # Create classifier (using current model)
        self.classifier = create_structured_client(
            "ollama",
            QuestionClassification,
            model=current_model,
            temperature=0.1,
            credential_manager=self.creds
        )
        
        # Create specialized handlers
        self.japanese_handler = create_text_client(
            "ollama",
            model=current_model,
            temperature=0.7,
            credential_manager=self.creds
        )
        
        self.home_assistant_handler = create_text_client(
            "ollama",
            model=current_model,
            temperature=0.3,
            credential_manager=self.creds
        )
        
        self.general_handler = create_text_client(
            "ollama",
            model=current_model,
            temperature=0.7,
            credential_manager=self.creds
        )
        
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file to text"""
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        print(f"🎤 Transcribing audio: {audio_file_path}")
        
        if self.use_faster_whisper:
            # Use direct API call to Faster Whisper service
            try:
                with open(audio_file_path, "rb") as audio_file:
                    files = {"file": audio_file}
                    response = requests.post(
                        f"{self.faster_whisper_url}/transcribe",
                        files=files,
                        timeout=60
                    )
                    
                if response.status_code == 200:
                    result = response.json()
                    # STT service returns "transcription" field, not "text"
                    transcript = result.get("transcription", result.get("text", ""))
                    return transcript
                else:
                    raise Exception(f"Transcription failed with status {response.status_code}: {response.text}")
                    
            except Exception as e:
                raise Exception(f"Faster Whisper transcription failed: {e}")
        
        elif self.use_openai_whisper:
            # Use OpenAI Whisper API
            try:
                with open(audio_file_path, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return transcript.text
            except Exception as e:
                raise Exception(f"OpenAI Whisper transcription failed: {e}")
        
        else:
            raise Exception("STT service not available. Please configure an STT provider.")
    
    def classify_question(self, transcribed_text: str) -> QuestionClassification:
        """Classify the transcribed question using Llama 2.5"""
        classification_prompt = f"""You are a question classifier that determines which specialized handler should process a user's question. 

Classify questions into these categories:
- 'japanese': Japanese language questions, culture, anime, manga, travel to Japan, Japanese food, customs, traditions. For basic Japanese questions, provide simple responses.
- 'home_assistant': Smart home automation, IoT devices, home security, lighting, thermostats, appliances, Home Assistant platform questions.
- 'general': Everything else including science, programming, general knowledge, math, history, etc.

Provide a confidence score (0.0 to 1.0) and brief reasoning for your classification.

Question: {transcribed_text}

Respond with JSON containing category, confidence, and reasoning."""
        
        return self.classifier.chat(classification_prompt)
    
    def handle_japanese_question(self, transcribed_text: str, classification: QuestionClassification) -> str:
        """Handle Japanese language questions with simple responses"""
        prompt = f"""You are a helpful Japanese language assistant. When users ask Japanese questions, respond with very simple Japanese and include English explanations. Keep responses basic and educational. For cultural questions, provide respectful and accurate information about Japanese culture, customs, and traditions. Always be patient and encouraging with language learners.

Original question: {transcribed_text}

Classification confidence: {classification.confidence}
Reasoning: {classification.reasoning}

Please provide a helpful response in simple Japanese with English explanations where appropriate."""
        
        return self.japanese_handler.chat(prompt)
    
    def handle_home_assistant_question(self, transcribed_text: str, classification: QuestionClassification) -> str:
        """Handle Home Assistant and smart home questions with actual integration"""
        prompt = f"""You are a Home Assistant expert that can actually interact with smart home devices. You have access to tools to control lights, check device status, and manage home automation. When users ask about home control, provide practical advice and actually execute commands when appropriate. Focus on being helpful and actionable.

Original question: {transcribed_text}

Classification confidence: {classification.confidence}
Reasoning: {classification.reasoning}

Please provide a helpful response and take any necessary actions to control Home Assistant devices."""
        
        return self.home_assistant_handler.chat(prompt)
    
    def handle_general_question(self, transcribed_text: str, classification: QuestionClassification) -> str:
        """Handle general questions using Gemini Flash 1.5"""
        prompt = f"""You are a knowledgeable general assistant with expertise across many domains including programming, science, mathematics, technology, history, geography, arts, literature, and philosophy. Provide accurate, well-reasoned responses with clear explanations. When appropriate, include examples, step-by-step guidance, or references to help users understand complex topics.

Original question: {transcribed_text}

Classification confidence: {classification.confidence}
Reasoning: {classification.reasoning}

Please provide a comprehensive and helpful response."""
        
        return self.general_handler.chat(prompt)
    
    def process_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Process an audio file through the complete workflow"""
        try:
            # Step 1: Transcribe audio
            transcribed_text = self.transcribe_audio(audio_file_path)
            print(f"🎤 Transcribed: {transcribed_text}")
            
            # Step 2: Classify question
            print("🔍 Classifying question...")
            classification = self.classify_question(transcribed_text)
            print(f"🤖 Handler: {classification.category}")
            print(f"📊 Confidence: {classification.confidence:.2f}")
            print(f"💭 Reasoning: {classification.reasoning}")
            
            # Step 3: Route to appropriate handler
            print(f"💬 Processing with {classification.category} handler...")
            
            if classification.category == "japanese":
                response = self.handle_japanese_question(transcribed_text, classification)
            elif classification.category == "home_assistant":
                response = self.handle_home_assistant_question(transcribed_text, classification)
            else:  # general
                response = self.handle_general_question(transcribed_text, classification)
            
            return {
                "success": True,
                "transcribed_text": transcribed_text,
                "classification": classification,
                "response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "audio_file": audio_file_path
            }
    
    def format_output(self, result: Dict[str, Any]) -> str:
        """Format the final output"""
        if not result["success"]:
            return f"❌ Error processing audio: {result['error']}"
        
        classification = result["classification"]
        return f"""🎤 Transcribed: {result['transcribed_text']}

🤖 Handler: {classification.category}
📊 Confidence: {classification.confidence:.2f}
💭 Reasoning: {classification.reasoning}

📝 Response:
{result['response']}"""

def demo_voice_agent():
    """Demo the voice orchestration agent"""
    print("🎤 Voice Orchestration Agent Demo")
    print("=" * 60)
    
    # Initialize agent
    try:
        agent = VoiceOrchestrationAgent()
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Test with example audio files (you'll need to provide actual audio files)
    test_files = [
        # Add paths to your test audio files here
        # "test_audio/japanese_question.wav",
        # "test_audio/home_assistant_question.wav", 
        # "test_audio/general_question.wav"
    ]
    
    if not test_files:
        print("⚠️ No test audio files provided. Please add audio file paths to test_files list.")
        return
    
    for i, audio_file in enumerate(test_files, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Test {i}/{len(test_files)}: {audio_file}")
        print("="*60)
        
        if not os.path.exists(audio_file):
            print(f"❌ Audio file not found: {audio_file}")
            continue
        
        try:
            result = agent.process_audio_file(audio_file)
            output = agent.format_output(result)
            print(output)
            
        except Exception as e:
            print(f"❌ Error processing audio: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("✅ Demo completed!")

def interactive_mode():
    """Interactive mode for testing with custom audio files"""
    print("🎤 Interactive Voice Orchestration Agent")
    print("Enter audio file paths to process (type 'quit' to exit)")
    print("=" * 60)
    
    try:
        agent = VoiceOrchestrationAgent()
        print("✅ Agent ready!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    while True:
        try:
            audio_file = input("\n🎧 Audio file path: ").strip()
            
            if audio_file.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not audio_file:
                continue
            
            result = agent.process_audio_file(audio_file)
            output = agent.format_output(result)
            print(f"\n{output}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            interactive_mode()
        else:
            # Process single audio file
            audio_file = sys.argv[1]
            if os.path.exists(audio_file):
                agent = VoiceOrchestrationAgent()
                result = agent.process_audio_file(audio_file)
                output = agent.format_output(result)
                print(output)
            else:
                print(f"❌ Audio file not found: {audio_file}")
    else:
        demo_voice_agent()