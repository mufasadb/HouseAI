#!/usr/bin/env python3
"""
Direct test of streaming functionality
"""
import sys
import os
sys.path.append('ai-lego-bricks')

def test_ollama_direct():
    """Test Ollama directly with current implementation"""
    try:
        from llm.text_clients import OllamaTextClient
        from llm.llm_types import LLMConfig
        from credentials import CredentialManager

        # Setup credential manager with our environment
        os.environ['OLLAMA_URL'] = 'http://100.83.40.11:11434'
        os.environ['OLLAMA_DEFAULT_MODEL'] = 'gemma3:4b'
        
        config = LLMConfig(
            provider="ollama",
            model="gemma3:4b",
            temperature=0.7,
            max_tokens=50
        )
        
        client = OllamaTextClient(config)
        
        print("=== Testing Ollama Text Client ===")
        print(f"Base URL: {client.base_url}")
        print(f"Model: {client.model}")
        
        # Test regular chat
        print("\n1. Testing regular chat:")
        try:
            response = client.chat("What is 2+2?")
            print(f"✅ Regular chat: {response[:100]}...")
        except Exception as e:
            print(f"❌ Regular chat failed: {e}")
            return False
        
        # Test streaming
        print("\n2. Testing streaming:")
        try:
            full_response = ""
            chunk_count = 0
            for chunk in client.chat_stream("Tell me a very short joke"):
                chunk_count += 1
                full_response += chunk
                print(f"   Chunk {chunk_count}: '{chunk}'")
                if chunk_count >= 10:  # Limit output
                    print("   ... (truncated)")
                    break
            
            print(f"✅ Streaming worked! Got {chunk_count} chunks")
            print(f"   Full response: {full_response[:100]}...")
            
            # Check if it's real streaming or simulated
            if "Simulate streaming" in str(client.chat_with_messages_stream.__doc__):
                print("⚠️  Note: This is simulated streaming")
            else:
                print("🚀 This appears to be real streaming")
                
            return True
            
        except Exception as e:
            print(f"❌ Streaming failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing streaming with updated ai-lego-bricks")
    result = test_ollama_direct()
    
    print("\n" + "="*60)
    if result:
        print("🎉 SUCCESS: Streaming functionality is working!")
    else:
        print("💥 FAILED: Streaming needs investigation")