# Appoint-AI | Medical Appointment Booking Agent

An AI-powered appointment booking system with advanced speech capabilities using FastAPI, Deepgram, and OpenAI services.

## Outcome (A Mobile App Build with React Native to schedule & Manage Appointment Agent)
### Platform : Android/IOS

<img width="300" height="100%" alt="Screenshot_1760971433" src="https://github.com/user-attachments/assets/dd72039c-1208-4417-bdb0-16cae4a25f3c" />
<img width="300" height="100%" alt="Screenshot_1760971453" src="https://github.com/user-attachments/assets/53440e79-af95-4279-921d-b0ec7b07078f" />
<img width="300" height="100%" alt="Screenshot_1760971439" src="https://github.com/user-attachments/assets/03a08844-a288-404d-9e1c-77324996a278" />
<img width="300" height="100%" alt="Screenshot_1760971726" src="https://github.com/user-attachments/assets/bd23d15f-d293-4356-8496-912fc24ab82f" />


## Features

- 🎤 **Advanced Speech Processing**: Real-time speech-to-text and text-to-speech via Deepgram
- 💬 **Text Conversations**: Alternative text-based booking interface  
- 🤖 **AI-Powered**: Uses OpenAI GPT-4 for natural conversation
- � **Phone Authentication**: SMS-based OTP authentication system
- 📋 **Conversation Management**: Real-time speech processing without Twilio voice dependencies
- 🏥 **Medical Context Aware**: Handles appointment booking for hospitals and doctors
- 📞 **No Traditional Calling**: Direct conversation interface without phone system dependencies

## Technology Stack

- **Backend**: FastAPI
- **AI/LLM**: OpenAI GPT-4
- **Speech Services**: Deepgram (STT/TTS)
- **Authentication**: JWT with SMS OTP (Twilio for SMS only)
- **Database**: PostgreSQL with SQLAlchemy
- **Audio Processing**: Deepgram SDK

## Quick Start

### 1. Installation

```bash
# Clone or download the project
git clone <your-repo-url>
cd med-assist-agent

# Run setup script (recommended)
python setup.py

# OR install manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Update the `.env` file with your API keys:

```env
# Core services (required)
OPENAI_API_KEY=your_actual_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/medassist

# Authentication (for OTP SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token  
TWILIO_PHONE_NUMBER=+1234567890
JWT_SECRET_KEY=your_jwt_secret_key

# Server configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True

# Deepgram configuration
TTS_PROVIDER=deepgram
TTS_VOICE=aura-asteria-en
TTS_SPEED=1.0
```

### 3. Run the Application

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the server
python main.py
```

The API will be available at `http://localhost:8000`

## API Usage

### Authentication

#### 1. Send OTP

```bash
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890"}'
```

Response:
```json
{
  "success": true,
  "message": "OTP sent successfully to your phone number",
  "expires_in_minutes": 5
}
```

#### 2. Verify OTP and Get Token

```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "otp_code": "123456"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Phone number verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

### Appointment Management

#### Create Appointment

```bash
curl -X POST http://localhost:8000/appointments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patient_name": "John Doe",
    "patient_phone": "+1234567890", 
    "hospital_name": "City Hospital",
    "hospital_phone": "+1987654321",
    "doctor_name": "Dr. Smith",
    "call_time": 1696521600
  }'
```

### Conversation Flow

#### 1. Start Conversation

```bash
curl -X GET http://localhost:8000/start_conversation/YOUR_CALL_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2. Send Speech Input

```bash
curl -X POST http://localhost:8000/conversation/YOUR_CALL_ID/speak \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_data=BASE64_ENCODED_AUDIO"
```

#### 3. Send Text Input

```bash
curl -X POST http://localhost:8000/conversation/YOUR_CALL_ID/text \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "message=Hello, I need to book an appointment"
```

#### 4. Get AI Audio Response

```bash
curl -X GET http://localhost:8000/conversation/YOUR_CALL_ID/audio \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output response.wav
```

## Conversation Flow

The AI agent follows a structured conversation flow:

1. **Greeting**: Welcome and explanation
2. **Patient Information**: 
   - Full name
   - Age
   - Phone number
3. **Appointment Details**:
   - Doctor name
   - Hospital name  
   - Preferred time/date
   - Reason for visit
4. **Medical Information**:
   - Blood pressure conditions
   - Diabetes
   - Other medical conditions
5. **Confirmation**: 
   - Summary of all details
   - Confirmation number generation

## API Endpoints

### Authentication
- `POST /auth/send-otp` - Send OTP to phone number
- `POST /auth/verify-otp` - Verify OTP and get access token
- `GET /auth/me` - Get current user information

