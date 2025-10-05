import os
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from database import get_db, User
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Initialize Twilio client
try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except Exception as e:
    print(f"Warning: Twilio client initialization failed: {e}")
    twilio_client = None

# HTTP Bearer scheme for JWT tokens
security = HTTPBearer()

def generate_otp() -> str:
    """Generate a 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_sms(phone_number: str, otp_code: str) -> bool:
    """Send OTP code via Twilio SMS"""
    if not twilio_client:
        print("Error: Twilio client not initialized")
        return False
    
    try:
        message_body = f"Your Med-Assist verification code is: {otp_code}. This code expires in 5 minutes."
        
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        print(f"OTP SMS sent successfully. Message SID: {message.sid}")
        return True
        
    except TwilioException as e:
        print(f"Twilio error sending SMS: {e}")
        return False
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": int(user_id)}
    except JWTError:
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phone number not verified"
        )
    
    return user

def get_or_create_user(phone_number: str, db: Session) -> User:
    """Get existing user or create a new one"""
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        user = User(
            phone_number=phone_number,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

def initiate_otp_verification(phone_number: str, db: Session) -> dict:
    """Initiate OTP verification process"""
    # Get or create user
    user = get_or_create_user(phone_number, db)
    
    # Generate new OTP
    otp_code = generate_otp()
    otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # Reset OTP attempts if more than 1 hour has passed since last attempt
    if user.otp_expires_at and (datetime.utcnow() - user.otp_expires_at).total_seconds() > 3600:
        user.otp_attempts = 0
    
    # Check if user has exceeded OTP attempts
    if user.otp_attempts >= 5:
        time_since_last_attempt = datetime.utcnow() - (user.otp_expires_at or datetime.utcnow())
        if time_since_last_attempt.total_seconds() < 3600:  # 1 hour cooldown
            remaining_minutes = 60 - int(time_since_last_attempt.total_seconds() / 60)
            return {
                "success": False,
                "message": f"Too many OTP attempts. Please try again in {remaining_minutes} minutes."
            }
        else:
            # Reset attempts after cooldown
            user.otp_attempts = 0
    
    # Update user with new OTP
    user.otp_code = otp_code
    user.otp_expires_at = otp_expires_at
    user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Send OTP via SMS
        if send_otp_sms(phone_number, otp_code):
            return {
                "success": True,
                "message": "OTP sent successfully to your phone number"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send OTP. Please try again."
            }
            
    except Exception as e:
        db.rollback()
        print(f"Database error during OTP initiation: {e}")
        return {
            "success": False,
            "message": "An error occurred. Please try again."
        }

def verify_otp_code(phone_number: str, otp_code: str, db: Session) -> dict:
    """Verify OTP code and return access token if valid"""
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        return {
            "success": False,
            "message": "Phone number not found"
        }
    
    # Check if OTP has expired
    if not user.otp_expires_at or datetime.utcnow() > user.otp_expires_at:
        return {
            "success": False,
            "message": "OTP has expired. Please request a new one."
        }
    
    # Increment OTP attempts
    user.otp_attempts = (user.otp_attempts or 0) + 1
    
    # Check if OTP code matches
    if user.otp_code != otp_code:
        db.commit()  # Save the incremented attempt count
        
        remaining_attempts = 5 - user.otp_attempts
        if remaining_attempts <= 0:
            return {
                "success": False,
                "message": "Too many failed attempts. Please request a new OTP."
            }
        
        return {
            "success": False,
            "message": f"Invalid OTP code. {remaining_attempts} attempts remaining."
        }
    
    # OTP is valid - verify the user and clear OTP data
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "success": True,
            "message": "Phone number verified successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id
        }
        
    except Exception as e:
        db.rollback()
        print(f"Database error during OTP verification: {e}")
        return {
            "success": False,
            "message": "An error occurred during verification. Please try again."
        }

def validate_phone_number(phone_number: str) -> str:
    """Validate and format phone number"""
    import re
    
    # Remove spaces, dashes, and other common separators
    phone = re.sub(r'[\s\-\(\)]', '', phone_number)
    
    # Check if it's a valid international format
    if not re.match(r'^\+?[1-9]\d{10,14}$', phone):
        raise ValueError('Invalid phone number format. Use international format like +1234567890')
    
    # Ensure it starts with + for international format
    if not phone.startswith('+'):
        phone = '+' + phone
        
    return phone