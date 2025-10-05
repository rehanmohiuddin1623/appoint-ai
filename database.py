import os
from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import json
import enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medassist")

# For psycopg3, we need to use the proper driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enum for appointment states
class AppointmentState(enum.Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to appointments
    appointments = relationship("AppointmentCall", back_populates="user")

class AppointmentCall(Base):
    __tablename__ = "appointment_calls"
    
    call_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Appointment scheduling information (for cron jobs)
    patient_name = Column(String, nullable=False)
    patient_phone = Column(String, nullable=False)
    hospital_name = Column(String, nullable=False)
    hospital_phone = Column(String, nullable=False)
    doctor_name = Column(String, nullable=False)
    call_time = Column(DateTime, nullable=False)  # For scheduling automation only
    appointment_state = Column(Enum(AppointmentState), default=AppointmentState.CREATED)
    
    # Call management (scheduling system)
    status = Column(String, default="scheduled")  # scheduled, conversation_started, completed, failed
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Legacy field for external call systems (scheduling only)
    twilio_call_sid = Column(String, nullable=True)  # Only used for scheduled call tracking
    
    # Conversation data (Deepgram-based)
    conversation_history = Column(JSON, default=list)  # Real-time conversation tracking
    last_audio = Column(Text, nullable=True)  # Latest TTS audio from Deepgram
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="appointments")

def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database and create tables"""
    try:
        create_tables()
        print("Database tables created successfully")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False