### Appointment Management  
- `POST /appointments` - Create new appointment
- `GET /appointments` - List user's appointments
- `GET /appointments/{call_id}` - Get specific appointment
- `DELETE /appointments/{call_id}` - Delete appointment
- `PATCH /appointments/{call_id}/state` - Update appointment state

### Conversation (Deepgram-powered)
- `GET /start_conversation/{call_id}` - Start conversation session
- `POST /conversation/{call_id}/speak` - Send speech input (base64 audio)
- `POST /conversation/{call_id}/text` - Send text input
- `GET /conversation/{call_id}/audio` - Get AI response audio

### Testing & Health
- `GET /test/conversation/{call_id}` - Test conversation flow
- `GET /test/deepgram-tts` - Test Deepgram TTS
- `GET /health` - Health check
- `GET /` - API information

## Data Models

### Patient Information
- Name, age, phone number
- Medical conditions (blood pressure, diabetes, etc.)
- Additional notes

### Appointment Details  
- Doctor name
- Hospital name
- Preferred time
- Reason for visit
- Urgency level

### Session Management
- Unique session IDs
- Conversation history
- Current step tracking
- Completion status

## Audio Support

### Supported Formats
- WAV (recommended for best quality)
- MP3, M4A, FLAC, OGG
- Maximum file size: 25MB

### Voice Configuration
Available TTS voices (OpenAI):
- `alloy` (default)
- `echo`
- `fable`
- `onyx`
- `nova`
- `shimmer`

## Environment Variables

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DEEPGRAM_API_KEY` | Deepgram API key for speech services (required) | - |
| `DATABASE_URL` | PostgreSQL connection string (required) | - |
| `TWILIO_ACCOUNT_SID` | Twilio SID for OTP SMS (required for auth) | - |
| `TWILIO_AUTH_TOKEN` | Twilio token for OTP SMS (required for auth) | - |
| `TWILIO_PHONE_NUMBER` | Twilio phone for OTP SMS (required for auth) | - |
| `JWT_SECRET_KEY` | JWT signing secret (required) | - |
| `APP_HOST` | Server host | `0.0.0.0` |
| `APP_PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `True` |
| `TTS_PROVIDER` | TTS provider (use 'deepgram') | `deepgram` |
| `TTS_VOICE` | Deepgram voice model | `aura-asteria-en` |
| `TTS_SPEED` | TTS speech speed | `1.0` |
| `AUDIO_SAMPLE_RATE` | Audio sample rate | `16000` |
| `AUDIO_CHANNELS` | Audio channels | `1` |

## Error Handling

- Automatic fallback from OpenAI to Google services
- Audio format conversion and validation
- Session timeout management  
- Graceful error responses

## Development

### Project Structure
```
med-assist-agent/
├── main.py              # Application entry point
├── api_endpoints.py     # FastAPI routes and endpoints
├── appointment_agent.py # LangGraph conversation logic
├── audio_services.py    # TTS and ASR services  
├── models.py           # Pydantic data models
├── requirements.txt    # Python dependencies
├── setup.py           # Setup and installation script
├── .env              # Environment configuration
└── README.md         # This file
```

### Adding New Features

1. **New Data Fields**: Update `models.py`
2. **Conversation Steps**: Modify `appointment_agent.py`
3. **API Endpoints**: Add to `api_endpoints.py`
## Appoint-AI — Medical Appointment Booking Agent

Lightweight FastAPI service that schedules and runs automated phone calls to hospitals to book appointments on behalf of patients. The service uses an LLM for conversational replies, TTS for spoken responses, and Twilio webhooks to place and manage phone calls.

This README reflects the current code in `api_endpoints.py`, `audio_services.py`, and `models.py`.

## Quick summary

- Schedule an automated appointment call: POST /schedule_call
- Initiate the call via Twilio: GET /trigger_call/{call_id}
- Twilio webhook to start/gather speech: POST /twilio/webhook/{call_id}
- Twilio webhook to process speech results: POST /twilio/process_input/{call_id}
- Serve last generated TTS audio for Twilio: GET /twilio/audio/{call_id}
- Root info: GET /

## Features

- Schedule appointment booking calls with patient & doctor details
- Initiate outbound calls through Twilio and handle Twilio webhooks
- LLM-powered conversational responses (OpenAI GPT; fallback to keyword logic)
- TTS (OpenAI TTS or gTTS fallback) and audio serving for Twilio to play
- ASR support (OpenAI Whisper preferred, Google Speech as fallback)
- Audio format conversion and validation (via pydub)
- In-memory call scheduling store (ephemeral; suitable for testing/prototyping)

