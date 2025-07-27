"""
Test Fish Speech voice cloning with shorter reference audio to avoid GPU memory issues
"""

import os
import sys
import json
import requests
import logging
import base64
from pathlib import Path

# Add ai-lego-bricks to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ai-lego-bricks'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_minimal_reference_audio():
    """
    Create a very short reference audio (2-3 seconds) to minimize GPU memory usage
    """
    
    logger.info("✂️  Creating Minimal Reference Audio for GPU Memory Efficiency")
    logger.info("=" * 65)
    
    try:
        import librosa
        import soundfile as sf
        
        # Load the original audio
        sonnet_audio_path = "../../sonnet29.mp3"
        audio, sr = librosa.load(sonnet_audio_path, sr=22050)  # Lower sample rate to save memory
        
        logger.info(f"📊 Original audio: {len(audio)/sr:.2f}s at {sr}Hz")
        
        # Extract a very short segment (2 seconds) with clear speech
        start_sample = int(3.0 * sr)  # Start at 3 seconds
        end_sample = int(5.0 * sr)    # End at 5 seconds (2-second segment)
        
        reference_segment = audio[start_sample:end_sample]
        
        # Normalize the segment
        reference_segment = librosa.util.normalize(reference_segment)
        
        # Save minimal reference
        reference_path = "sonnet29_minimal_reference.wav"
        sf.write(reference_path, reference_segment, sr)
        
        duration = len(reference_segment) / sr
        file_size = os.path.getsize(reference_path)
        
        logger.info(f"✅ Created minimal reference: {reference_path}")
        logger.info(f"⏱️  Duration: {duration:.2f}s")
        logger.info(f"📊 File size: {file_size:,} bytes")
        logger.info("🎯 Optimized for minimal GPU memory usage")
        
        return reference_path
        
    except ImportError:
        logger.error("❌ librosa not available for audio processing")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to create minimal reference: {e}")
        return None


