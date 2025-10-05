# Med Assist Agent - Docker Setup

This document provides instructions for running the Med Assist Agent as Docker containers.

## 🐳 Docker Setup

### Prerequisites

- Docker and Docker Compose installed on your system
- At least 2GB of available RAM
- Internet connection for downloading dependencies

### Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.docker .env
   ```

2. **Edit the `.env` file with your API keys:**
   ```bash
   # Required API Keys
   OPENAI_API_KEY=your_openai_api_key_here
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   
   # JWT Secret (change this!)
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
   
   # Optional: Twilio for OTP SMS
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

3. **Start the application:**
   ```bash
   ./docker.sh start
   ```
   
   Or manually:
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Database: localhost:5432 (user: medassist, password: medassist_password)

## 🛠 Management Commands

Use the convenient `docker.sh` script for managing the application:

### Basic Operations
```bash
./docker.sh start          # Start all services
./docker.sh stop           # Stop all services
./docker.sh restart        # Restart all services
./docker.sh status         # Show service status
./docker.sh logs          # Show all logs
./docker.sh logs app      # Show app logs only
```

### Database Operations
```bash
./docker.sh db:migrate     # Run database migrations
./docker.sh db:reset       # Reset database (WARNING: deletes data)
./docker.sh db:shell       # Open database shell
```

### Development
```bash
./docker.sh build          # Build Docker image
./docker.sh shell          # Open application shell
./docker.sh cleanup        # Remove containers and volumes
```

### Production
```bash
./docker.sh start:prod     # Start with nginx reverse proxy
```

## 📦 Container Services

The Docker setup includes:

1. **app** - Main FastAPI application (port 8000)
2. **postgres** - PostgreSQL database (port 5432)
3. **redis** - Redis cache (port 6379)
4. **nginx** - Reverse proxy (port 80/443, production only)

## 🔧 Configuration

### Environment Variables

The application uses these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DEEPGRAM_API_KEY` | Deepgram API key (required) | - |
| `DATABASE_URL` | PostgreSQL connection string | Set automatically |
| `JWT_SECRET_KEY` | JWT signing secret | Change in production |
| `TWILIO_ACCOUNT_SID` | Twilio account SID (optional) | - |
| `TWILIO_AUTH_TOKEN` | Twilio auth token (optional) | - |
| `TWILIO_PHONE_NUMBER` | Twilio phone number (optional) | - |
| `TTS_VOICE` | Deepgram TTS voice | aura-asteria-en |
| `TTS_SPEED` | TTS speech speed | 1.0 |
| `DEBUG` | Enable debug mode | False |

### Database Configuration

The PostgreSQL database is automatically configured with:
- **Database name:** medassist
- **Username:** medassist
- **Password:** medassist_password
- **Port:** 5432

Data is persisted in a Docker volume named `postgres_data`.

### Volumes

The setup creates persistent volumes for:
- `postgres_data` - Database files
- `redis_data` - Redis cache files
- `./logs` - Application logs (mounted from host)

## 🚀 Deployment

### Development
```bash
# Start development environment
./docker.sh start

# View logs in real-time
./docker.sh logs
```

### Production

1. **Configure environment:**
   ```bash
   # Update .env with production values
   DEBUG=False
   JWT_SECRET_KEY=your-secure-production-key
   WEBHOOK_BASE_URL=https://your-domain.com
   ```

2. **Start with nginx:**
   ```bash
   ./docker.sh start:prod
   ```

3. **Configure SSL (optional):**
   - Place SSL certificates in `nginx/ssl/`
   - Uncomment HTTPS configuration in `nginx/nginx.conf`

### Cloud Deployment

The containers can be deployed to various cloud platforms:

#### Docker Swarm
```bash
docker stack deploy -c docker-compose.yml med-assist
```

#### Kubernetes
Convert using Kompose:
```bash
kompose convert
kubectl apply -f .
```

#### Cloud Platforms
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform

## 🔍 Monitoring & Debugging

### Health Checks
All services include health checks:
```bash
# Check all services
./docker.sh status

# Manual health check
curl http://localhost:8000/health
```

### Logs
```bash
# All services
./docker.sh logs

# Specific service
./docker.sh logs app
./docker.sh logs postgres
./docker.sh logs redis

# Follow logs
docker-compose logs -f app
```

### Database Access
```bash
# Database shell
./docker.sh db:shell

# Or manually
docker-compose exec postgres psql -U medassist -d medassist
```

### Application Shell
```bash
# Application container shell
./docker.sh shell

# Run Python commands
docker-compose exec app python -c "print('Hello from container')"
```

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :5432
   
   # Stop conflicting services
   brew services stop postgresql  # macOS
   sudo systemctl stop postgresql  # Linux
   ```

2. **Permission errors:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   chmod +x docker.sh
   ```

3. **Database connection errors:**
   ```bash
   # Reset database
   ./docker.sh db:reset
   
   # Or recreate containers
   docker-compose down -v
   docker-compose up -d
   ```

4. **API key errors:**
   ```bash
   # Check environment variables
   docker-compose exec app env | grep API_KEY
   
   # Update .env file and restart
   ./docker.sh restart
   ```

### Performance Tuning

1. **Increase memory for PostgreSQL:**
   ```yaml
   # In docker-compose.yml under postgres service
   command: postgres -c shared_buffers=256MB -c max_connections=200
   ```

2. **Enable production optimizations:**
   ```bash
   # Set in .env
   DEBUG=False
   UVICORN_WORKERS=4
   ```

### Backup & Restore

```bash
# Backup database
docker-compose exec postgres pg_dump -U medassist medassist > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U medassist -d medassist
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [FastAPI with Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)

For more help, check the application logs or open an issue in the repository.