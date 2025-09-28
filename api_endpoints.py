from fastapi import FastAPI, HTTPException, WebSocket, Response, Form
from pydantic import BaseModel
from typing import Optional
import uuid
import os
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import base64
from deepgram import Deepgram
from audio_services import TTSService, ASRService
from models import CallScheduleRequest, CallScheduleResponse
import openai

# Initialize OpenAI client
try:
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"OpenAI client initialization failed: {e}")
    openai_client = None

def process_conversation_with_llm(user_input: str, call_data: dict, conversation_history: list = None) -> str:
    """Process user input with LLM for natural conversation about appointment booking."""
    if not openai_client:
        # Fallback to simple keyword matching if OpenAI fails
        return process_simple_conversation(user_input, call_data)
    
    if conversation_history is None:
        conversation_history = []
    
    # System prompt for appointment booking
    system_prompt = f"""You are an AI assistant calling a hospital to book a medical appointment. You are calling on behalf of patient {call_data['patient_name']} to schedule an appointment with Dr. {call_data['doctor_name']} at {call_data['hospital_name']} on {call_data['call_time']}.

Your goals:
1. Confirm you reached the correct hospital appointment line
2. Request to book the appointment for the specified patient, doctor, and time
3. Handle confirmations, denials, and alternative suggestions professionally
4. Keep responses concise and natural for voice conversation
5. End the conversation politely once booking is confirmed

Current call status: {call_data.get('status', 'scheduled')}
Conversation history: {'; '.join([f"{'AI' if msg['role'] == 'assistant' else 'User'}: {msg['content']}" for msg in conversation_history[-3:]]) if conversation_history else 'Just started'}

Respond naturally as if you're on a phone call. Keep responses under 50 words when possible."""
    
    # Add current user input to history
    conversation_history.append({"role": "user", "content": user_input})
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history[-6:]  # Keep last 6 messages for context
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Add AI response to history
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Update conversation history in call data
        call_data["conversation_history"] = conversation_history
        
        # Check for booking confirmation keywords to update status
        if any(word in ai_response.lower() for word in ["confirmed", "booked", "scheduled", "perfect", "thank you for confirming"]):
            call_data["status"] = "appointment_booked"
        
        return ai_response
        
    except Exception as e:
        print(f"LLM processing failed: {e}")
        return process_simple_conversation(user_input, call_data)

def process_simple_conversation(user_input: str, call_data: dict) -> str:
    """Fallback simple conversation processing when LLM fails."""
    user_input = user_input.lower()
    
    # Simple keyword-based responses
    if any(word in user_input for word in ["yes", "correct", "right", "this is", "speaking", "appointment"]):
        return f"Great! I'd like to schedule an appointment for {call_data['patient_name']} with Dr. {call_data['doctor_name']} on {call_data['call_time']}. Is this time available?"
    elif any(word in user_input for word in ["no", "not available", "full", "busy", "unavailable"]):
        return "I understand that time isn't available. Could you suggest an alternative time for the appointment?"
    elif any(word in user_input for word in ["book", "schedule", "confirm", "available"]):
        call_data["status"] = "appointment_booked"
        return f"Perfect! The appointment for {call_data['patient_name']} with Dr. {call_data['doctor_name']} has been confirmed. Thank you!"
    else:
        return "I'm sorry, I didn't understand. Could you please clarify if the appointment time is available?"

app = FastAPI(title="Call Scheduler API", description="Schedule and initiate medical calls.", version="1.0.0")

# --- In-memory store ---
scheduled_calls = {}

# --- API Endpoints ---
@app.post("/schedule_call", response_model=CallScheduleResponse)
async def schedule_call(request: CallScheduleRequest):
    """Schedule an automated appointment booking call to the hospital on behalf of a patient."""
    call_id = str(uuid.uuid4())
    scheduled_calls[call_id] = {
        "patient_name": request.patient_name,
        "patient_phone": request.patient_phone,
        "hospital_name": request.hospital_name,
        "hospital_phone": request.hospital_phone,
        "doctor_name": request.doctor_name,
        "call_time": request.call_time,
        "status": "scheduled"
    }
    return CallScheduleResponse(call_id=call_id, status="scheduled", scheduled_time=request.call_time)

