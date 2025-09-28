from pydantic import BaseModel

class CallScheduleRequest(BaseModel):
    patient_name: str
    patient_phone: str
    hospital_name: str
    hospital_phone: str
    doctor_name: str
    call_time: str  # ISO format string

class CallScheduleResponse(BaseModel):
    call_id: str
    status: str
    scheduled_time: str
