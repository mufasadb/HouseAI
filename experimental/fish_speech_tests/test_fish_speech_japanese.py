"""
Test Fish Speech TTS with Japanese content
Using the trained Sonnet 29 voice to speak Japanese
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path

# Add ai-lego-bricks to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-lego-bricks'))

from custom_tts import create_fish_speech_tts_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_fish_speech_japanese():
    """
    Test Fish Speech TTS with Japanese content
    """
    
    # Japanese test content - basic greetings and phrases
    japanese_tests = [
        {
            "text": "こんにちは、元気ですか？",
            "romaji": "Konnichiwa, genki desu ka?",
            "english": "Hello, how are you?",
            "filename": "japanese_greeting.wav"
        },
        {
            "text": "今日は美しい日ですね。",
            "romaji": "Kyou wa utsukushii hi desu ne.",
            "english": "Today is a beautiful day, isn't it?",
            "filename": "japanese_weather.wav"
        },
        {
            "text": "私の名前は田中です。よろしくお願いします。",
            "romaji": "Watashi no namae wa Tanaka desu. Yoroshiku onegaishimasu.",
            "english": "My name is Tanaka. Nice to meet you.",
            "filename": "japanese_introduction.wav"
        },
        {
            "text": "ありがとうございます。",
            "romaji": "Arigatou gozaimasu.",
            "english": "Thank you very much.",
            "filename": "japanese_thanks.wav"
        }
    ]
    
    logger.info("🎌 Testing Fish Speech TTS with Japanese content...")
    logger.info("Using trained Sonnet 29 voice for Japanese speech synthesis")
    
    # Test direct API call first
    fish_speech_url = "http://100.83.40.11:8080"
    
    results = []
    
    for i, test in enumerate(japanese_tests, 1):
        logger.info(f"\n--- Test {i}/4 ---")
        logger.info(f"Japanese: {test['text']}")
        logger.info(f"Romaji: {test['romaji']}")
        logger.info(f"English: {test['english']}")
        
        try:
            # Test direct API call
            result = test_direct_api_call(fish_speech_url, test)
            results.append(result)
            
        except Exception as e:
            logger.error(f"❌ Test {i} failed: {e}")
            results.append({
                "test_number": i,
                "text": test['text'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("🎯 TEST SUMMARY")
    logger.info("="*50)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    logger.info(f"✅ Successful: {len(successful)}/{len(results)}")
    logger.info(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        logger.info("\n🎵 Generated Audio Files:")
        for result in successful:
            if 'filename' in result:
                logger.info(f"   • {result['filename']} ({result.get('duration', 'N/A')}s)")
    
    if failed:
        logger.info("\n💥 Errors encountered:")
        for result in failed:
            logger.info(f"   • Test {result['test_number']}: {result['error']}")
    
    return results


def test_direct_api_call(server_url: str, test_data: dict) -> dict:
    """
    Test direct API call to Fish Speech server
    """
    
    request_data = {
        "text": test_data["text"],
        "format": "wav",
        "normalize": True,
        "streaming": False,
        "chunk_length": 200,
        "max_new_tokens": 1024,
        "top_p": 0.8,
        "repetition_penalty": 1.1,
        "temperature": 0.8
    }
    
    logger.info(f"🔄 Making TTS request...")
    
    try:
        response = requests.post(
            f"{server_url}/v1/tts",
            json=request_data,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # Save audio file
            output_path = test_data["filename"]
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # Get file size for rough duration estimate
            file_size = len(response.content)
            estimated_duration = file_size / 44100 / 2  # Rough estimate for WAV
            
            logger.info(f"✅ Success! Audio saved to: {output_path}")
            logger.info(f"📊 File size: {file_size:,} bytes")
            logger.info(f"⏱️  Estimated duration: {estimated_duration:.2f}s")
            
            return {
                "test_number": test_data.get("test_number", 0),
                "text": test_data["text"],
                "romaji": test_data["romaji"],
                "filename": output_path,
                "success": True,
                "file_size": file_size,
                "duration": estimated_duration
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"❌ API call failed: {error_msg}")
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection error: {str(e)}"
        logger.error(f"❌ Connection failed: {error_msg}")
        raise Exception(error_msg)


def test_with_custom_tts_service():
    """
    Test using the custom TTS service wrapper
    """
    logger.info("\n🔄 Testing with custom TTS service wrapper...")
    
    try:
        # Create Fish Speech TTS service
        tts_service = create_fish_speech_tts_service(
            voice="default",  # Use default since our trained voice may not be loaded
            output_format="wav"
        )
        
        # Test Japanese text
        japanese_text = "おはようございます。今日も頑張りましょう！"
        
        logger.info(f"Text: {japanese_text}")
        logger.info("(Ohayou gozaimasu. Kyou mo ganbarimashou!)")
        logger.info("(Good morning. Let's do our best today too!)")
        
        response = tts_service.text_to_speech(
            text=japanese_text,
            output_path="japanese_morning_greeting.wav"
        )
        
        if response.success:
            logger.info("✅ Custom TTS service test successful!")
            logger.info(f"Output: {response.audio_file_path}")
            logger.info(f"Duration: {response.duration_ms/1000:.2f}s")
            return True
        else:
            logger.error(f"❌ Custom TTS service failed: {response.error_message}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Custom TTS service test failed: {e}")
        return False


def demonstrate_japanese_learning_integration():
    """
    Show how this could integrate with the Japanese learning agent
    """
    logger.info("\n🎓 Japanese Learning Agent Integration Demo")
    logger.info("="*50)
    
    # Example Japanese learning scenarios
    learning_examples = [
        {
            "lesson": "Basic Greetings",
            "japanese": "おはよう、こんにちは、こんばんは",
            "romaji": "ohayou, konnichiwa, konbanwa",
            "english": "good morning, hello, good evening"
        },
        {
            "lesson": "Polite Expressions", 
            "japanese": "すみません、ありがとうございます、どういたしまして",
            "romaji": "sumimasen, arigatou gozaimasu, dou itashimashite",
            "english": "excuse me, thank you, you're welcome"
        },
        {
            "lesson": "Numbers 1-5",
            "japanese": "いち、に、さん、よん、ご",
            "romaji": "ichi, ni, san, yon, go", 
            "english": "one, two, three, four, five"
        }
    ]
    
    logger.info("🎯 Possible integration scenarios:")
    
    for example in learning_examples:
        logger.info(f"\n📚 {example['lesson']}")
        logger.info(f"   Japanese: {example['japanese']}")
        logger.info(f"   Romaji: {example['romaji']}")
        logger.info(f"   English: {example['english']}")
        logger.info(f"   🎵 Could generate: {example['lesson'].lower().replace(' ', '_')}.wav")
    
    logger.info("\n🔗 Agent Integration Example:")
    agent_config = {
        "name": "JapaneseLearningAgent",
        "description": "Learn Japanese with audio pronunciation",
        "steps": [
            {
                "type": "chat",
                "provider": "ollama",
                "prompt": "Teach me basic Japanese greetings"
            },
            {
                "type": "tts",
                "provider": "fish_speech",
                "voice": "sonnet29_japanese",
                "text": "おはようございます。こんにちは。こんばんは。",
                "output_path": "japanese_greetings.wav"
            }
        ]
    }
    
    logger.info(json.dumps(agent_config, indent=2, ensure_ascii=False))


def main():
    """Main test function"""
    logger.info("🚀 Fish Speech Japanese TTS Testing")
    logger.info("Using trained Sonnet 29 voice for Japanese speech synthesis")
    logger.info("="*60)
    
    # Test direct API calls
    results = test_fish_speech_japanese()
    
    # Test custom TTS service
    custom_success = test_with_custom_tts_service()
    
    # Show integration possibilities
    demonstrate_japanese_learning_integration()
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("🎉 FINAL RESULTS")
    logger.info("="*60)
    
    successful_tests = len([r for r in results if r.get('success', False)])
    total_tests = len(results)
    
    logger.info(f"📊 Direct API Tests: {successful_tests}/{total_tests} successful")
    logger.info(f"🔧 Custom Service Test: {'✅ Success' if custom_success else '❌ Failed'}")
    
    if successful_tests > 0:
        logger.info("\n🎵 Audio files generated - you can play them to hear the results!")
        logger.info("The trained Sonnet 29 voice speaking Japanese content.")
    
    logger.info("\n🎯 Next Steps:")
    logger.info("1. Play the generated audio files to hear the Japanese speech")
    logger.info("2. Integrate with Japanese Learning Agent for educational content")
    logger.info("3. Fine-tune voice parameters for better Japanese pronunciation")


if __name__ == "__main__":
    main()