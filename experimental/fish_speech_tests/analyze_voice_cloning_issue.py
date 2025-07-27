"""
Analyze why Fish Speech isn't using the trained Sonnet 29 voice
Fish Speech uses reference audio for voice cloning, not traditional training
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


def analyze_fish_speech_voice_system():
    """
    Analyze how Fish Speech actually handles voice cloning
    """
    
    logger.info("🔍 Analyzing Fish Speech Voice Cloning System")
    logger.info("=" * 60)
    
    # Check the API schema again
    fish_speech_url = "http://100.83.40.11:8080"
    
    try:
        response = requests.get(f"{fish_speech_url}/json", timeout=5)
        if response.status_code == 200:
            api_schema = response.json()
            
            # Look at the TTS request schema
            tts_schema = api_schema.get("components", {}).get("schemas", {}).get("ServeTTSRequest", {})
            
            logger.info("🎯 Fish Speech TTS Request Parameters:")
            logger.info("-" * 40)
            
            properties = tts_schema.get("properties", {})
            for param, details in properties.items():
                param_type = details.get("type", "unknown")
                description = details.get("title", param)
                default = details.get("default", "N/A")
                logger.info(f"  • {param}: {param_type} - {description} (default: {default})")
            
            # Focus on voice-related parameters
            logger.info("\n🎤 Voice-Related Parameters:")
            logger.info("-" * 40)
            
            if "references" in properties:
                ref_schema = properties["references"]
                logger.info("📎 References parameter found!")
                logger.info(f"   Type: {ref_schema.get('type')}")
                logger.info(f"   Description: Reference audio for voice cloning")
                
                # Check reference audio schema
                ref_items = ref_schema.get("items", {}).get("$ref", "")
                if "ServeReferenceAudio" in ref_items:
                    logger.info("   ✅ Supports reference audio for voice cloning!")
            
            if "reference_id" in properties:
                logger.info("🆔 Reference ID parameter found!")
                logger.info("   Can reference pre-loaded voice samples")
            
        else:
            logger.error(f"Failed to get API schema: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Failed to analyze API: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🧠 ANALYSIS: How Fish Speech Voice Cloning Works")
    logger.info("=" * 60)
    
    logger.info("""
🎯 KEY INSIGHT: Fish Speech uses REFERENCE AUDIO, not traditional training!

📚 How it actually works:
1. Fish Speech uses reference audio samples for voice cloning
2. You provide a short audio sample (3-10 seconds) with corresponding text
3. The model clones the voice characteristics from that sample
4. No traditional "training" or model fine-tuning required

