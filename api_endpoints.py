from fastapi import FastAPI, HTTPException, WebSocket, Response, Form, Depends, status, Request, Header
from pydantic import BaseModel
from typing import Optional
import uuid
import os
from datetime import datetime
import base64
from audio_services import TTSService, ASRService
from models import (
    CallScheduleRequest, CallScheduleResponse, SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, VerifyOTPResponse, AppointmentResponse, UpdateAppointmentStateRequest,
    UserResponse
)
from database import get_db, AppointmentCall, User, AppointmentState, init_database
from auth import (
    initiate_otp_verification, verify_otp_code, get_current_user,
    validate_phone_number
)
from sqlalchemy.orm import Session
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
try:
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"OpenAI client initialization failed: {e}")
    openai_client = None

def process_conversation_with_llm(user_input: str, call: AppointmentCall, db: Session, conversation_history: list = None) -> str:
    """Process user input with LLM for natural conversation about appointment booking."""
    if not openai_client:
        # Fallback to simple keyword matching if OpenAI fails
        return process_simple_conversation(user_input, call, db)
    
    if conversation_history is None:
        conversation_history = call.conversation_history or []
    
    # System prompt for appointment booking
    system_prompt = f"""You are an AI assistant helping to book a medical appointment. You are assisting with booking an appointment for patient {call.patient_name} with Dr. {call.doctor_name} at {call.hospital_name}.

Your goals:
1. Confirm you reached the correct hospital appointment line
2. Request to book the appointment for the specified patient and doctor
3. Handle confirmations, denials, and alternative suggestions professionally
4. Keep responses concise and natural for voice conversation
5. End the conversation politely once booking is confirmed

Current call status: {call.status}
Conversation history: {'; '.join([f"{'AI' if msg['role'] == 'assistant' else 'User'}: {msg['content']}" for msg in conversation_history[-3:]]) if conversation_history else 'Just started'}

Respond naturally as if you're in a conversation. Keep responses under 50 words when possible."""
    
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
        
        # Update conversation history in database
        call.conversation_history = conversation_history
        call.updated_at = datetime.utcnow()
        
        # Check for booking confirmation keywords to update status
        if any(word in ai_response.lower() for word in ["confirmed", "booked", "scheduled", "perfect", "thank you for confirming"]):
            call.status = "appointment_booked"
        
        db.commit()
        return ai_response
        
    except Exception as e:
        print(f"LLM processing failed: {e}")
        return process_simple_conversation(user_input, call, db)

def process_simple_conversation(user_input: str, call: AppointmentCall, db: Session) -> str:
    """Fallback simple conversation processing when LLM fails."""
    user_input = user_input.lower()
    
    # Simple keyword-based responses
    if any(word in user_input for word in ["yes", "correct", "right", "this is", "speaking", "appointment"]):
        return f"Great! I'd like to schedule an appointment for {call.patient_name} with Dr. {call.doctor_name}. What times are available?"
    elif any(word in user_input for word in ["no", "not available", "full", "busy", "unavailable"]):
        return "I understand. Could you suggest some available times for the appointment?"
    elif any(word in user_input for word in ["book", "schedule", "confirm", "available"]):
        call.status = "appointment_booked"
        call.updated_at = datetime.utcnow()
        db.commit()
        return f"Perfect! The appointment for {call.patient_name} with Dr. {call.doctor_name} has been confirmed. Thank you!"
    else:
        return "I'm sorry, I didn't understand. Could you please clarify about the appointment availability?"

app = FastAPI(title="Medical Appointment Booking API", description="Schedule and manage medical appointments with OTP authentication.", version="2.0.0")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    if not init_database():
        print("Warning: Database initialization failed")

# --- OTP Authentication Endpoints ---

@app.post("/auth/send-otp", response_model=SendOTPResponse)
async def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP verification code to user's phone number"""
    try:
        # Validate phone number format
        phone_number = validate_phone_number(request.phone_number)
        
        # Initiate OTP verification
        result = initiate_otp_verification(phone_number, db)
        
        if result["success"]:
            return SendOTPResponse(
                success=True,
                message=result["message"],
                expires_in_minutes=5
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending OTP. Please try again."
        )

@app.post("/auth/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP code and return access token"""
    try:
        # Validate phone number format
        phone_number = validate_phone_number(request.phone_number)
        
        # Verify OTP code
        result = verify_otp_code(phone_number, request.otp_code, db)
        
        if result["success"]:
            return VerifyOTPResponse(
                success=True,
                message=result["message"],
                access_token=result.get("access_token"),
                token_type="bearer",
                user_id=result.get("user_id")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during verification. Please try again."
        )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(
        id=current_user.id,
        phone_number=current_user.phone_number,
        is_verified=current_user.is_verified,
        created_at=int(current_user.created_at.timestamp())
    )

# --- Appointment Management Endpoints ---
@app.post("/appointments", response_model=CallScheduleResponse)
async def create_appointment(
    request: CallScheduleRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new appointment booking call (requires authentication)"""
    call_id = str(uuid.uuid4())
    
    # Convert epoch timestamp to datetime for database storage
    call_time_dt = datetime.fromtimestamp(request.call_time)
    
    # Create new appointment call record with user association
    db_call = AppointmentCall(
        call_id=call_id,
        user_id=current_user.id,
        patient_name=request.patient_name,
        patient_phone=request.patient_phone,
        hospital_name=request.hospital_name,
        hospital_phone=request.hospital_phone,
        doctor_name=request.doctor_name,
        call_time=call_time_dt,
        appointment_state=AppointmentState.CREATED,
        status="scheduled"
    )
    
    try:
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        
        return CallScheduleResponse(
            call_id=call_id, 
            status="scheduled",
            appointment_state=db_call.appointment_state.value,
            scheduled_time=request.call_time,  # Return original epoch timestamp
            user_id=current_user.id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")

# Legacy endpoint for backward compatibility (will be deprecated)
@app.post("/schedule_call", response_model=CallScheduleResponse)
async def schedule_call(
    request: CallScheduleRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule an automated appointment booking call to the hospital on behalf of a patient."""
    call_id = str(uuid.uuid4())
    
    # Convert epoch timestamp to datetime for database storage
    call_time_dt = datetime.fromtimestamp(request.call_time)
    
    # Create new appointment call record
    db_call = AppointmentCall(
        call_id=call_id,
        user_id=current_user.id,
        patient_name=request.patient_name,
        patient_phone=request.patient_phone,
        hospital_name=request.hospital_name,
        hospital_phone=request.hospital_phone,
        doctor_name=request.doctor_name,
        call_time=call_time_dt,
        appointment_state=AppointmentState.CREATED,
        status="scheduled"
    )
    
    try:
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        
        return CallScheduleResponse(
            call_id=call_id, 
            status="scheduled",
            appointment_state=db_call.appointment_state.value,
            scheduled_time=request.call_time,  # Return original epoch timestamp
            user_id=current_user.id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to schedule call: {str(e)}")

@app.get("/start_conversation/{call_id}")
async def start_conversation(
    call_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a conversation session for appointment booking using Deepgram."""
    # Get call from database - ensure it belongs to the authenticated user
    call = db.query(AppointmentCall).filter(
        AppointmentCall.call_id == call_id,
        AppointmentCall.user_id == current_user.id
    ).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    try:
        # Import Twilio client
        from twilio.rest import Client
        twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        webhook_base_url = os.getenv("WEBHOOK_BASE_URL")
        if not (twilio_account_sid and twilio_auth_token and twilio_phone_number and webhook_base_url):
            raise HTTPException(status_code=500, detail="Twilio or webhook configuration missing in environment variables.")

        # Initialize Twilio client
        twilio_client = Client(twilio_account_sid, twilio_auth_token)

        # Get authorization header from the original request
        auth_header = request.headers.get("authorization", "")
        
        # Place outbound call to hospital with proper webhook URL
        twilio_call = twilio_client.calls.create(
            to=call.hospital_phone,
            from_=twilio_phone_number,
            url=f"{webhook_base_url}/twilio/webhook/{call_id}",
            method="POST"
        )

        # Update call status and Twilio SID
        call.status = "initiated"
        call.twilio_call_sid = twilio_call.sid
        call.updated_at = datetime.utcnow()
        if not call.conversation_history:
            call.conversation_history = []
        db.commit()

        return {
            "call_id": call_id,
            "status": "initiated",
            "twilio_call_sid": twilio_call.sid,
            "details": {
                "patient_name": call.patient_name,
                "hospital_name": call.hospital_name,
                "doctor_name": call.doctor_name,
                "hospital_phone": call.hospital_phone
            },
            "message": "Call initiated to hospital. Conversation will proceed over the phone using speech-to-text and text-to-speech."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start conversation/call: {str(e)}")

@app.post("/conversation/{call_id}/speak")
async def process_speech(
    call_id: str,
    audio_data: str = Form(...),  # base64 encoded audio
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process speech input using Deepgram and generate AI response."""
    # Get call from database
    call = db.query(AppointmentCall).filter(
        AppointmentCall.call_id == call_id,
        AppointmentCall.user_id == current_user.id
    ).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    try:
        # Initialize services
        asr_service = ASRService()
        tts_service = TTSService(provider=os.getenv("TTS_PROVIDER", "deepgram"))
        
        # Convert speech to text using Deepgram
        user_speech_text = asr_service.base64_audio_to_text(audio_data, provider="deepgram")
        print(f"User said: {user_speech_text}")
        
        if not user_speech_text or user_speech_text.strip() == "":
            ai_response = "I'm sorry, I didn't catch that. Could you please repeat?"
        else:
            # Get conversation history
            conversation_history = call.conversation_history or []
            
            # Process with LLM
            ai_response = process_conversation_with_llm(user_speech_text, call, db, conversation_history)
        
        print(f"AI Response: {ai_response}")
        
        # Convert AI response to speech
        audio_base64 = tts_service.text_to_base64_audio(ai_response)
        
        # Store the response audio
        call.last_audio = audio_base64
        call.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "call_id": call_id,
            "user_input": user_speech_text,
            "ai_response_text": ai_response,
            "ai_response_audio": audio_base64,
            "conversation_complete": call.status == "appointment_booked"
        }
        
    except Exception as e:
        print(f"Error processing speech: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process speech: {str(e)}")

@app.post("/conversation/{call_id}/text")
async def process_text(
    call_id: str,
    message: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process text input and generate AI response."""
    # Get call from database
    call = db.query(AppointmentCall).filter(
        AppointmentCall.call_id == call_id,
        AppointmentCall.user_id == current_user.id
    ).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    try:
        # Get conversation history
        conversation_history = call.conversation_history or []
        
        # Process with LLM
        ai_response = process_conversation_with_llm(message, call, db, conversation_history)
        print(f"Text conversation - User: {message}, AI: {ai_response}")
        
        # Optionally generate speech audio for the response
        tts_service = TTSService(provider=os.getenv("TTS_PROVIDER", "deepgram"))
        audio_base64 = tts_service.text_to_base64_audio(ai_response)
        
        # Store the response audio
        call.last_audio = audio_base64
        call.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "call_id": call_id,
            "user_input": message,
            "ai_response_text": ai_response,
            "ai_response_audio": audio_base64,
            "conversation_complete": call.status == "appointment_booked"
        }
        
    except Exception as e:
        print(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process text: {str(e)}")


@app.get("/conversation/{call_id}/audio")
async def get_conversation_audio(
    call_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the last generated TTS audio for a conversation."""
    print(f"Received request for audio for call_id={call_id}")
    
    # Get call from database
    call = db.query(AppointmentCall).filter(
        AppointmentCall.call_id == call_id,
        AppointmentCall.user_id == current_user.id
    ).first()
    if not call or not call.last_audio:
        print(f"Audio not found for call {call_id}")
        raise HTTPException(status_code=404, detail="Audio not found for this conversation")

    b64 = call.last_audio
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

# --- Twilio Webhook Endpoints for Phone Call Conversation ---

@app.post("/twilio/webhook/{call_id}")
async def twilio_webhook(call_id: str, db: Session = Depends(get_db)):
    """Handle Twilio webhook for call processing with Deepgram."""
    # Get call from database
    call = db.query(AppointmentCall).filter(AppointmentCall.call_id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Import TwiML
    from twilio.twiml.voice_response import VoiceResponse
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Initial greeting for appointment booking (without call_time)
    greeting = f"Hello! I'm calling on behalf of {call.patient_name} to schedule an appointment with Dr. {call.doctor_name} at {call.hospital_name}. Is this the correct number for appointment scheduling?"
    
    # Use Twilio's built-in Say for the first message to avoid initial delay
    response.say(greeting)
    
    # Gather speech input with extended timeout for Deepgram processing
    gather = response.gather(
        input="speech",
        action=f"/twilio/process_input/{call_id}",
        method="POST",
        timeout=30,  # Increased timeout to allow for TTS generation
        speech_timeout=5,  # Wait 5 seconds for speech to start
        speech_model="phone_call"
    )
    
    return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/process_input/{call_id}")
async def twilio_process_input(call_id: str, SpeechResult: Optional[str] = Form(None), db: Session = Depends(get_db)):
    """Process speech input from Twilio and generate LLM-powered response using Deepgram."""
    print(f"Processing input for call {call_id}, SpeechResult: {SpeechResult}")
    
    # Get call from database
    call = db.query(AppointmentCall).filter(AppointmentCall.call_id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Import TwiML
    from twilio.twiml.voice_response import VoiceResponse
    
    # Initialize services
    tts_service = TTSService(provider=os.getenv("TTS_PROVIDER", "deepgram"))
    
    response = VoiceResponse()
    
    if SpeechResult:
        # Get conversation history
        conversation_history = call.conversation_history or []
        
        # Process with LLM
        ai_response = process_conversation_with_llm(SpeechResult, call, db, conversation_history)
        print(f"AI Response: {ai_response}")
        
        # Convert response to speech using Deepgram and store it on the call record
        try:
            print(f"Generating TTS audio with Deepgram for: {ai_response[:50]}...")
            audio_base64 = tts_service.text_to_base64_audio(ai_response)
            call.last_audio = audio_base64
            call.updated_at = datetime.utcnow()
            db.commit()
            print(f"Deepgram TTS audio generated successfully, size: {len(audio_base64)} chars")
        except Exception as e:
            print(f"Deepgram TTS generation failed: {e}")
            # Fallback to Twilio's built-in TTS
            response.say(ai_response)
            # Continue with gather without custom audio
            if call.status != "appointment_booked":
                gather = response.gather(
                    input="speech",
                    action=f"/twilio/process_input/{call_id}",
                    method="POST",
                    timeout=30,
                    speech_timeout=5,
                    speech_model="phone_call"
                )
            else:
                response.say("Thank you for your assistance. Goodbye.")
                response.hangup()
            return Response(content=str(response), media_type="application/xml")

        # Play the audio response via a reachable URL (Twilio will fetch this URL)
        webhook_base = os.getenv('WEBHOOK_BASE_URL')
        if webhook_base:
            audio_url = f"{webhook_base}/twilio/audio/{call_id}"
            print(f"Playing Deepgram audio from URL: {audio_url}")
            response.play(audio_url)
        else:
            # If there's no public base URL, fall back to Twilio's Say
            print("No webhook base URL, falling back to Twilio Say")
            response.say(ai_response)
        
        # Continue gathering input unless appointment is booked
        if call.status != "appointment_booked":
            gather = response.gather(
                input="speech",
                action=f"/twilio/process_input/{call_id}",
                method="POST",
                timeout=30,  # Extended timeout
                speech_timeout=5,  # Clear speech timeout
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
        
        try:
            print("Generating fallback TTS audio with Deepgram...")
            audio_base64 = tts_service.text_to_base64_audio(ai_response)
            call.last_audio = audio_base64
            call.updated_at = datetime.utcnow()
            db.commit()
            print("Fallback Deepgram TTS audio generated successfully")
        except Exception as e:
            print(f"Fallback Deepgram TTS generation failed: {e}")
            # Just use Twilio's Say
            response.say(ai_response)
            gather = response.gather(
                input="speech",
                action=f"/twilio/process_input/{call_id}",
                method="POST",
                timeout=30,
                speech_timeout=5,
                speech_model="phone_call"
            )
            return Response(content=str(response), media_type="application/xml")
        
        # Store and serve fallback audio
        webhook_base = os.getenv('WEBHOOK_BASE_URL')
        if webhook_base:
            audio_url = f"{webhook_base}/twilio/audio/{call_id}"
            print(f"Playing fallback Deepgram audio from URL: {audio_url}")
            response.play(audio_url)
        else:
            print("No webhook base URL, using Twilio Say for fallback")
            response.say(ai_response)
        
        gather = response.gather(
            input="speech",
            action=f"/twilio/process_input/{call_id}",
            method="POST",
            timeout=30,  # Extended timeout
            speech_timeout=5,  # Clear speech timeout  
            speech_model="phone_call"
        )
    
    return Response(content=str(response), media_type="application/xml")

@app.get("/twilio/audio/{call_id}")
async def twilio_audio(call_id: str, db: Session = Depends(get_db)):
    """Serve last generated TTS audio for a call as WAV so Twilio can fetch and play it."""
    print(f"Twilio requesting audio for call_id={call_id}")
    
    # Get call from database
    call = db.query(AppointmentCall).filter(AppointmentCall.call_id == call_id).first()
    if not call or not call.last_audio:
        print(f"Audio not found for call {call_id}")
        raise HTTPException(status_code=404, detail="Audio not found for this call")

    b64 = call.last_audio
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
    print(f"Serving Deepgram audio for call {call_id} with media_type={media_type}, size={len(audio_bytes)}")
    return Response(content=audio_bytes, media_type=media_type, headers=headers)

@app.get("/test/conversation/{call_id}")
async def test_conversation(
    call_id: str, 
    current_user: User = Depends(get_current_user),
    text: str = "Hello, this is a test message for conversation", 
    db: Session = Depends(get_db)
):
    """Test endpoint to verify conversation flow with Deepgram"""
    import time
    start_time = time.time()
    
    try:
        # Get or create test call record
        call = db.query(AppointmentCall).filter(
            AppointmentCall.call_id == call_id,
            AppointmentCall.user_id == current_user.id
        ).first()
        if not call:
            call = AppointmentCall(
                call_id=call_id,
                user_id=current_user.id,
                patient_name="Test Patient",
                patient_phone="+1234567890",
                hospital_name="Test Hospital",
                hospital_phone="+1234567890",
                doctor_name="Test Doctor",
                call_time=datetime.fromtimestamp(int(time.time()) + 3600),  # 1 hour from now
                status="test"
            )
            db.add(call)
            db.commit()
            db.refresh(call)
        
        # Test conversation processing
        conversation_history = call.conversation_history or []
        ai_response = process_conversation_with_llm(text, call, db, conversation_history)
        
        # Test TTS generation
        tts_service = TTSService(provider=os.getenv("TTS_PROVIDER", "deepgram"))
        audio_base64 = tts_service.text_to_base64_audio(ai_response)
        
        call.last_audio = audio_base64
        call.updated_at = datetime.utcnow()
        db.commit()
        
        generation_time = time.time() - start_time
        
        return {
            "success": True,
            "generation_time_seconds": generation_time,
            "user_input": text,
            "ai_response": ai_response,
            "audio_size_chars": len(audio_base64),
            "provider": tts_service.provider,
            "audio_url": f"/conversation/{call_id}/audio"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "generation_time_seconds": time.time() - start_time
        }

@app.get("/")
async def root():
    return {"message": "Medical Appointment Booking API. Use /auth/send-otp and /auth/verify-otp for authentication, then use authenticated endpoints to manage appointments."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Medical Appointment Booking API"}

@app.get("/test/deepgram-tts")
async def test_deepgram_tts(current_user: User = Depends(get_current_user)):
    """Test endpoint to verify Deepgram TTS is working"""
    try:
        tts_service = TTSService(provider="deepgram")
        test_message = "Hello! This is a test of Deepgram text-to-speech for medical appointment booking. The voice quality is excellent for patient interactions."
        
        audio_data = tts_service.text_to_speech(test_message)
        audio_base64 = tts_service.text_to_base64_audio(test_message)
        
        return {
            "status": "success",
            "provider": "deepgram",
            "voice": os.getenv("TTS_VOICE", "aura-asteria-en"),
            "audio_size_bytes": len(audio_data),
            "audio_base64_size": len(audio_base64),
            "message": "Deepgram TTS is working correctly!"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "message": "Deepgram TTS test failed"
        }

# --- User Appointment Management Endpoints ---

@app.get("/appointments")
async def get_user_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all appointments for the authenticated user"""
    try:
        appointments = db.query(AppointmentCall).filter(AppointmentCall.user_id == current_user.id).all()
        return {
            "total": len(appointments),
            "user_id": current_user.id,
            "appointments": [
                AppointmentResponse(
                    call_id=appt.call_id,
                    patient_name=appt.patient_name,
                    patient_phone=appt.patient_phone,
                    hospital_name=appt.hospital_name,
                    hospital_phone=appt.hospital_phone,
                    doctor_name=appt.doctor_name,
                    call_time=int(appt.call_time.timestamp()),
                    appointment_state=appt.appointment_state.value,
                    status=appt.status,
                    retry_count=appt.retry_count,
                    max_retries=appt.max_retries,
                    created_at=int(appt.created_at.timestamp()),
                    updated_at=int(appt.updated_at.timestamp())
                )
                for appt in appointments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch appointments: {str(e)}")

@app.get("/appointments/{call_id}", response_model=AppointmentResponse)
async def get_user_appointment(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific appointment by call_id for the authenticated user"""
    call = db.query(AppointmentCall).filter(
        AppointmentCall.call_id == call_id,
        AppointmentCall.user_id == current_user.id
    ).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return AppointmentResponse(
        call_id=call.call_id,
        patient_name=call.patient_name,
        patient_phone=call.patient_phone,
        hospital_name=call.hospital_name,
        hospital_phone=call.hospital_phone,
        doctor_name=call.doctor_name,
        call_time=int(call.call_time.timestamp()),
        appointment_state=call.appointment_state.value,
        status=call.status,
        retry_count=call.retry_count,
        max_retries=call.max_retries,
        created_at=int(call.created_at.timestamp()),
        updated_at=int(call.updated_at.timestamp())
    )

@app.delete("/appointments/{call_id}")
async def delete_user_appointment(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific appointment for the authenticated user"""
    call = db.query(AppointmentCall).filter(
        AppointmentCall.call_id == call_id,
        AppointmentCall.user_id == current_user.id
    ).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    try:
        db.delete(call)
        db.commit()
        return {"message": f"Appointment {call_id} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete appointment: {str(e)}")

@app.patch("/appointments/{call_id}/state")
async def update_appointment_state(
    call_id: str,
    request: UpdateAppointmentStateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the state of a specific appointment for the authenticated user"""
    call = db.query(AppointmentCall).filter(
        AppointmentCall.call_id == call_id,
        AppointmentCall.user_id == current_user.id
    ).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    try:
        # Convert string to enum
        new_state = AppointmentState(request.appointment_state)
        call.appointment_state = new_state
        call.updated_at = datetime.utcnow()
        
        # Update status based on appointment state
        if new_state == AppointmentState.CONFIRMED:
            call.status = "confirmed"
        elif new_state == AppointmentState.REJECTED:
            call.status = "rejected" 
        elif new_state == AppointmentState.EXPIRED:
            call.status = "expired"
        
        db.commit()
        
        return {
            "message": f"Appointment state updated to {new_state.value}",
            "call_id": call_id,
            "new_state": new_state.value,
            "status": call.status
        }
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid appointment state. Valid states are: {[state.value for state in AppointmentState]}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update appointment state: {str(e)}")

@app.post("/appointments/{call_id}/retry")
async def retry_appointment_call(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry a failed appointment call (increments retry count)"""
    call = db.query(AppointmentCall).filter(
        AppointmentCall.call_id == call_id,
        AppointmentCall.user_id == current_user.id
    ).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if call.retry_count >= call.max_retries:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum retry attempts ({call.max_retries}) reached for this appointment"
        )
    
    try:
        call.retry_count += 1
        call.status = "retry_scheduled"
        call.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": f"Appointment call retry scheduled (attempt {call.retry_count}/{call.max_retries})",
            "call_id": call_id,
            "retry_count": call.retry_count,
            "max_retries": call.max_retries,
            "status": call.status
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to schedule retry: {str(e)}")

# --- Legacy Admin Endpoints (for backward compatibility) ---

@app.get("/admin/appointments")
async def get_all_appointments_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all appointments from all users (admin endpoint - requires authentication)"""
    try:
        appointments = db.query(AppointmentCall).all()
        return {
            "total": len(appointments),
            "appointments": [
                {
                    "call_id": appt.call_id,
                    "user_id": appt.user_id,
                    "patient_name": appt.patient_name,
                    "hospital_name": appt.hospital_name,
                    "doctor_name": appt.doctor_name,
                    "call_time": int(appt.call_time.timestamp()),
                    "appointment_state": appt.appointment_state.value,
                    "status": appt.status,
                    "retry_count": appt.retry_count,
                    "created_at": int(appt.created_at.timestamp()),
                    "updated_at": int(appt.updated_at.timestamp())
                }
                for appt in appointments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch appointments: {str(e)}")
