#!/usr/bin/env python3
"""
Simple test script to verify Deepgram integration
"""

import os
import asyncio
from dotenv import load_dotenv
from audio_services import TTSService, ASRService

# Load environment variables
load_dotenv()

async def test_deepgram_services():
    """Test Deepgram TTS and ASR services"""
    
    print("🧪 Testing Deepgram Integration")
    print("=" * 40)
    
    # Check if Deepgram API key is configured
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ DEEPGRAM_API_KEY not found in environment")
        return False
    
    print(f"✅ Deepgram API Key: {api_key[:10]}...")
    
    # Test TTS Service
    print("\n🔊 Testing Text-to-Speech (TTS)")
    try:
        tts_service = TTSService(provider="deepgram")
        test_text = "Hello! This is a test of Deepgram text-to-speech for medical appointment booking."
        
        print(f"📝 Input text: {test_text}")
        print("🔄 Generating audio...")
        
        # Generate audio
        audio_data = tts_service.text_to_speech(test_text)
        audio_base64 = tts_service.text_to_base64_audio(test_text)
        
        print(f"✅ TTS successful!")
        print(f"   Audio size: {len(audio_data)} bytes")
        print(f"   Base64 size: {len(audio_base64)} chars")
        print(f"   Voice: {os.getenv('TTS_VOICE', 'aura-asteria-en')}")
        
    except Exception as e:
        print(f"❌ TTS failed: {e}")
        return False
    
    # Test ASR Service  
    print("\n🎤 Testing Automatic Speech Recognition (ASR)")
    try:
        asr_service = ASRService()
        
        # Note: We can't easily test ASR without actual audio input
        # But we can verify the service initializes correctly
        if hasattr(asr_service, 'deepgram') and asr_service.deepgram:
            print("✅ ASR service initialized successfully")
            print("   Provider: Deepgram")
            print("   Fallback: OpenAI Whisper (if available)")
        else:
            print("⚠️  ASR service initialized but Deepgram client not available")
            
    except Exception as e:
        print(f"❌ ASR initialization failed: {e}")
        return False
    
    print("\n🎉 All Deepgram services initialized successfully!")
    print("\n📋 Next steps:")
    print("1. Start the API server: python main.py")
    print("2. Create an appointment: POST /appointments")
    print("3. Start conversation: GET /start_conversation/{call_id}")
    print("4. Send speech: POST /conversation/{call_id}/speak")
    print("5. Get audio response: GET /conversation/{call_id}/audio")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_deepgram_services())