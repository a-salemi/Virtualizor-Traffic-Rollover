#!/usr/bin/env bash
# ==============================================================================
# VirtuRoll - Native Linux Installer (No Docker Required)
# Production-ready Systemd service setup with random port allocation
# ==============================================================================

set -e

# Styling
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "=========================================================="
echo "          VirtuRoll - Bandwidth Rollover Engine           "
echo "=========================================================="
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run this installer as root (e.g. sudo bash install.sh)${NC}"
    exit 1
fi

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$INSTALL_DIR"

echo -e "${YELLOW}[1/5] Checking and installing system dependencies...${NC}"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv curl

echo -e "${YELLOW}[2/5] Setting up isolated Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

echo -e "${YELLOW}[3/5] Configuring environment & random security port...${NC}"
if [ ! -f ".env" ]; then
    # Generate high random port between 22000 and 59000
    RANDOM_PORT=$(( ( RANDOM % 37000 ) + 22000 ))
    RANDOM_SECRET=$(head -c 32 /dev/urandom | xxd -p)
    INITIAL_PASSWORD=$(head -c 8 /dev/urandom | xxd -p)

    cat <<EOF > .env
# Server Binding
HOST=0.0.0.0
PORT=${RANDOM_PORT}

# Security
SECRET_KEY=${RANDOM_SECRET}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${INITIAL_PASSWORD}

# Virtualizor Node API (Localhost on Dedicated Server)
VIRTUALIZOR_IP=127.0.0.1
VIRTUALIZOR_PORT=4085
VIRTUALIZOR_API_KEY=
VIRTUALIZOR_API_PASS=

# Watcher Settings
POLL_INTERVAL_MINUTES=5
ROLLOVER_WINDOW_START_DAY=27
ROLLOVER_WINDOW_END_DAY=5
EOF

    echo -e "${GREEN}Created new .env configuration file.${NC}"
else
    echo -e "${CYAN}Existing .env found. Keeping your current configuration.${NC}"
    RANDOM_PORT=$(grep -E "^PORT=" .env | cut -d '=' -f2 | tr -d ' ')
fi

mkdir -p data

echo -e "${YELLOW}[4/5] Creating Systemd service (virturoll.service)...${NC}"
SERVICE_FILE="/etc/systemd/system/virturoll.service"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=VirtuRoll Persistent Bandwidth Guardian
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port \${PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable virturoll
systemctl restart virturoll

echo -e "${YELLOW}[5/5] Checking service status...${NC}"
sleep 2

if systemctl is-active --quiet virturoll; then
    echo -e "${GREEN}==========================================================${NC}"
    echo -e "${GREEN}      VirtuRoll has been installed and started successfully!  ${NC}"
    echo -e "${GREEN}==========================================================${NC}"
    echo ""
    echo -e "Service Port:        ${CYAN}${RANDOM_PORT}${NC}"
    echo -e "Dashboard URL:       ${CYAN}http://YOUR_SERVER_IP:${RANDOM_PORT}${NC}"
    echo -e "Config File:         ${YELLOW}${INSTALL_DIR}/.env${NC}"
    echo ""
    echo -e "${YELLOW}Important Next Steps:${NC}"
    echo -e "1. Edit ${CYAN}.env${NC} and fill in your ${YELLOW}VIRTUALIZOR_API_KEY${NC} and ${YELLOW}VIRTUALIZOR_API_PASS${NC}."
    echo -e "2. Check your initial admin password in ${CYAN}.env${NC}."
    echo -e "3. Reverse proxy this port (${CYAN}${RANDOM_PORT}${NC}) from your external server securely."
    echo -e "4. Restart after changing .env: ${CYAN}systemctl restart virturoll${NC}"
    echo ""
else
    echo -e "${RED}Service failed to start. Check logs with: journalctl -u virturoll -f${NC}"
fi
