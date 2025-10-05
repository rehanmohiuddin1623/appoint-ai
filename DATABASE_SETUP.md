# Med Assist Agent - Database Integration Setup

This guide will help you set up PostgreSQL database integration for the Med Assist Agent.

## Prerequisites

1. **PostgreSQL Server Running**: Make sure PostgreSQL is running on `localhost:5432`
2. **Database Access**: You'll need credentials for your PostgreSQL instance

## Setup Instructions

### 1. Install Dependencies

First, install the new PostgreSQL dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `sqlalchemy` - ORM for database operations
- `psycopg2-binary` - PostgreSQL adapter for Python
- `alembic` - Database migration tool

### 2. Configure Database URL

Update your `.env` file with your PostgreSQL credentials:

```bash
# Replace with your actual PostgreSQL credentials
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/medassist
```

Example:
```bash
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/medassist
```

### 3. Create Database

Create the database if it doesn't exist:

```bash
# Using psql command line
psql -U your_username -c "CREATE DATABASE medassist;"

# Or using Python script
python migrate.py create
```

### 4. Initialize Database Tables

Run the setup script to create tables:

```bash
python setup_db.py
```

Or use the migration script:

```bash
python migrate.py create
```

### 5. Verify Setup

Start the application:

```bash
python main.py
```

The application will now:
- ✅ Store appointments in PostgreSQL instead of memory
- ✅ Persist conversation history in the database
- ✅ Provide CRUD endpoints for appointment management

## New Database Features

### Database Schema

The `appointment_calls` table stores:
- `call_id` (Primary Key) - Unique identifier for each call
- `patient_name` - Patient's name
- `patient_phone` - Patient's phone number
- `hospital_name` - Hospital name
- `hospital_phone` - Hospital phone number
- `doctor_name` - Doctor's name
- `call_time` - Scheduled appointment time
- `status` - Call status (scheduled, initiated, completed, etc.)
- `twilio_call_sid` - Twilio call identifier
- `conversation_history` - JSON array of conversation messages
- `last_audio` - Base64 encoded audio for TTS
- `created_at` - Record creation timestamp
- `updated_at` - Last update timestamp

### New API Endpoints

- `GET /appointments` - List all appointments
- `GET /appointments/{call_id}` - Get specific appointment
- `DELETE /appointments/{call_id}` - Delete appointment
- `GET /appointments/status/{status}` - Filter by status

### Database Management Commands

```bash
# Create database and tables
python migrate.py create

# Reset database (CAUTION: Deletes all data)
python migrate.py reset

# Drop all tables
python migrate.py drop

# Test database connection
python setup_db.py
```

## Troubleshooting

### Connection Issues

1. **PostgreSQL not running**:
   ```bash
   # macOS with Homebrew
   brew services start postgresql
   
   # Linux with systemd
   sudo systemctl start postgresql
   ```

2. **Wrong credentials**:
   - Check your username and password in the DATABASE_URL
   - Verify you can connect with `psql -U username -d medassist`

3. **Database doesn't exist**:
   ```bash
   psql -U username -c "CREATE DATABASE medassist;"
   ```

4. **Permission issues**:
   - Make sure your user has CREATE/INSERT/UPDATE/DELETE permissions
   - Grant permissions: `GRANT ALL PRIVILEGES ON DATABASE medassist TO username;`

### Migration Issues

If you encounter table creation issues:

```bash
# Reset and recreate everything
python migrate.py reset
```

## Testing the Integration

1. **Schedule an appointment**:
   ```bash
   curl -X POST "http://localhost:8000/schedule_call" \
        -H "Content-Type: application/json" \
        -d '{
          "patient_name": "John Doe",
          "patient_phone": "+1234567890",
          "hospital_name": "General Hospital",
          "hospital_phone": "+1987654321",
          "doctor_name": "Dr. Smith",
          "call_time": "2025-10-05T10:00:00"
        }'
   ```

2. **View appointments**:
   ```bash
   curl "http://localhost:8000/appointments"
   ```

3. **Check specific appointment**:
   ```bash
   curl "http://localhost:8000/appointments/{call_id}"
   ```

The appointments are now persisted in PostgreSQL and will survive application restarts!

## Environment Variables Reference

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/medassist

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Twilio
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number

# Webhook
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io

# TTS
TTS_PROVIDER=deepgram
DEEPGRAM_API_KEY=your_deepgram_key
```