#!/bin/bash

# Med Assist Agent - VPS Auto Deployment Script
# This script pulls the latest Docker image and deploys to your VPS

set -e

# Configuration
DOCKER_IMAGE="rehanmohiuddin/med-assist-agent:latest"
APP_NAME="med-assist-agent"
DEPLOY_DIR="/opt/${APP_NAME}"
BACKUP_DIR="${DEPLOY_DIR}/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Med Assist Agent - VPS Auto Deploy${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Install Docker if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        print_status "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        usermod -aG docker $SUDO_USER 2>/dev/null || true
        rm get-docker.sh
        print_status "Docker installed successfully!"
    else
        print_status "Docker is already installed"
    fi
}

# Install Docker Compose if not present
install_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_status "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        print_status "Docker Compose installed successfully!"
    else
        print_status "Docker Compose is already installed"
    fi
}

# Create deployment directory structure
setup_directories() {
    print_status "Setting up deployment directories..."
    mkdir -p "${DEPLOY_DIR}"
    mkdir -p "${BACKUP_DIR}"
    mkdir -p "${DEPLOY_DIR}/logs"
    mkdir -p "${DEPLOY_DIR}/ssl"
    
    # Set proper ownership
    if [[ -n "$SUDO_USER" ]]; then
        chown -R $SUDO_USER:$SUDO_USER "${DEPLOY_DIR}"
    fi
}

# Create production environment file
create_env_file() {
    if [[ ! -f "${DEPLOY_DIR}/.env" ]]; then
        print_status "Creating environment file template..."
        cat > "${DEPLOY_DIR}/.env" << 'EOF'
# Med Assist Agent - Production Environment
# Please update these values with your actual configuration

# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Database Password (change this!)
POSTGRES_PASSWORD=secure_random_password_here

# JWT Secret (change this to a secure random string!)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-change-this

# Twilio Configuration (Optional - for OTP SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Webhook Configuration (update with your domain)
WEBHOOK_BASE_URL=https://your-domain.com

# Application Configuration
DEBUG=False
TTS_VOICE=aura-asteria-en
TTS_SPEED=1.0
EOF
        print_warning "Environment file created at ${DEPLOY_DIR}/.env"
        print_warning "Please edit this file with your actual configuration before running the deployment!"
        return 1
    fi
    return 0
}

# Create production docker-compose file
create_docker_compose() {
    print_status "Creating production docker-compose configuration..."
    cat > "${DEPLOY_DIR}/docker-compose.prod.yml" << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: med-assist-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: medassist
      POSTGRES_USER: medassist
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - med-assist-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U medassist -d medassist"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: med-assist-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - med-assist-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  app:
    image: rehanmohiuddin/med-assist-agent:latest
    container_name: med-assist-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://medassist:${POSTGRES_PASSWORD}@postgres:5432/medassist
      APP_HOST: 0.0.0.0
      APP_PORT: 8000
      DEBUG: ${DEBUG:-False}
      TTS_VOICE: ${TTS_VOICE:-aura-asteria-en}
      TTS_SPEED: ${TTS_SPEED:-1.0}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DEEPGRAM_API_KEY: ${DEEPGRAM_API_KEY}
      TWILIO_ACCOUNT_SID: ${TWILIO_ACCOUNT_SID}
      TWILIO_AUTH_TOKEN: ${TWILIO_AUTH_TOKEN}
      TWILIO_PHONE_NUMBER: ${TWILIO_PHONE_NUMBER}
      WEBHOOK_BASE_URL: ${WEBHOOK_BASE_URL}
    volumes:
      - ./logs:/app/logs
    networks:
      - med-assist-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: med-assist-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs:/var/log/nginx
    networks:
      - med-assist-network
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:

networks:
  med-assist-network:
    driver: bridge
EOF
}

# Create nginx configuration
create_nginx_config() {
    print_status "Creating nginx configuration..."
    cat > "${DEPLOY_DIR}/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    upstream app {
        server app:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    server {
        listen 80;
        server_name _;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy "strict-origin-when-cross-origin";

        # Rate limiting
        limit_req zone=api burst=50 nodelay;

        # Proxy to FastAPI app
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://app/health;
            access_log off;
        }

        # Deny access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }
    }

    # HTTPS configuration (uncomment and configure for production)
    # server {
    #     listen 443 ssl http2;
    #     server_name your-domain.com;
    #     
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #     
    #     ssl_protocols TLSv1.2 TLSv1.3;
    #     ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    #     ssl_prefer_server_ciphers off;
    #     ssl_session_cache shared:SSL:10m;
    #     ssl_session_timeout 10m;
    #     
    #     add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    #     
    #     location / {
    #         proxy_pass http://app;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #     }
    # }
}
EOF
}

# Backup existing database
backup_database() {
    if docker ps | grep -q med-assist-postgres; then
        print_status "Creating database backup..."
        BACKUP_FILE="${BACKUP_DIR}/backup-$(date +%Y%m%d-%H%M%S).sql"
        docker exec med-assist-postgres pg_dump -U medassist medassist > "$BACKUP_FILE"
        print_status "Database backup created: $BACKUP_FILE"
        
        # Keep only last 7 backups
        find "${BACKUP_DIR}" -name "backup-*.sql" -type f -mtime +7 -delete
    fi
}

