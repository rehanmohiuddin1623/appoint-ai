from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import re
import time

# OTP Authentication Models
class SendOTPRequest(BaseModel):
    phone_number: str
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove spaces, dashes, and other common separators
        phone = re.sub(r'[\s\-\(\)]', '', v)
        
        # Check if it's a valid international format (+1234567890) or US format (1234567890)
        if not re.match(r'^\+?[1-9]\d{10,14}$', phone):
            raise ValueError('Invalid phone number format. Use international format like +1234567890')
        
        # Ensure it starts with + for international format
        if not phone.startswith('+'):
            phone = '+' + phone
            
        return phone

class SendOTPResponse(BaseModel):
    success: bool
    message: str
    expires_in_minutes: int = 5

class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp_code: str
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        phone = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[1-9]\d{10,14}$', phone):
            raise ValueError('Invalid phone number format')
        if not phone.startswith('+'):
            phone = '+' + phone
        return phone
    
    @validator('otp_code')
    def validate_otp_code(cls, v):
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP code must be exactly 6 digits')
        return v

class VerifyOTPResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: Optional[int] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int

# Conversation Models (Deepgram-based)
class StartConversationResponse(BaseModel):
    call_id: str
    status: str
    message: str
    details: dict

class ConversationSpeechRequest(BaseModel):
    audio_data: str  # base64 encoded audio

class ConversationTextRequest(BaseModel):
    message: str

class ConversationResponse(BaseModel):
    call_id: str
    user_input: str
    ai_response_text: str
    ai_response_audio: str  # base64 encoded
    conversation_complete: bool

# Appointment Models
class CallScheduleRequest(BaseModel):
    patient_name: str
    patient_phone: str
    hospital_name: str
    hospital_phone: str
    doctor_name: str
    call_time: int  # Epoch timestamp in seconds
    
    @validator('patient_phone', 'hospital_phone')
    def validate_phone_numbers(cls, v):
        phone = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[1-9]\d{10,14}$', phone):
            raise ValueError('Invalid phone number format')
        if not phone.startswith('+'):
            phone = '+' + phone
        return phone
    
    @validator('call_time')
    def validate_call_time(cls, v):
        if v <= 0:
            raise ValueError('call_time must be a positive epoch timestamp')
        # Check if timestamp is reasonable (not too far in past or future)
        import time
        current_time = int(time.time())
        if v < current_time - 86400:  # Not more than 1 day in the past
            raise ValueError('call_time cannot be more than 1 day in the past')
        if v > current_time + (365 * 86400):  # Not more than 1 year in the future
            raise ValueError('call_time cannot be more than 1 year in the future')
        return v

class CallScheduleResponse(BaseModel):
    call_id: str
    status: str
    appointment_state: str
    scheduled_time: int  # Epoch timestamp
    user_id: int

class AppointmentResponse(BaseModel):
    """Response model for appointment scheduling (includes call_time for cron job scheduling)"""
    call_id: str
    patient_name: str
    patient_phone: str
    hospital_name: str
    hospital_phone: str
    doctor_name: str
    call_time: int  # Epoch timestamp - ONLY for scheduling purposes
    appointment_state: str
    status: str
    retry_count: int
    max_retries: int
    created_at: int  # Epoch timestamp
    updated_at: int  # Epoch timestamp

class UpdateAppointmentStateRequest(BaseModel):
    appointment_state: str
    
    @validator('appointment_state')
    def validate_appointment_state(cls, v):
        valid_states = ['created', 'confirmed', 'rejected', 'expired']
        if v.lower() not in valid_states:
            raise ValueError(f'Invalid appointment state. Must be one of: {", ".join(valid_states)}')
        return v.lower()

class UserResponse(BaseModel):
    id: int
    phone_number: str
    is_verified: bool
    created_at: int  # Epoch timestamp
