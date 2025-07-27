"""
Simple test to verify streaming functionality works with current ai-lego-bricks
"""
import sys
import os
sys.path.append('ai-lego-bricks')
from ai_lego_bricks.llm.text_clients import OllamaTextClient, GeminiTextClient
from ai_lego_bricks.llm.llm_types import LLMConfig

def test_ollama_streaming():
    """Test Ollama streaming functionality"""
    try:
        
        # Create client with basic config
        config = LLMConfig(
            model="llama3.2:1b",  # Small model for testing
            temperature=0.7,
            max_tokens=100
        )
        
        client = OllamaTextClient(config)
        
        print("Testing Ollama streaming...")
        print("=" * 50)
        
        # Test regular chat first
        try:
            response = client.chat("Say hello in exactly 3 words")
            print(f"Regular chat works: {response}")
        except Exception as e:
            print(f"Regular chat failed: {e}")
            return False
        
        # Test streaming
        try:
            print("\nTesting streaming:")
            chunks = []
            for chunk in client.chat_stream("Tell me a very short joke"):
                print(f"Chunk: '{chunk}'")
                chunks.append(chunk)
            
            print(f"\nStreaming works! Got {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"Streaming failed: {e}")
            return False
            
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

def test_gemini_streaming():
    """Test Gemini streaming functionality"""
    try:
        
        config = LLMConfig(
            model="gemini-1.5-flash",
            temperature=0.7,
            max_tokens=50
        )
        
        client = GeminiTextClient(config)
        
        print("\nTesting Gemini streaming...")
        print("=" * 50)
        
        # Test streaming
        try:
            print("Testing streaming:")
            chunks = []
            for chunk in client.chat_stream("Say hello"):
                print(f"Chunk: '{chunk}'")
                chunks.append(chunk)
            
            print(f"\nGemini streaming works! Got {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"Gemini streaming failed: {e}")
            return False
            
    except ImportError as e:
        print(f"Gemini import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing streaming functionality with updated ai-lego-bricks")
    
    # Test Ollama first (if available)
    ollama_result = test_ollama_streaming()
    
    # Test Gemini (if credentials available)
    gemini_result = test_gemini_streaming()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Ollama streaming: {'✅ PASS' if ollama_result else '❌ FAIL'}")
    print(f"Gemini streaming: {'✅ PASS' if gemini_result else '❌ FAIL'}")