❌ What we did wrong:
- Created training data preparation (not needed for Fish Speech)
- Expected model training/fine-tuning (Fish Speech doesn't work this way)
- Didn't use the 'references' parameter in API calls

✅ What we should do:
- Use sonnet29.mp3 as reference audio directly
- Include reference audio in TTS API calls
- Extract a clean segment from sonnet29.mp3 for voice cloning
    """)


def test_reference_audio_approach():
    """
    Test using the original sonnet29.mp3 as reference audio
    """
    
    logger.info("\n🎵 Testing Reference Audio Approach")
    logger.info("=" * 50)
    
    # Path to original audio
    sonnet_audio_path = "../../sonnet29.mp3"
    
    if not os.path.exists(sonnet_audio_path):
        logger.error(f"❌ Original audio not found: {sonnet_audio_path}")
        return False
    
    logger.info(f"✅ Found original audio: {sonnet_audio_path}")
    
    # For Fish Speech, we need to provide the reference audio as base64
    try:
        with open(sonnet_audio_path, 'rb') as f:
            audio_data = f.read()
        
        # Convert to base64 for API
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        logger.info(f"📊 Audio size: {len(audio_data):,} bytes")
        logger.info(f"📊 Base64 size: {len(audio_base64):,} characters")
        
        # Create reference audio object for Fish Speech
        reference_text = "When, in disgrace with fortune and men's eyes, I all alone beweep my outcast state"
        
        reference_audio = {
            "audio": audio_base64,
            "text": reference_text
        }
        
        logger.info("✅ Reference audio prepared for Fish Speech")
        logger.info(f"📝 Reference text: {reference_text[:50]}...")
        
        return reference_audio
        
    except Exception as e:
        logger.error(f"❌ Failed to prepare reference audio: {e}")
        return False


def test_voice_cloning_with_reference():
    """
    Test Fish Speech voice cloning using reference audio
    """
    
    logger.info("\n🎤 Testing Voice Cloning with Reference Audio")
    logger.info("=" * 55)
    
    # Get reference audio
    reference_audio = test_reference_audio_approach()
    if not reference_audio:
        return False
    
    # Test Japanese text with Sonnet 29 voice
    japanese_text = "こんにちは、私の名前は田中です。"
    
    logger.info(f"🎌 Japanese text: {japanese_text}")
    logger.info("🎵 Using Sonnet 29 voice as reference")
    
    # Prepare Fish Speech API request with reference audio
    request_data = {
        "text": japanese_text,
        "references": [reference_audio],  # This is the key!
        "format": "wav",
        "normalize": True,
        "streaming": False,
        "chunk_length": 200,
        "max_new_tokens": 1024,
        "top_p": 0.8,
        "repetition_penalty": 1.1,
        "temperature": 0.8
    }
    
    fish_speech_url = "http://100.83.40.11:8080"
    
    try:
        logger.info("🔄 Making TTS request with reference audio...")
        
        response = requests.post(
            f"{fish_speech_url}/v1/tts",
            json=request_data,
            timeout=60,  # Longer timeout for voice cloning
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # Save audio file
            output_path = "japanese_with_sonnet29_voice.wav"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            logger.info(f"✅ SUCCESS! Voice cloning worked!")
            logger.info(f"📁 Output: {output_path}")
            logger.info(f"📊 File size: {file_size:,} bytes")
            logger.info("🎵 This should sound like the Sonnet 29 voice!")
            
            return True
            
        else:
            logger.error(f"❌ Voice cloning failed: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Voice cloning request failed: {e}")
        return False


def create_optimized_reference_audio():
    """
    Create an optimized reference audio segment from sonnet29.mp3
    Fish Speech works best with 3-10 second clean audio samples
    """
    
    logger.info("\n✂️  Creating Optimized Reference Audio")
    logger.info("=" * 45)
    
    try:
        import librosa
        import soundfile as sf
        
        # Load the original audio
        sonnet_audio_path = "../../sonnet29.mp3"
        audio, sr = librosa.load(sonnet_audio_path, sr=44100)
        
        logger.info(f"📊 Original audio: {len(audio)/sr:.2f}s at {sr}Hz")
        
        # Extract a clean 5-second segment from the beginning
        # Skip the first 2 seconds in case there's silence/noise
        start_sample = int(2.0 * sr)  # Start at 2 seconds
        end_sample = int(7.0 * sr)    # End at 7 seconds (5-second segment)
        
        reference_segment = audio[start_sample:end_sample]
        
        # Normalize the segment
        reference_segment = librosa.util.normalize(reference_segment)
        
        # Save optimized reference
        reference_path = "sonnet29_reference_optimized.wav"
        sf.write(reference_path, reference_segment, sr)
        
        duration = len(reference_segment) / sr
        logger.info(f"✅ Created optimized reference: {reference_path}")
        logger.info(f"⏱️  Duration: {duration:.2f}s")
        logger.info("🎯 This should work better for Fish Speech voice cloning")
        
        return reference_path
        
    except ImportError:
        logger.error("❌ librosa not available for audio processing")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to create optimized reference: {e}")
        return None


def main():
    """Main analysis function"""
    
    logger.info("🚀 Fish Speech Voice Cloning Analysis")
    logger.info("Investigating why Sonnet 29 voice isn't being used")
    logger.info("=" * 70)
    
    # Analyze the Fish Speech API
    analyze_fish_speech_voice_system()
    
    # Create optimized reference audio
    optimized_ref = create_optimized_reference_audio()
    
    # Test voice cloning with reference audio
    if optimized_ref:
        success = test_voice_cloning_with_reference()
        
        if success:
            logger.info("\n🎉 SUCCESS! Voice cloning with reference audio works!")
            logger.info("The generated audio should now sound like the Sonnet 29 voice")
        else:
            logger.info("\n❌ Voice cloning still not working - may need server configuration")
    
    logger.info("\n" + "=" * 70)
    logger.info("📋 SUMMARY & NEXT STEPS")
    logger.info("=" * 70)
    
    logger.info("""
🎯 Key Findings:
• Fish Speech uses reference audio, not traditional training
• We need to include audio samples in API calls using 'references' parameter
• The training data we created isn't used by Fish Speech

✅ Next Steps:
1. Use sonnet29.mp3 as reference audio in TTS calls
2. Include reference audio in 'references' parameter
3. Test Japanese TTS with proper voice cloning
4. Create clean reference audio segments for best results

🔧 Technical Solution:
• Include reference audio in every TTS request
• Use optimized 3-10 second audio segments
• Match reference text with audio content
    """)


if __name__ == "__main__":
    main()