# Deploy the application
deploy() {
    print_status "Starting deployment process..."
    cd "${DEPLOY_DIR}"
    
    # Load environment variables
    if [[ -f .env ]]; then
        set -a
        source .env
        set +a
    else
        print_error "Environment file not found. Please run setup first."
        exit 1
    fi
    
    # Validate required environment variables
    required_vars=("OPENAI_API_KEY" "DEEPGRAM_API_KEY" "POSTGRES_PASSWORD" "JWT_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" || "${!var}" == *"your_"* || "${!var}" == *"change"* ]]; then
            print_error "Please set $var in ${DEPLOY_DIR}/.env"
            exit 1
        fi
    done
    
    # Backup database if it exists
    backup_database
    
    # Pull latest images
    print_status "Pulling latest Docker images..."
    docker-compose -f docker-compose.prod.yml pull
    
    # Stop existing containers
    print_status "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans
    
    # Start new containers
    print_status "Starting updated containers..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    max_attempts=10
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_status "✅ Deployment successful! Application is healthy."
            break
        else
            if [[ $attempt -eq $max_attempts ]]; then
                print_error "❌ Deployment failed! Application health check failed after $max_attempts attempts."
                print_error "Check logs with: docker-compose -f ${DEPLOY_DIR}/docker-compose.prod.yml logs"
                exit 1
            fi
            print_warning "Health check failed, attempt $attempt/$max_attempts. Retrying in 10 seconds..."
            sleep 10
            ((attempt++))
        fi
    done
    
    # Clean up old images
    print_status "Cleaning up old Docker images..."
    docker image prune -f
    
    print_status "🚀 Deployment completed successfully!"
    
    # Show service information
    echo ""
    print_status "Service Information:"
    echo "  🌐 Application URL: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}'):8000"
    echo "  📊 API Documentation: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}'):8000/docs"
    echo "  🏥 Health Check: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}'):8000/health"
    echo "  📁 Deployment Directory: ${DEPLOY_DIR}"
    echo "  📝 Logs: docker-compose -f ${DEPLOY_DIR}/docker-compose.prod.yml logs"
}

# Setup initial installation
setup() {
    print_header
    check_permissions
    
    print_status "Setting up Med Assist Agent on VPS..."
    
    # Install requirements
    install_docker
    install_docker_compose
    
    # Setup directories
    setup_directories
    
    # Create configuration files
    if ! create_env_file; then
        print_error "Setup completed but environment file needs configuration."
        print_error "Please edit ${DEPLOY_DIR}/.env with your actual values and run 'deploy' command."
        exit 1
    fi
    
    create_docker_compose
    create_nginx_config
    
    print_status "✅ Setup completed successfully!"
    print_status "Next steps:"
    echo "  1. Edit ${DEPLOY_DIR}/.env with your API keys and configuration"
    echo "  2. Run: $0 deploy"
}

# Show service status
status() {
    print_header
    cd "${DEPLOY_DIR}" 2>/dev/null || {
        print_error "Application not installed. Run 'setup' first."
        exit 1
    }
    
    print_status "Service Status:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    print_status "Container Health:"
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status "✅ Application is healthy"
    else
        print_error "❌ Application health check failed"
    fi
}

# Show logs
logs() {
    cd "${DEPLOY_DIR}" 2>/dev/null || {
        print_error "Application not installed. Run 'setup' first."
        exit 1
    }
    
    docker-compose -f docker-compose.prod.yml logs -f "${1:-}"
}

# Stop services
stop() {
    cd "${DEPLOY_DIR}" 2>/dev/null || {
        print_error "Application not installed. Run 'setup' first."
        exit 1
    }
    
    print_status "Stopping services..."
    docker-compose -f docker-compose.prod.yml down
    print_status "Services stopped."
}

# Create systemd service for auto-start
create_systemd_service() {
    print_status "Creating systemd service..."
    cat > /etc/systemd/system/med-assist-agent.service << EOF
[Unit]
Description=Med Assist Agent
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${DEPLOY_DIR}
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable med-assist-agent
    print_status "Systemd service created and enabled."
}

# Show help
help() {
    print_header
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup         Initial setup and installation"
    echo "  deploy        Deploy/update the application"
    echo "  status        Show service status"
    echo "  stop          Stop all services"
    echo "  logs [service] Show logs"
    echo "  backup        Create database backup"
    echo "  systemd       Create systemd service for auto-start"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup          # Initial setup"
    echo "  $0 deploy         # Deploy application"
    echo "  $0 logs app       # Show application logs"
    echo "  $0 status         # Check status"
}

# Main command handling
case "${1:-help}" in
    setup)
        setup
        ;;
    deploy)
        deploy
        ;;
    status)
        status
        ;;
    stop)
        stop
        ;;
    logs)
        logs "$2"
        ;;
    backup)
        backup_database
        ;;
    systemd)
        create_systemd_service
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac