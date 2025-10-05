# VPS Deployment Guide

This guide helps you deploy the Med Assist Agent to your VPS using Docker and automated scripts.

## 🚀 Quick Deployment (Recommended)

### Option 1: One-Line Install
Run this command on your VPS as root:

```bash
curl -fsSL https://raw.githubusercontent.com/rehanmohiuddin1623/appoint-ai/production/deploy/quick-install.sh | sudo bash
```

### Option 2: Manual Setup

1. **Download the deployment script:**
   ```bash
   wget https://raw.githubusercontent.com/rehanmohiuddin1623/appoint-ai/production/deploy/vps-deploy.sh
   chmod +x vps-deploy.sh
   ```

2. **Run initial setup:**
   ```bash
   sudo ./vps-deploy.sh setup
   ```

3. **Configure environment:**
   ```bash
   sudo nano /opt/med-assist-agent/.env
   ```

4. **Deploy the application:**
   ```bash
   sudo ./vps-deploy.sh deploy
   ```

## 📋 Prerequisites

- Ubuntu 18.04+ / CentOS 7+ / Debian 9+
- 2GB+ RAM recommended
- 20GB+ disk space
- Root or sudo access
- Internet connection

## 🔧 Configuration

### Required Environment Variables

Edit `/opt/med-assist-agent/.env` with your configuration:

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-key-here
DEEPGRAM_API_KEY=your-deepgram-key-here

# Database Password (change this!)
POSTGRES_PASSWORD=your-secure-database-password

# JWT Secret (change this!)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key

# Twilio (Optional - for OTP SMS)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number

# Your domain/IP
WEBHOOK_BASE_URL=https://your-domain.com
```

## 🛠 Management Commands

Once installed, use these commands to manage your deployment:

```bash
# Deploy/update application
sudo /opt/med-assist-agent/vps-deploy.sh deploy

# Check status
sudo /opt/med-assist-agent/vps-deploy.sh status

# View logs
sudo /opt/med-assist-agent/vps-deploy.sh logs

# Stop services
sudo /opt/med-assist-agent/vps-deploy.sh stop

# Create database backup
sudo /opt/med-assist-agent/vps-deploy.sh backup

# Enable auto-start on boot
sudo /opt/med-assist-agent/vps-deploy.sh systemd
```

## 🔄 Automatic Updates

### Set up GitHub Actions (Recommended)

1. **Add Docker Hub secrets to your GitHub repository:**
   - Go to your repository Settings → Secrets and variables → Actions
   - Add these secrets:
     - `DOCKER_USERNAME`: Your Docker Hub username
     - `DOCKER_TOKEN`: Docker Hub access token

2. **Push to production branch:**
   ```bash
   git push origin production
   ```

3. **GitHub Actions will automatically:**
   - Build Docker image
   - Push to Docker Hub
   - Create deployment artifacts

### Set up auto-deployment webhook (Optional)

Create a webhook endpoint on your VPS:

```bash
# Install webhook handler
sudo apt install webhook

# Create webhook configuration
sudo tee /etc/webhook.conf << 'EOF'
[
  {
    "id": "med-assist-deploy",
    "execute-command": "/opt/med-assist-agent/vps-deploy.sh",
    "command-working-directory": "/opt/med-assist-agent",
    "pass-arguments-to-command": [
      {
        "source": "string",
        "name": "deploy"
      }
    ],
    "trigger-rule": {
      "match": {
        "type": "payload-hash-sha1",
        "secret": "your-webhook-secret",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature"
        }
      }
    }
  }
]
EOF

