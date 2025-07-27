#!/usr/bin/env python3
"""
Test script for Fish Speech TTS integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add ai-lego-bricks to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-lego-bricks'))

from custom_tts import create_fish_speech_tts_service

def test_tts_with_routing():
    """Test TTS with a routing response"""
    print("🔊 Testing Fish Speech TTS with routing response...")
    
    # Sample routing explanation
    test_text = "I'm routing your query about machine learning to the GENERAL agent. This agent specializes in technical topics and can provide comprehensive information about AI and ML concepts."
    
    try:
        # Create TTS service
        tts_service = create_fish_speech_tts_service()
        print("✅ TTS service created")
        
        # Generate speech
        print(f"🎤 Converting to speech: '{test_text[:50]}...'")
        result = tts_service.text_to_speech(test_text)
        
        if result.success:
            print(f"✅ Audio generated successfully")
            print(f"   📁 File: {result.audio_file_path}")
            print(f"   📏 Size: {len(result.audio_data)} bytes")
            print(f"   ⏱️  Duration: {result.duration_ms}ms")
            
            # Play audio
            print("🔊 Playing audio...")
            os.system(f'afplay "{result.audio_file_path}"')
            print("✅ Audio playback completed")
            
            return result.audio_file_path
        else:
            print(f"❌ TTS generation failed: {result.error_message}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_routing_simulation():
    """Simulate the full routing workflow with TTS"""
    print("\n🤖 Simulating routing agent with TTS...")
    
    # Simulate user queries and responses
    test_cases = [
        {
            "query": "What is machine learning?",
            "routing": "GENERAL",
            "explanation": "I'm routing your query about machine learning to the GENERAL agent, which specializes in technical explanations and can provide comprehensive information about AI concepts."
        },
        {
            "query": "Turn on the bedroom light",
            "routing": "HOME_ASSISTANT", 
            "explanation": "I'm routing your smart home request to the HOME_ASSISTANT agent, which can control your lights and other connected devices."
        },
        {
            "query": "How do you say hello in Japanese?",
            "routing": "JAPANESE",
            "explanation": "I'm routing your Japanese language question to the JAPANESE agent, which specializes in language learning and translation."
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"👤 User: {case['query']}")
        print(f"🤖 Router Decision: {case['routing']}")
        print(f"💬 Explanation: {case['explanation']}")
        
        # Generate TTS for explanation
        try:
            tts_service = create_fish_speech_tts_service()
            result = tts_service.text_to_speech(case['explanation'])
            
            if result.success:
                print(f"✅ Audio generated ({result.duration_ms}ms)")
                print("🔊 Playing...")
                os.system(f'afplay "{result.audio_file_path}" &')
                input("Press Enter for next test case...")
            else:
                print(f"❌ TTS failed: {result.error_message}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Fish Speech TTS Testing Suite")
    print("=" * 50)
    
    # Test 1: Basic TTS
    audio_file = test_tts_with_routing()
    
    if audio_file:
        # Test 2: Full simulation
        test_routing_simulation()
        
        print("\n" + "=" * 50)
        print("✅ TTS testing completed!")
        print(f"🎯 Integration Status: Fish Speech TTS is working")
        print(f"📁 Last audio file: {audio_file}")
    else:
        print("\n❌ TTS testing failed - check Fish Speech server")