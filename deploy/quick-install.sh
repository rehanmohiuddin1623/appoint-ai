#!/bin/bash

# Quick VPS deployment script
# Download and run this script on your VPS to deploy Med Assist Agent

set -e

REPO_URL="https://raw.githubusercontent.com/rehanmohiuddin1623/appoint-ai/production/deploy/vps-deploy.sh"
INSTALL_DIR="/tmp/med-assist-install"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Med Assist Agent - Quick Install${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_header

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root or with sudo"
    echo "Run: sudo bash $0"
    exit 1
fi

print_status "Downloading deployment script..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download the main deployment script
curl -fsSL "$REPO_URL" -o vps-deploy.sh
chmod +x vps-deploy.sh

print_status "Starting setup..."
./vps-deploy.sh setup

print_status "Quick install completed!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/med-assist-agent/.env with your API keys"
echo "2. Run: sudo /opt/med-assist-agent/vps-deploy.sh deploy"
echo ""
echo "The deployment script is available at: /opt/med-assist-agent/vps-deploy.sh"