# Start webhook service
sudo systemctl enable webhook
sudo systemctl start webhook
```

## 🌐 Domain and SSL Setup

### Configure Domain

1. **Point your domain to your VPS IP:**
   ```
   A record: your-domain.com → YOUR_VPS_IP
   ```

2. **Update environment:**
   ```bash
   sudo nano /opt/med-assist-agent/.env
   # Change WEBHOOK_BASE_URL=https://your-domain.com
   ```

### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/med-assist-agent/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/med-assist-agent/ssl/key.pem

# Update nginx config to enable HTTPS
sudo nano /opt/med-assist-agent/nginx.conf
# Uncomment the HTTPS server block and update server_name

# Restart services
sudo /opt/med-assist-agent/vps-deploy.sh deploy
```

### Auto-renewal

```bash
# Add to crontab for auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet --post-hook "docker-compose -f /opt/med-assist-agent/docker-compose.prod.yml restart nginx"
```

## 📊 Monitoring

### Application Health

```bash
# Check application health
curl http://your-server-ip:8000/health

# Check detailed status
sudo /opt/med-assist-agent/vps-deploy.sh status
```

### Logs

```bash
# Application logs
sudo /opt/med-assist-agent/vps-deploy.sh logs app

# All services logs
sudo /opt/med-assist-agent/vps-deploy.sh logs

# Nginx logs
sudo /opt/med-assist-agent/vps-deploy.sh logs nginx

# Database logs
sudo /opt/med-assist-agent/vps-deploy.sh logs postgres
```

### Resource Usage

```bash
# Docker stats
docker stats

# System resources
htop
df -h
free -h
```

## 🔒 Security

### Firewall Configuration

```bash
# Basic firewall setup
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

### Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
sudo /opt/med-assist-agent/vps-deploy.sh deploy
```

### Database Security

- Change default database password in `.env`
- Database is not exposed to the internet (only accessible within Docker network)
- Regular backups are created automatically

## 🚨 Troubleshooting

### Common Issues

1. **Docker not found:**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Permission denied:**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Logout and login again
   ```

3. **Port already in use:**
   ```bash
   # Check what's using the port
   sudo lsof -i :8000
   sudo lsof -i :80
   
   # Stop conflicting services
   sudo systemctl stop apache2  # If Apache is running
   sudo systemctl stop nginx    # If nginx is running
   ```

4. **Health check fails:**
   ```bash
   # Check application logs
   sudo /opt/med-assist-agent/vps-deploy.sh logs app
   
   # Check environment configuration
   sudo nano /opt/med-assist-agent/.env
   ```

5. **Database connection issues:**
   ```bash
   # Reset database
   cd /opt/med-assist-agent
   sudo docker-compose -f docker-compose.prod.yml down -v
   sudo docker-compose -f docker-compose.prod.yml up -d
   ```

### Support

- Check logs first: `sudo /opt/med-assist-agent/vps-deploy.sh logs`
- Verify configuration: `sudo nano /opt/med-assist-agent/.env`
- Test health endpoint: `curl http://localhost:8000/health`

## 📁 File Locations

- **Application:** `/opt/med-assist-agent/`
- **Environment:** `/opt/med-assist-agent/.env`
- **Logs:** `/opt/med-assist-agent/logs/`
- **Backups:** `/opt/med-assist-agent/backups/`
- **SSL Certificates:** `/opt/med-assist-agent/ssl/`
- **Deployment Script:** `/opt/med-assist-agent/vps-deploy.sh`

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Check logs for errors
   - Verify application health
   - Review resource usage

2. **Monthly:**
   - Update system packages
   - Clean old Docker images
   - Rotate log files

3. **As needed:**
   - Deploy application updates
   - Backup database
   - Update SSL certificates

### Update Process

1. **Pull latest changes:**
   ```bash
   sudo /opt/med-assist-agent/vps-deploy.sh deploy
   ```

2. **This automatically:**
   - Backs up the database
   - Pulls latest Docker image
   - Restarts services
   - Verifies health

Your Med Assist Agent will be accessible at:
- **HTTP:** `http://your-server-ip:8000`
- **API Docs:** `http://your-server-ip:8000/docs`
- **Health Check:** `http://your-server-ip:8000/health`