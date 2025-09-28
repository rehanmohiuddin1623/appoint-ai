#!/usr/bin/env python3
"""
Medical Appointment Booking AI Agent
====================================

An AI-powered medical appointment booking system with voice support using:
- FastAPI for REST API endpoints
- LangGraph for conversation flow management  
- OpenAI GPT-4 for natural language processing
- OpenAI Whisper for speech-to-text (ASR)
- OpenAI TTS for text-to-speech
- Fallback to Google services when needed

Features:
- Voice-based appointment booking via microphone
- Text-based chat interface
- Collects patient information (name, age, phone)
- Gathers appointment details (doctor, hospital, time)
- Records medical conditions (blood pressure, diabetes, etc.)
- Confirms appointments with unique confirmation IDs

Usage:
    python main.py

API Endpoints:
    POST /session/start - Start new conversation session (with optional patient info)
    POST /chat/text - Text-based conversation
    POST /chat/voice - Voice-based conversation via microphone
    POST /chat/voice/upload - Upload audio file for conversation
    GET /session/{session_id} - Get session state
    GET /appointment/{session_id}/summary - Get appointment summary
    DELETE /session/{session_id} - End session

Environment Variables:
    OPENAI_API_KEY - Required for OpenAI services
    APP_HOST - Server host (default: 0.0.0.0)
    APP_PORT - Server port (default: 8000)
    DEBUG - Enable debug mode (default: True)
    TTS_VOICE - TTS voice selection (default: alloy)
    TTS_SPEED - TTS speed (default: 1.0)
"""

import os
import uvicorn
from dotenv import load_dotenv
from api_endpoints import app

# Load environment variables
load_dotenv()

def main():
    """Main application entry point"""
    # Validate required environment variables
    required_env_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please update your .env file with the missing variables.")
        print("   Example .env file created in the project directory.")
        return
    
    # Configuration
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print("🏥 Starting Medical Appointment Booking AI Agent...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   OpenAI API: {'✅ Configured' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    
    print("\n📋 Available Endpoints:")
    print(f"   🌐 API Documentation: http://{host}:{port}/docs")
    print(f"   💬 Start Session: POST http://{host}:{port}/session/start")
    print(f"   📝 Text Chat: POST http://{host}:{port}/chat/text")  
    print(f"   🎤 Voice Chat: POST http://{host}:{port}/chat/voice")
    print(f"   📊 Health Check: GET http://{host}:{port}/health")
    
    print("\n🚀 Starting server...")
    
    try:
        if debug:
            uvicorn.run(
                "api_endpoints:app",
                host=host,
                port=port,
                reload=True,
                log_level="info"
            )
        else:
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="warning"
            )
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()