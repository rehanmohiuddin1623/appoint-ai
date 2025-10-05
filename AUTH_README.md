# Med-Assist Agent - User Authentication System

This document describes the phone number-based OTP authentication system implemented for the Med-Assist appointment booking agent.

## 🔐 Authentication Overview

The system uses **phone number-based OTP (One-Time Password)** authentication via Twilio SMS, eliminating the need for email and password management.

### Key Features
- ✅ Phone number validation with international format support
- ✅ 6-digit OTP codes with 5-minute expiration
- ✅ Rate limiting (5 attempts per hour)
- ✅ JWT token-based session management (30-day expiration)
- ✅ User-specific appointment management
- ✅ Appointment state management (CREATED, CONFIRMED, REJECTED, EXPIRED)
- ✅ Retry logic for failed calls (configurable, default 3 attempts)

## 🚀 Quick Start

### 1. Environment Setup

Add these variables to your `.env` file:

```bash
# Existing variables
DATABASE_URL=postgresql://username:password@localhost:5432/medassist
OPENAI_API_KEY=your_openai_api_key

# Twilio Configuration (for OTP SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Optional Webhook URL (for Twilio callbacks)
WEBHOOK_BASE_URL=https://your-domain.com
```

### 2. Database Migration

Run the migration script to update your database schema:

```bash
python migrate_to_auth.py
```

**⚠️ Important**: Backup your database before running migration!

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Server

```bash
python main.py
```

## 📱 Authentication Flow

### Step 1: Send OTP
```bash
POST /auth/send-otp
Content-Type: application/json

{
  "phone_number": "+1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully to your phone number",
  "expires_in_minutes": 5
}
```

### Step 2: Verify OTP
```bash
POST /auth/verify-otp
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Phone number verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

### Step 3: Use Bearer Token
For all subsequent API calls, include the token in the Authorization header:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📅 Appointment Management API

All appointment endpoints now require authentication and are user-specific.

### Create Appointment
```bash
POST /appointments
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_name": "John Doe",
  "patient_phone": "+1234567890",
  "hospital_name": "City Hospital",
  "hospital_phone": "+1987654321",
  "doctor_name": "Dr. Smith",
  "call_time": "2025-10-15T14:30:00"
}
```

### Get User's Appointments
```bash
GET /appointments
Authorization: Bearer <token>
```

### Get Specific Appointment
```bash
GET /appointments/{call_id}
Authorization: Bearer <token>
```

### Delete Appointment
```bash
DELETE /appointments/{call_id}
Authorization: Bearer <token>
```

### Update Appointment State
```bash
PATCH /appointments/{call_id}/state
Authorization: Bearer <token>
Content-Type: application/json

{
  "appointment_state": "confirmed"
}
```

Valid states: `created`, `confirmed`, `rejected`, `expired`

### Retry Failed Call
```bash
POST /appointments/{call_id}/retry
Authorization: Bearer <token>
```

## 🔄 Appointment States

| State | Description |
|-------|-------------|
| `CREATED` | Initial state when appointment is scheduled |
| `CONFIRMED` | Hospital confirmed the appointment |
| `REJECTED` | Hospital rejected/denied the appointment |
| `EXPIRED` | Appointment time has passed without confirmation |

## 🔁 Retry Logic

- **Default**: 3 retry attempts per appointment
- **Configurable**: `max_retries` field in appointment record
- **Status**: Tracks current `retry_count`
- **Automatic**: Can be triggered via API or scheduled jobs

## 🛡️ Security Features

### Phone Number Validation
- International format required (`+1234567890`)
- Automatic formatting and validation
- Prevents invalid/malformed numbers

### OTP Security
- 6-digit random codes
- 5-minute expiration
- Rate limiting (5 attempts per hour)
- Secure generation using Python's `secrets` module

### JWT Tokens
- 30-day expiration (configurable)
- HS256 algorithm
- Includes user ID in payload
- Bearer token authentication

### API Security
- All appointment endpoints require authentication
- User isolation (users can only access their own appointments)
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy ORM

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR UNIQUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    otp_code VARCHAR,
    otp_expires_at TIMESTAMP,
    otp_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Updated Appointment Calls Table
```sql
CREATE TABLE appointment_calls (
    call_id VARCHAR PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    patient_name VARCHAR NOT NULL,
    patient_phone VARCHAR NOT NULL,
    hospital_name VARCHAR NOT NULL,
    hospital_phone VARCHAR NOT NULL,
    doctor_name VARCHAR NOT NULL,
    call_time TIMESTAMP NOT NULL,
    appointment_state appointmentstate DEFAULT 'created',
    status VARCHAR DEFAULT 'scheduled',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    twilio_call_sid VARCHAR,
    conversation_history JSON DEFAULT '[]',
    last_audio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 Error Handling

### Common Error Responses

**Invalid Phone Number:**
```json
{
  "detail": "Invalid phone number format. Use international format like +1234567890"
}
```

**OTP Expired:**
```json
{
  "detail": "OTP has expired. Please request a new one."
}
```

**Invalid OTP:**
```json
{
  "detail": "Invalid OTP code. 3 attempts remaining."
}
```

**Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Rate Limited:**
```json
{
  "detail": "Too many OTP attempts. Please try again in 45 minutes."
}
```

## 📈 Monitoring & Analytics

### Key Metrics to Track
- OTP delivery success rate
- Authentication success rate
- User verification completion rate
- Appointment creation/completion rates
- Call retry statistics

### Logging
The system logs important events:
- OTP generation and delivery
- Authentication attempts
- Appointment state changes
- Call retry attempts
- Error conditions

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT tokens | (required) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | 43200 (30 days) |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | (required) |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | (required) |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | (required) |

### Customizable Settings in Code
- OTP length (default: 6 digits)
- OTP expiration (default: 5 minutes)
- Max OTP attempts (default: 5 per hour)
- JWT expiration (default: 30 days)
- Max call retries (default: 3)

## 🚀 Deployment Considerations

### Production Checklist
- [ ] Use strong, unique `JWT_SECRET_KEY`
- [ ] Configure proper Twilio account with SMS capabilities
- [ ] Set up database backups
- [ ] Configure HTTPS for API endpoints
- [ ] Set up monitoring and alerting
- [ ] Test OTP delivery in target regions
- [ ] Configure rate limiting at infrastructure level
- [ ] Set up proper logging and log rotation

### Scaling
- Consider Redis for OTP storage in high-traffic scenarios
- Implement distributed rate limiting
- Use connection pooling for database
- Set up load balancing for multiple instances

## 🤝 Migration from Previous Version

The migration script (`migrate_to_auth.py`) handles:
- Creating new User table
- Updating AppointmentCall schema
- Preserving existing appointment data
- Creating default user for legacy appointments
- Adding proper indexes for performance

### Legacy Endpoint Support
Some legacy endpoints remain for backward compatibility:
- `/schedule_call` (creates appointments with default user)
- `/admin/appointments` (admin view of all appointments)

## 📞 Support

For issues or questions:
1. Check the error logs in the application
2. Verify Twilio configuration and SMS delivery
3. Ensure database migration completed successfully
4. Check phone number format compliance

---

**Security Note**: Always use HTTPS in production and keep your JWT secret key secure!