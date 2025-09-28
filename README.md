# Appoint-AI | AI Agent

An AI-powered appointment booking system with voice support using FastAPI, LangGraph, and OpenAI services.

## Features

- 🎤 **Voice Interaction**: Book appointments using natural speech
- 💬 **Text Chat**: Alternative text-based booking interface  
- 🤖 **AI-Powered**: Uses OpenAI GPT-4 for natural conversation
- 🔄 **Conversation Flow**: LangGraph manages multi-step booking process
- 📋 **Complete Information Gathering**: Collects patient details, appointment preferences, and medical conditions
- 🏥 **Medical Context Aware**: Handles medical conditions like blood pressure, diabetes
- 📞 **Receptionist Simulation**: Natural conversation flow like calling a doctor's office

## Technology Stack

- **Backend**: FastAPI
- **AI/LLM**: OpenAI GPT-4
- **Conversation Management**: LangGraph
- **Text-to-Speech**: OpenAI TTS (with Google TTS fallback)
- **Audio Processing**: PyAudio, pydub

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

Update the `.env` file with your OpenAI API key:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
TTS_PROVIDER=openai
TTS_VOICE=alloy
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

### Start a Session

```bash
curl -X POST http://localhost:8000/session/start
```

Response:
```json
{
  "session_id": "uuid-here",
  "message": "Hello! I'm here to help you book a medical appointment.",
  "status": "started"
}
```

### Text Chat

```bash
curl -X POST http://localhost:8000/chat/text \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to book an appointment",
    "session_id": "your-session-id"
  }'
```

### Voice Chat

```bash
curl -X POST http://localhost:8000/chat/voice \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64-encoded-audio",
    "session_id": "your-session-id",
    "format": "wav"
  }'
```

### Upload Audio File

```bash
curl -X POST http://localhost:8000/chat/voice/upload \
  -F "file=@audio.wav" \
  -F "session_id=your-session-id"
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

- `GET /` - API information
- `GET /health` - Health check
- `POST /session/start` - Start new conversation session
- `GET /session/{session_id}` - Get session state
- `POST /chat/text` - Text-based conversation
- `POST /chat/voice` - Voice-based conversation
- `POST /chat/voice/upload` - Upload audio file
- `GET /appointment/{session_id}/summary` - Get appointment summary
- `DELETE /session/{session_id}` - End session
- `GET /sessions/active` - List active sessions (debug)

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

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `APP_HOST` | Server host | `0.0.0.0` |
| `APP_PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `True` |
| `TTS_PROVIDER` | TTS provider | `openai` |
| `TTS_VOICE` | TTS voice | `alloy` |
| `TTS_SPEED` | TTS speed | `1.0` |
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