@app.get("/trigger_call/{call_id}")
async def trigger_call(call_id: str):
    """Initiate automated appointment booking call to the hospital using Twilio and Deepgram."""
    call = scheduled_calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Initialize Twilio client
    twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    
    try:
        # Initiate call to hospital using Twilio
        twilio_call = twilio_client.calls.create(
            to=call["hospital_phone"],
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            url=f"{os.getenv('WEBHOOK_BASE_URL')}/twilio/webhook/{call_id}",
            method="POST"
        )
        
        # Update call status
        call["status"] = "initiated"
        call["twilio_call_sid"] = twilio_call.sid
        
        return {
            "call_id": call_id, 
            "status": "initiated", 
            "twilio_call_sid": twilio_call.sid,
            "details": call
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

@app.post("/twilio/webhook/{call_id}")
async def twilio_webhook(call_id: str):
    """Handle Twilio webhook for call processing with Deepgram."""
    call = scheduled_calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Initial greeting for appointment booking
    greeting = f"Hello! I'm calling on behalf of {call['patient_name']} to schedule an appointment with Dr. {call['doctor_name']} at {call['hospital_name']}. Is this the correct number for appointment scheduling?"
    
    response.say(greeting)
    
    # Gather speech input with better parameters
    gather = response.gather(
        input="speech",
        action=f"/twilio/process_input/{call_id}",
        method="POST",
        timeout=10,
        speech_timeout="auto",
    speech_model="phone_call"
    )
    
    return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/process_input/{call_id}")
async def process_input(call_id: str, SpeechResult: Optional[str] = Form(None)):
    """Process speech input from Twilio and generate LLM-powered response."""
    print(f"Processing input for call {call_id}, SpeechResult: {SpeechResult}")
    
    call = scheduled_calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Initialize services
    tts_service = TTSService()
    
    response = VoiceResponse()
    
    if SpeechResult:
        # Get conversation history
        conversation_history = call.get("conversation_history", [])
        
        # Process with LLM
        ai_response = process_conversation_with_llm(SpeechResult, call, conversation_history)
        print(f"AI Response: {ai_response}")
        
        # Convert response to speech and store it on the call record
        audio_base64 = tts_service.text_to_base64_audio(ai_response)
        call['last_audio'] = audio_base64

        # Play the audio response via a reachable URL (Twilio will fetch this URL)
        webhook_base = os.getenv('WEBHOOK_BASE_URL')
        if webhook_base:
            audio_url = f"{webhook_base}/twilio/audio/{call_id}"
            response.play(audio_url)
        else:
            # If there's no public base URL, fall back to Twilio's Say
            response.say(ai_response)
        
        # Continue gathering input unless appointment is booked
        if call.get("status") != "appointment_booked":
            gather = response.gather(
                input="speech",
                action=f"/twilio/process_input/{call_id}",
                method="POST",
                timeout=10,
                speech_timeout="auto",
                speech_model="phone_call"
            )
        else:
            # End conversation if appointment is booked
            response.say("Thank you for your assistance. Goodbye.")
            response.hangup()
    
    else:
        # No speech detected
        print("No speech result received")
        ai_response = "I'm sorry, I didn't catch that. Could you please repeat?"
        audio_base64 = tts_service.text_to_base64_audio(ai_response)
        # Store and serve fallback audio
        call['last_audio'] = audio_base64
        webhook_base = os.getenv('WEBHOOK_BASE_URL')
        if webhook_base:
            audio_url = f"{webhook_base}/twilio/audio/{call_id}"
            response.play(audio_url)
        else:
            response.say(ai_response)
        
        gather = response.gather(
            input="speech",
            action=f"/twilio/process_input/{call_id}",
            method="POST",
            timeout=10,
            speech_timeout="auto",
            speech_model="phone_call"
        )
    
    return Response(content=str(response), media_type="application/xml")


@app.get("/twilio/audio/{call_id}")
async def twilio_audio(call_id: str):
    """Serve last generated TTS audio for a call as WAV so Twilio can fetch and play it."""
    print(f"Received request for audio for call_id={call_id}")
    call = scheduled_calls.get(call_id)
    if not call or 'last_audio' not in call:
        print(f"Audio not found for call {call_id}")
        raise HTTPException(status_code=404, detail="Audio not found for this call")

    b64 = call['last_audio']
    # Strip possible data URI prefix
    if isinstance(b64, str) and b64.startswith("data:"):
        try:
            b64 = b64.split(',', 1)[1]
        except Exception:
            print("Failed to parse data URI in stored audio")
            raise HTTPException(status_code=500, detail="Invalid stored audio format")

    try:
        audio_bytes = base64.b64decode(b64)
    except Exception as e:
        print(f"Failed to decode base64 audio for call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to decode audio: {e}")

    # Detect common audio formats from magic bytes and return appropriate Content-Type
    media_type = "audio/wav"
    if audio_bytes.startswith(b"RIFF"):
        media_type = "audio/wav"
    elif audio_bytes.startswith(b"ID3") or audio_bytes[:2] in (b"\xff\xfb", b"\xff\xf3"):
        media_type = "audio/mpeg"
    elif audio_bytes.startswith(b"OggS"):
        media_type = "audio/ogg"

    headers = {"Content-Length": str(len(audio_bytes))}
    print(f"Serving audio for call {call_id} with media_type={media_type}, size={len(audio_bytes)}")
    return Response(content=audio_bytes, media_type=media_type, headers=headers)

@app.get("/")
async def root():
    return {"message": "Medical Appointment Booking API. Use /schedule_call to schedule an appointment booking call, /trigger_call/{call_id} to initiate automated appointment booking with the hospital."}
