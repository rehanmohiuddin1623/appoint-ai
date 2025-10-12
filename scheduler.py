"""
Background Scheduler Service for Medical Appointment Calls

This module provides scheduling functionality to automatically trigger appointment calls
at the scheduled time using APScheduler.
"""

import os
import requests
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from sqlalchemy.orm import Session
from database import get_db, AppointmentCall
from typing import Optional

# Configure logging for scheduler
logging.basicConfig(level=logging.INFO)
scheduler_logger = logging.getLogger(__name__)

class MedicalAppointmentScheduler:
    """Handles scheduling of medical appointment calls"""
    
    def __init__(self):
        # Configure job stores and executors
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20)  # Max 20 concurrent jobs
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 3,
            'misfire_grace_time': 300  # 5 minutes grace period
        }
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'  # Use UTC for consistency
        )
        
        self.webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        self.scheduler_logger = scheduler_logger
        
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            self.scheduler_logger.info("Medical appointment scheduler started successfully")
        except Exception as e:
            self.scheduler_logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        try:
            self.scheduler.shutdown(wait=True)
            self.scheduler_logger.info("Medical appointment scheduler shut down successfully")
        except Exception as e:
            self.scheduler_logger.error(f"Error during scheduler shutdown: {e}")
    
    def schedule_appointment_call(self, call_id: str, call_time: datetime, user_id: int) -> bool:
        """
        Schedule an appointment call to be triggered at the specified time
        
        Args:
            call_id: Unique identifier for the appointment call
            call_time: When to trigger the call (datetime object)
            user_id: User who owns the appointment
            
        Returns:
            bool: True if successfully scheduled, False otherwise
        """
        try:
            # Create unique job ID
            job_id = f"appointment_call_{call_id}"
            
            # Schedule the job
            self.scheduler.add_job(
                func=self._execute_appointment_call,
                trigger=DateTrigger(run_date=call_time),
                args=[call_id, user_id],
                id=job_id,
                name=f"Appointment Call for {call_id}",
                replace_existing=True  # Replace if already exists
            )
            
            self.scheduler_logger.info(
                f"Scheduled appointment call {call_id} for {call_time} (Job ID: {job_id})"
            )
            return True
            
        except Exception as e:
            self.scheduler_logger.error(f"Failed to schedule appointment call {call_id}: {e}")
            return False
    
    def cancel_appointment_call(self, call_id: str) -> bool:
        """
        Cancel a scheduled appointment call
        
        Args:
            call_id: Unique identifier for the appointment call
            
        Returns:
            bool: True if successfully cancelled, False otherwise
        """
        try:
            job_id = f"appointment_call_{call_id}"
            
            # Try to remove the job
            self.scheduler.remove_job(job_id)
            self.scheduler_logger.info(f"Cancelled scheduled appointment call {call_id}")
            return True
            
        except Exception as e:
            self.scheduler_logger.warning(f"Could not cancel appointment call {call_id}: {e}")
            return False
    
    def _execute_appointment_call(self, call_id: str, user_id: int):
        """
        Execute the appointment call by triggering the start_conversation endpoint
        
        Args:
            call_id: Unique identifier for the appointment call
            user_id: User who owns the appointment
        """
        try:
            self.scheduler_logger.info(f"Executing scheduled appointment call {call_id}")
            
            # First, verify the appointment still exists and is valid
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                call = db.query(AppointmentCall).filter(
                    AppointmentCall.call_id == call_id,
                    AppointmentCall.user_id == user_id
                ).first()
                
                if not call:
                    self.scheduler_logger.warning(
                        f"Appointment call {call_id} not found or invalid user {user_id}"
                    )
                    return
                
                if call.status in ["completed", "cancelled", "failed"]:
                    self.scheduler_logger.info(
                        f"Appointment call {call_id} has status {call.status}, skipping execution"
                    )
                    return
                
                # Update status to indicate automated execution
                call.status = "auto_initiated"
                call.updated_at = datetime.utcnow()
                db.commit()
                
            finally:
                db.close()
            
            # Get user token for authentication (we'll need to handle this differently)
            # For now, we'll make a direct call to the internal start_conversation function
            self._trigger_start_conversation_internal(call_id, user_id)
            
        except Exception as e:
            self.scheduler_logger.error(f"Failed to execute appointment call {call_id}: {e}")
            
            # Update call status to failed
            try:
                db_gen = get_db()
                db = next(db_gen)
                try:
                    call = db.query(AppointmentCall).filter(
                        AppointmentCall.call_id == call_id,
                        AppointmentCall.user_id == user_id
                    ).first()
                    
                    if call:
                        call.status = "auto_failed"
                        call.updated_at = datetime.utcnow()
                        db.commit()
                        
                finally:
                    db.close()
            except Exception as db_error:
                self.scheduler_logger.error(f"Failed to update call status: {db_error}")
    
    def _trigger_start_conversation_internal(self, call_id: str, user_id: int):
        """
        Trigger the start_conversation logic internally without going through HTTP
        
        Args:
            call_id: Unique identifier for the appointment call
            user_id: User who owns the appointment
        """
        try:
            from twilio.rest import Client
            
            # Get environment variables
            twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
            webhook_base_url = os.getenv("WEBHOOK_BASE_URL")
            
            if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number, webhook_base_url]):
                raise Exception("Missing Twilio or webhook configuration")
            
            # Get call details from database
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                call = db.query(AppointmentCall).filter(
                    AppointmentCall.call_id == call_id,
                    AppointmentCall.user_id == user_id
                ).first()
                
                if not call:
                    raise Exception(f"Call {call_id} not found")
                
                # Initialize Twilio client
                twilio_client = Client(twilio_account_sid, twilio_auth_token)
                
                # Place outbound call to hospital
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
                
                self.scheduler_logger.info(
                    f"Successfully initiated scheduled call {call_id} "
                    f"to {call.hospital_phone} (Twilio SID: {twilio_call.sid})"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            self.scheduler_logger.error(f"Failed to trigger start_conversation for {call_id}: {e}")
            raise
    
    def get_scheduled_jobs(self) -> list:
        """Get list of currently scheduled jobs"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                if job.id.startswith("appointment_call_"):
                    call_id = job.id.replace("appointment_call_", "")
                    jobs.append({
                        "call_id": call_id,
                        "job_id": job.id,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                        "name": job.name
                    })
            return jobs
        except Exception as e:
            self.scheduler_logger.error(f"Failed to get scheduled jobs: {e}")
            return []
    
    def reschedule_appointment_call(self, call_id: str, new_call_time: datetime, user_id: int) -> bool:
        """
        Reschedule an existing appointment call
        
        Args:
            call_id: Unique identifier for the appointment call
            new_call_time: New time to trigger the call
            user_id: User who owns the appointment
            
        Returns:
            bool: True if successfully rescheduled, False otherwise
        """
        try:
            # Cancel existing job
            self.cancel_appointment_call(call_id)
            
            # Schedule new job
            return self.schedule_appointment_call(call_id, new_call_time, user_id)
            
        except Exception as e:
            self.scheduler_logger.error(f"Failed to reschedule appointment call {call_id}: {e}")
            return False

# Global scheduler instance
appointment_scheduler: Optional[MedicalAppointmentScheduler] = None

def get_scheduler() -> MedicalAppointmentScheduler:
    """Get the global scheduler instance"""
    global appointment_scheduler
    if appointment_scheduler is None:
        appointment_scheduler = MedicalAppointmentScheduler()
    return appointment_scheduler

def init_scheduler():
    """Initialize and start the scheduler"""
    global appointment_scheduler
    try:
        appointment_scheduler = MedicalAppointmentScheduler()
        appointment_scheduler.start()
        return True
    except Exception as e:
        scheduler_logger.error(f"Failed to initialize scheduler: {e}")
        return False

def shutdown_scheduler():
    """Shutdown the scheduler"""
    global appointment_scheduler
    if appointment_scheduler:
        appointment_scheduler.shutdown()
        appointment_scheduler = None