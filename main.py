#!/usr/bin/env python3
"""
Medical Appointment Booking AI Agent
====================================

An AI-powered medical appointment booking system with Deepgram speech support:
- FastAPI for REST API endpoints
- OpenAI GPT-4 for natural language processing  
- Deepgram for speech-to-text (ASR) and text-to-speech (TTS)
- PostgreSQL for data persistence
- JWT-based phone number authentication

Features:
- Phone number OTP authentication
- Voice-based conversation via Deepgram
- Text-based conversation interface
- Real-time speech processing
- Appointment scheduling and management
- User-specific appointment tracking

Usage:
    python main.py

API Endpoints:
    POST /auth/send-otp - Send OTP to phone number
    POST /auth/verify-otp - Verify OTP and get access token
    POST /appointments - Create new appointment
    GET /start_conversation/{call_id} - Start conversation session
    POST /conversation/{call_id}/speak - Send speech input
    POST /conversation/{call_id}/text - Send text input
    GET /conversation/{call_id}/audio - Get AI response audio
    GET /appointments - List user appointments

Environment Variables:
    OPENAI_API_KEY - Required for OpenAI GPT-4
    DEEPGRAM_API_KEY - Required for speech services
    DATABASE_URL - PostgreSQL connection string
    TWILIO_ACCOUNT_SID - For OTP SMS (optional for testing)
    TWILIO_AUTH_TOKEN - For OTP SMS (optional for testing)
    TWILIO_PHONE_NUMBER - For OTP SMS (optional for testing)
    JWT_SECRET_KEY - For JWT token signing
    APP_HOST - Server host (default: 0.0.0.0)
    APP_PORT - Server port (default: 8000)
    DEBUG - Enable debug mode (default: True)
    TTS_VOICE - Deepgram voice selection (default: aura-asteria-en)
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
    required_env_vars = ["OPENAI_API_KEY", "DATABASE_URL", "DEEPGRAM_API_KEY"]
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
    print(f"   Database: {'✅ Configured' if os.getenv('DATABASE_URL') else '❌ Missing'}")
    print(f"   Deepgram API: {'✅ Configured' if os.getenv('DEEPGRAM_API_KEY') else '❌ Missing'}")
    print(f"   Twilio (OTP only): {'✅ Configured' if os.getenv('TWILIO_ACCOUNT_SID') else '⚠️  Optional'}")
    
    print("\n📋 Available Endpoints:")
    print(f"   🌐 API Documentation: http://{host}:{port}/docs")
    print(f"   � Send OTP: POST http://{host}:{port}/auth/send-otp")
    print(f"   � Verify OTP: POST http://{host}:{port}/auth/verify-otp")
    print(f"   � Create Appointment: POST http://{host}:{port}/appointments")
    print(f"   💬 Start Conversation: GET http://{host}:{port}/start_conversation/{{call_id}}")
    print(f"   🎤 Send Speech: POST http://{host}:{port}/conversation/{{call_id}}/speak")
    print(f"   📝 Send Text: POST http://{host}:{port}/conversation/{{call_id}}/text")
    print(f"   🔊 Get Audio: GET http://{host}:{port}/conversation/{{call_id}}/audio")
    print(f"   📊 View Appointments: GET http://{host}:{port}/appointments")
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