## API Endpoints (current)

- POST /schedule_call
  - Description: Schedule an appointment call.
  - Request model: CallScheduleRequest
    - patient_name: string
    - patient_phone: string
    - hospital_name: string
    - hospital_phone: string
    - doctor_name: string
    - call_time: string (ISO datetime preferred)
  - Response model: CallScheduleResponse
    - call_id: string (uuid)
    - status: string ("scheduled")
    - scheduled_time: string

- GET /trigger_call/{call_id}
  - Description: Initiate the previously scheduled call through Twilio. Requires Twilio credentials and a public `WEBHOOK_BASE_URL` where Twilio can reach your app.
  - Response: JSON with call_id, status ("initiated"), and Twilio call SID on success.

- POST /twilio/webhook/{call_id}
  - Description: Twilio calls this endpoint to get TwiML when the call connects. The endpoint responds with a greeting and a speech gather to collect the hospital's spoken reply.
  - Note: This is designed to be called by Twilio (configured in the Twilio call creation `url` parameter).

- POST /twilio/process_input/{call_id}
  - Description: Twilio sends gathered speech (or the speech result) to this webhook. The app forwards the transcribed text to the LLM (or fallback logic), generates a TTS audio response, stores it on the call record, and returns TwiML to play the audio and continue gathering unless the appointment is booked.

- GET /twilio/audio/{call_id}
  - Description: Serves the last generated TTS audio as bytes (wav/mp3/ogg) so Twilio can fetch and play it.

- GET /
  - Description: Basic API information and usage hint.

## Models

Defined in `models.py`:

- CallScheduleRequest
  - patient_name: str
  - patient_phone: str
  - hospital_name: str
  - hospital_phone: str
  - doctor_name: str
  - call_time: str

- CallScheduleResponse
  - call_id: str
  - status: str
  - scheduled_time: str

## Quick examples

1) Schedule a call

```bash
curl -X POST http://localhost:8000/schedule_call \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "Jane Doe",
    "patient_phone": "+15551234567",
    "hospital_name": "City Hospital",
    "hospital_phone": "+15557654321",
    "doctor_name": "Smith",
    "call_time": "2025-10-01T10:00:00"
  }'
```

Response (example):

```json
{
  "call_id": "<uuid>",
  "status": "scheduled",
  "scheduled_time": "2025-10-01T10:00:00"
}
```

2) Trigger the call (will use Twilio credentials)

```bash
curl http://localhost:8000/trigger_call/<call_id>
```

3) Fetch last TTS audio (used by Twilio)

```bash
curl http://localhost:8000/twilio/audio/<call_id> --output last_response.wav
```

## Environment variables

Required for basic operation:

- OPENAI_API_KEY — required for LLM & ASR/TTS (if using OpenAI providers)
- TWILIO_ACCOUNT_SID — required to place calls via Twilio (for /trigger_call)
- TWILIO_AUTH_TOKEN — Twilio auth token
- TWILIO_PHONE_NUMBER — From number registered in Twilio
- WEBHOOK_BASE_URL — Public base URL for Twilio to reach your app (e.g., https://<your-host>)

Optional / defaults:

- APP_HOST (default: 0.0.0.0)
- APP_PORT (default: 8000)
- DEBUG (default: True)
- TTS_PROVIDER (default: gtts when not using OpenAI)
- TTS_VOICE (default: alloy when using OpenAI TTS)
- TTS_SPEED (default: 1.0)

Example .env snippet:

```
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1555xxxxxxx
WEBHOOK_BASE_URL=https://your-ngrok-or-host
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
TTS_PROVIDER=gtts
TTS_VOICE=alloy
TTS_SPEED=1.0
```

## Notes & recommendations

- The app currently stores scheduled calls in an in-memory dict (`scheduled_calls` in `api_endpoints.py`). For production use, persist calls to a database.
- Ensure `WEBHOOK_BASE_URL` is reachable by Twilio (use HTTPS in production). For local development use ngrok or a similar tunnel.
- Secure environment variables and restrict access to Twilio and OpenAI credentials.
- Consider rate limits and costs when using LLM/ASR/TTS providers in production.

## Development & running

1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` with required variables (see above)

3. Run the app

```bash
python main.py
```

Open API docs at: http://localhost:8000/docs

## Status

- Requirement: Revamp README with current endpoints and features — Done

If you'd like, I can also:

- Add a small example client script that schedules and triggers a call
- Add unit tests for the endpoints
- Wire a simple persistent store (SQLite) for scheduled calls
