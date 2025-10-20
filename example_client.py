#!/usr/bin/env python3
"""
Example script showing how to use the new Deepgram-based conversation system
"""

import requests
import base64
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MedAssistClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
    
    def authenticate(self, phone_number, otp_code=None):
        """Authenticate with phone number and OTP"""
        if not otp_code:
            # Step 1: Send OTP
            response = self.session.post(
                f"{self.base_url}/auth/send-otp",
                json={"phone_number": phone_number}
            )
            if response.status_code == 200:
                print(f"✅ OTP sent to {phone_number}")
                print("📱 Please check your phone and enter the OTP code.")
                return False
            else:
                print(f"❌ Failed to send OTP: {response.text}")
                return False
        else:
            # Step 2: Verify OTP
            response = self.session.post(
                f"{self.base_url}/auth/verify-otp",
                json={
                    "phone_number": phone_number,
                    "otp_code": otp_code
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                print(f"✅ Authenticated successfully! User ID: {data['user_id']}")
                return True
            else:
                print(f"❌ Authentication failed: {response.text}")
                return False
    
    def create_appointment(self, patient_name, hospital_name, doctor_name, 
                          patient_phone="+1234567890", hospital_phone="+1987654321"):
        """Create a new appointment"""
        if not self.token:
            print("❌ Not authenticated. Please authenticate first.")
            return None
        
        # Use current time + 1 hour for call_time (for scheduling purposes only)
        call_time = int(time.time()) + 3600
        
        response = self.session.post(
            f"{self.base_url}/appointments",
            json={
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "hospital_name": hospital_name,
                "hospital_phone": hospital_phone,
                "doctor_name": doctor_name,
                "call_time": call_time
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            call_id = data["call_id"]
            print(f"✅ Appointment created! Call ID: {call_id}")
            return call_id
        else:
            print(f"❌ Failed to create appointment: {response.text}")
            return None
    
    def start_conversation(self, call_id):
        """Start a conversation session"""
        response = self.session.get(f"{self.base_url}/start_conversation/{call_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conversation started: {data['message']}")
            return True
        else:
            print(f"❌ Failed to start conversation: {response.text}")
            return False
    
    def send_text_message(self, call_id, message):
        """Send a text message in the conversation"""
        response = self.session.post(
            f"{self.base_url}/conversation/{call_id}/text",
            data={"message": message}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 AI Response: {data['ai_response_text']}")
            print(f"🔊 Audio available: {len(data['ai_response_audio'])} chars")
            print(f"✅ Conversation complete: {data['conversation_complete']}")
            return data
        else:
            print(f"❌ Failed to send message: {response.text}")
            return None
    
    def get_audio_response(self, call_id, save_path="ai_response.wav"):
        """Get the latest AI audio response"""
        response = self.session.get(f"{self.base_url}/conversation/{call_id}/audio")
        
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"🔊 Audio saved to {save_path}")
            return True
        else:
            print(f"❌ Failed to get audio: {response.text}")
            return False
    
    def get_user_info(self):
        """Get current user information including medical details"""
        if not self.token:
            print("❌ Not authenticated. Please authenticate first.")
            return None
        
        response = self.session.get(f"{self.base_url}/auth/me")
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User information retrieved:")
            print(f"   📱 Phone: {user_data['phone_number']}")
            print(f"   👤 Name: {user_data.get('full_name', 'Not set')}")
            print(f"   🩸 Blood Pressure: {user_data.get('blood_pressure', 'Not set')}")
            print(f"   🍯 Blood Sugar (avg without tablets): {user_data.get('blood_sugar_avg_without_tablets', 'Not set')}")
            print(f"   🅱️ Blood Group: {user_data.get('blood_group', 'Not set')}")
            print(f"   🦋 TSH Thyroid: {user_data.get('tsh_thyroid_value', 'Not set')}")
            print(f"   ⚖️ Weight: {user_data.get('weight', 'Not set')}")
            return user_data
        else:
            print(f"❌ Failed to get user info: {response.text}")
            return None
    
    def update_medical_details(self, full_name=None, blood_pressure=None, 
                              blood_sugar=None, blood_group=None, 
                              tsh_thyroid=None, weight=None):
        """Update user medical details including weight"""
        if not self.token:
            print("❌ Not authenticated. Please authenticate first.")
            return False
        
        # Build update payload with only non-None values
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        if blood_pressure is not None:
            update_data["blood_pressure"] = blood_pressure
        if blood_sugar is not None:
            update_data["blood_sugar_avg_without_tablets"] = blood_sugar
        if blood_group is not None:
            update_data["blood_group"] = blood_group
        if tsh_thyroid is not None:
            update_data["tsh_thyroid_value"] = tsh_thyroid
        if weight is not None:
            update_data["weight"] = weight
        
        if not update_data:
            print("❌ No data provided for update")
            return False
        
        response = self.session.post(f"{self.base_url}/auth/me", json=update_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Medical details updated successfully!")
            print("📋 Updated details:")
            for key, value in result["medical_details"].items():
                if value:
                    print(f"   {key}: {value}")
            return True
        else:
            print(f"❌ Failed to update medical details: {response.text}")
            return False

def example_conversation():
    """Example conversation flow"""
    print("🏥 Med-Assist Conversation Example")
    print("=" * 40)
    
    client = MedAssistClient()
    
    # Step 1: Authentication
    phone_number = input("📱 Enter your phone number (e.g., +1234567890): ")
    
    # Send OTP
    if not client.authenticate(phone_number):
        return
    
    # Get OTP from user
    otp_code = input("🔢 Enter the OTP code you received: ")
    if not client.authenticate(phone_number, otp_code):
        return
    
    # Step 2: Create appointment
    print("\\n📅 Creating appointment...")
    patient_name = input("👤 Patient name: ") or "John Doe"
    hospital_name = input("🏥 Hospital name: ") or "City General Hospital"
    doctor_name = input("👨‍⚕️ Doctor name: ") or "Dr. Smith"
    
    call_id = client.create_appointment(patient_name, hospital_name, doctor_name)
    if not call_id:
        return
    
    # Step 3: Start conversation
    print("\\n💬 Starting conversation...")
    if not client.start_conversation(call_id):
        return
    
    # Step 4: Interactive conversation
    print("\\n🗣️ You can now chat with the AI assistant!")
    print("Type 'quit' to end the conversation\\n")
    
    while True:
        user_message = input("You: ")
        if user_message.lower() in ['quit', 'exit', 'bye']:
            break
        
        response = client.send_text_message(call_id, user_message)
        if response and response.get('conversation_complete'):
            print("🎉 Appointment booking completed!")
            break
    
    # Step 5: Get final audio response
    print("\\n🔊 Getting final audio response...")
    client.get_audio_response(call_id)
    
    print("\\n✅ Example completed!")

def quick_test():
    """Quick test without user input"""
    print("🧪 Quick Test Mode")
    print("=" * 20)
    
    client = MedAssistClient()
    
    # Note: This requires manual OTP entry
    print("📝 For quick testing, you'll need to:")
    print("1. Set up authentication manually")
    print("2. Use the test endpoint")
    
    # Test the conversation endpoint directly
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        print("✅ API is running")
    else:
        print("❌ API is not accessible")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        example_conversation()