def test_voice_cloning_with_minimal_reference():
    """
    Test Fish Speech voice cloning with minimal reference audio
    """
    
    logger.info("\n🎤 Testing Voice Cloning with Minimal Reference Audio")
    logger.info("=" * 58)
    
    # Create minimal reference audio
    reference_path = create_minimal_reference_audio()
    if not reference_path:
        return False
    
    # Load the minimal reference audio
    try:
        with open(reference_path, 'rb') as f:
            audio_data = f.read()
        
        # Convert to base64 for API
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        logger.info(f"📊 Reference audio size: {len(audio_data):,} bytes")
        logger.info(f"📊 Base64 size: {len(audio_base64):,} characters")
        
        # Corresponding text for the reference segment
        reference_text = "When, in disgrace with fortune and men's eyes"
        
        reference_audio = {
            "audio": audio_base64,
            "text": reference_text
        }
        
        logger.info("✅ Minimal reference audio prepared")
        
    except Exception as e:
        logger.error(f"❌ Failed to prepare reference audio: {e}")
        return False
    
    # Test Japanese text with Sonnet 29 voice
    japanese_texts = [
        "こんにちは",  # Simple greeting
        "ありがとう",  # Thank you  
        "さようなら"   # Goodbye
    ]
    
    fish_speech_url = "http://100.83.40.11:8080"
    results = []
    
    for i, japanese_text in enumerate(japanese_texts, 1):
        logger.info(f"\n--- Test {i}/3: {japanese_text} ---")
        
        # Prepare Fish Speech API request with minimal reference audio
        request_data = {
            "text": japanese_text,
            "references": [reference_audio],
            "format": "wav",
            "normalize": True,
            "streaming": False,
            "chunk_length": 100,  # Smaller chunks to save memory
            "max_new_tokens": 512,  # Reduced tokens
            "top_p": 0.7,
            "repetition_penalty": 1.0,
            "temperature": 0.7
        }
        
        try:
            logger.info("🔄 Making TTS request with minimal reference...")
            
            response = requests.post(
                f"{fish_speech_url}/v1/tts",
                json=request_data,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Save audio file
                output_path = f"japanese_sonnet29_voice_{i}.wav"
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                logger.info(f"✅ SUCCESS! Voice cloning worked!")
                logger.info(f"📁 Output: {output_path}")
                logger.info(f"📊 File size: {file_size:,} bytes")
                
                results.append({
                    "success": True,
                    "text": japanese_text,
                    "output": output_path,
                    "size": file_size
                })
                
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Voice cloning failed: {error_msg}")
                results.append({
                    "success": False,
                    "text": japanese_text,
                    "error": error_msg
                })
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Request failed: {error_msg}")
            results.append({
                "success": False,
                "text": japanese_text,
                "error": error_msg
            })
    
    return results


def test_without_reference_audio():
    """
    Test default Fish Speech without reference audio (fallback)
    """
    
    logger.info("\n🎵 Testing Default Fish Speech (No Reference Audio)")
    logger.info("=" * 55)
    
    japanese_text = "こんにちは、元気ですか？"
    
    request_data = {
        "text": japanese_text,
        "format": "wav",
        "normalize": True,
        "streaming": False,
        "chunk_length": 100,
        "max_new_tokens": 512,
        "top_p": 0.8,
        "repetition_penalty": 1.1,
        "temperature": 0.8
    }
    
    fish_speech_url = "http://100.83.40.11:8080"
    
    try:
        logger.info("🔄 Making TTS request without reference audio...")
        
        response = requests.post(
            f"{fish_speech_url}/v1/tts",
            json=request_data,
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            output_path = "japanese_default_voice.wav"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            logger.info(f"✅ Default voice generation successful!")
            logger.info(f"📁 Output: {output_path}")
            logger.info(f"📊 File size: {file_size:,} bytes")
            logger.info("🎯 This is the default Fish Speech voice")
            
            return True
            
        else:
            logger.error(f"❌ Default voice failed: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Default voice request failed: {e}")
        return False


def main():
    """Main test function"""
    
    logger.info("🚀 Fish Speech Voice Cloning with Memory Optimization")
    logger.info("Testing Sonnet 29 voice cloning with minimal GPU usage")
    logger.info("=" * 70)
    
    # Test with minimal reference audio
    results = test_voice_cloning_with_minimal_reference()
    
    # Test default voice as comparison
    default_success = test_without_reference_audio()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESULTS SUMMARY")
    logger.info("=" * 70)
    
    if results:
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        logger.info(f"🎤 Voice Cloning Tests: {len(successful)}/{len(results)} successful")
        
        if successful:
            logger.info("✅ Successful voice cloning outputs:")
            for result in successful:
                logger.info(f"   • {result['output']} - '{result['text']}'")
            
            logger.info("\n🎵 These files should sound like the Sonnet 29 voice!")
            logger.info("Compare them to the default voice file to hear the difference.")
        
        if failed:
            logger.info("❌ Failed tests:")
            for result in failed:
                logger.info(f"   • '{result['text']}': {result['error']}")
    
    logger.info(f"🔧 Default Voice Test: {'✅ Success' if default_success else '❌ Failed'}")
    
    logger.info("\n🎯 Key Insights:")
    logger.info("• Fish Speech uses reference audio for voice cloning")
    logger.info("• GPU memory constraints limit reference audio size")  
    logger.info("• Shorter reference audio (2-3s) works better than long samples")
    logger.info("• Compare voice-cloned output to default to hear differences")
    
    logger.info("\n📋 Files Generated:")
    logger.info("• sonnet29_minimal_reference.wav - Optimized reference audio")
    logger.info("• japanese_sonnet29_voice_*.wav - Voice cloning results")
    logger.info("• japanese_default_voice.wav - Default Fish Speech voice")


if __name__ == "__main__":
    main()