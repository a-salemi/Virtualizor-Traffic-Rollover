#!/usr/bin/env bash
# ==============================================================================
# VirtuRoll - Interactive Linux Installer (No Docker Required)
# Supports one-line installation:
# bash -c "$(curl -fsSL https://raw.githubusercontent.com/a-salemi/Virtualizor-Traffic-Rollover/main/install.sh)"
# ==============================================================================

set -e

# Styling
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear 2>/dev/null || true

echo -e "${CYAN}${BOLD}"
echo "=========================================================="
echo "          VirtuRoll - Bandwidth Rollover Engine           "
echo "        Interactive Installer & Systemd Setup             "
echo "=========================================================="
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run this installer as root (e.g. sudo bash install.sh)${NC}"
    exit 1
fi

# Detect TTY for interactive inputs even if piped through curl | bash
if [ -t 0 ]; then
    INPUT_SRC="/dev/stdin"
else
    INPUT_SRC="/dev/tty"
fi

# Target directory
INSTALL_DIR="/opt/virturoll"

echo -e "${YELLOW}[1/5] Checking and installing system dependencies...${NC}"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl

# Handle one-liner cloning or local execution
if [ ! -f "backend/app.py" ]; then
    echo -e "${YELLOW}Cloning VirtuRoll into ${INSTALL_DIR}...${NC}"
    if [ -d "$INSTALL_DIR/.git" ]; then
        cd "$INSTALL_DIR"
        git reset --hard HEAD
        git pull origin main
    else
        mkdir -p "$INSTALL_DIR"
        git clone https://github.com/a-salemi/Virtualizor-Traffic-Rollover.git "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
else
    INSTALL_DIR="$(pwd)"
    cd "$INSTALL_DIR"
fi

SKIP_CREDENTIAL_PROMPT=false
if [ -f ".env" ] && grep -q "ADMIN_USERNAME=" .env && grep -q "PORT=" .env; then
    EXISTING_USER=$(grep -E "^ADMIN_USERNAME=" .env | cut -d '=' -f2- | tr -d '[:space:]')
    EXISTING_PORT=$(grep -E "^PORT=" .env | cut -d '=' -f2- | tr -d '[:space:]')
    
    echo ""
    echo -e "${GREEN}${BOLD}✓ Existing installation detected!${NC}"
    echo -e "User: ${CYAN}${EXISTING_USER}${NC} | Port: ${CYAN}${EXISTING_PORT}${NC}"
    echo ""
    read -r -p "$(echo -e "${BOLD}Keep existing credentials, database & configuration? [Y/n]:${NC} ")" KEEP_CONF < "$INPUT_SRC"
    KEEP_CONF=${KEEP_CONF:-Y}
    
    if [[ "$KEEP_CONF" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Keeping existing configuration. Your user data and port will NOT be overwritten.${NC}"
        ADMIN_USER="$EXISTING_USER"
        SELECTED_PORT="$EXISTING_PORT"
        SKIP_CREDENTIAL_PROMPT=true
    fi
fi

if [ "$SKIP_CREDENTIAL_PROMPT" != "true" ]; then
    echo ""
    echo -e "${CYAN}${BOLD}--- Administrator & Security Setup ---${NC}"
    echo -e "${YELLOW}Please enter your desired credentials for the VirtuRoll web panel.${NC}"
    echo ""

    # 1. Prompt for Admin Username (Mandatory)
    ADMIN_USER=""
    while [ -z "$ADMIN_USER" ]; do
        read -r -p "$(echo -e "${BOLD}Enter Admin Username:${NC} ")" ADMIN_USER < "$INPUT_SRC"
        ADMIN_USER=$(echo "$ADMIN_USER" | tr -d '[:space:]')
        if [ -z "$ADMIN_USER" ]; then
            echo -e "${RED}Username cannot be empty. Please enter a valid username.${NC}"
        fi
    done

    # 2. Prompt for Admin Password (Mandatory)
    ADMIN_PASS=""
    while [ -z "$ADMIN_PASS" ]; do
        read -s -r -p "$(echo -e "${BOLD}Enter Admin Password:${NC} ")" ADMIN_PASS < "$INPUT_SRC"
        echo ""
        ADMIN_PASS=$(echo "$ADMIN_PASS" | tr -d '[:space:]')
        if [ -z "$ADMIN_PASS" ]; then
            echo -e "${RED}Password cannot be empty. Please enter a valid password.${NC}"
        elif [ ${#ADMIN_PASS} -lt 6 ]; then
            echo -e "${RED}Password should be at least 6 characters for security.${NC}"
            ADMIN_PASS=""
        fi
    done

    # 3. Find an available 4-digit port (2000 - 9999) without conflict
    check_port() {
        python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); res = s.connect_ex(('127.0.0.1', $1)); s.close(); exit(0 if res == 0 else 1)" 2>/dev/null
    }

    SUGGESTED_PORT=""
    while [ -z "$SUGGESTED_PORT" ]; do
        CANDIDATE=$(( ( RANDOM % 8000 ) + 2000 ))
        if ! check_port "$CANDIDATE"; then
            SUGGESTED_PORT="$CANDIDATE"
        fi
    done

    SELECTED_PORT=""
    while [ -z "$SELECTED_PORT" ]; do
        read -r -p "$(echo -e "${BOLD}Enter Service Port [Default: ${GREEN}${SUGGESTED_PORT}${NC}${BOLD}] (Press Enter to accept):${NC} ")" INPUT_PORT < "$INPUT_SRC"
        INPUT_PORT=$(echo "$INPUT_PORT" | tr -d '[:space:]')
        
        if [ -z "$INPUT_PORT" ]; then
            SELECTED_PORT="$SUGGESTED_PORT"
        else
            if [[ "$INPUT_PORT" =~ ^[0-9]+$ ]] && [ "$INPUT_PORT" -ge 1024 ] && [ "$INPUT_PORT" -le 65535 ]; then
                if check_port "$INPUT_PORT"; then
                    echo -e "${RED}Port $INPUT_PORT is already in use by another service! Please choose another port.${NC}"
                else
                    SELECTED_PORT="$INPUT_PORT"
                fi
            else
                echo -e "${RED}Invalid port. Must be a number between 1024 and 65535.${NC}"
            fi
        fi
    done

    echo ""
    echo -e "${GREEN}Configured: Username='${ADMIN_USER}', Port='${SELECTED_PORT}'${NC}"
    echo ""
fi

echo -e "${YELLOW}[2/5] Setting up isolated Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

echo -e "${YELLOW}[3/5] Checking configuration...${NC}"
if [ "$SKIP_CREDENTIAL_PROMPT" = "true" ]; then
    echo -e "${GREEN}Keeping existing .env configuration and database intact.${NC}"
else
    RANDOM_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Keep existing API key if present
    PREV_API_KEY=""
    PREV_API_PASS=""
    PREV_NODE_IP="127.0.0.1"
    PREV_NODE_PORT="4085"
    if [ -f ".env" ]; then
        PREV_API_KEY=$(grep -E "^VIRTUALIZOR_API_KEY=" .env | cut -d '=' -f2- | tr -d ' ' || true)
        PREV_API_PASS=$(grep -E "^VIRTUALIZOR_API_PASS=" .env | cut -d '=' -f2- | tr -d ' ' || true)
        PREV_NODE_IP=$(grep -E "^VIRTUALIZOR_IP=" .env | cut -d '=' -f2- | tr -d ' ' || true)
        PREV_NODE_PORT=$(grep -E "^VIRTUALIZOR_PORT=" .env | cut -d '=' -f2- | tr -d ' ' || true)
    fi

    cat <<EOF > .env
# Server Binding
HOST=0.0.0.0
PORT=${SELECTED_PORT}

# Security
SECRET_KEY=${RANDOM_SECRET}
ADMIN_USERNAME=${ADMIN_USER}
ADMIN_PASSWORD=${ADMIN_PASS}

# Virtualizor Node API (Can also be configured in Web Dashboard)
VIRTUALIZOR_IP=${PREV_NODE_IP:-127.0.0.1}
VIRTUALIZOR_PORT=${PREV_NODE_PORT:-4085}
VIRTUALIZOR_API_KEY=${PREV_API_KEY}
VIRTUALIZOR_API_PASS=${PREV_API_PASS}

# Watcher Settings
POLL_INTERVAL_MINUTES=5
ROLLOVER_WINDOW_START_DAY=27
ROLLOVER_WINDOW_END_DAY=5
EOF

    chmod 600 .env
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
ExecStart=${INSTALL_DIR}/venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port ${SELECTED_PORT}
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

# Robust Server IP detection with regex validation and multiple fallbacks
get_server_ip() {
    local detected_ip=""
    for service_url in "https://api.ipify.org" "https://icanhazip.com" "https://checkip.amazonaws.com" "https://ipinfo.io/ip"; do
        detected_ip=$(curl -s4 -A "curl/7.81.0" --max-time 3 "$service_url" 2>/dev/null | tr -d '[:space:]' || true)
        if [[ "$detected_ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            echo "$detected_ip"
            return 0
        fi
    done

    # Fallback to local default network route IP
    detected_ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' | tr -d '[:space:]' || true)
    if [[ "$detected_ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo "$detected_ip"
        return 0
    fi

    # Fallback to hostname -I
    detected_ip=$(hostname -I 2>/dev/null | awk '{print $1}' | tr -d '[:space:]' || true)
    if [[ "$detected_ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo "$detected_ip"
        return 0
    fi

    echo "YOUR_SERVER_IP"
}

SERVER_IP=$(get_server_ip)

if systemctl is-active --quiet virturoll; then
    echo ""
    echo -e "${GREEN}${BOLD}==========================================================${NC}"
    echo -e "${GREEN}${BOLD}      VirtuRoll has been installed and started successfully!  ${NC}"
    echo -e "${GREEN}${BOLD}==========================================================${NC}"
    echo ""
    echo -e "Dashboard URL:       ${CYAN}http://${SERVER_IP}:${SELECTED_PORT}${NC}"
    echo -e "Service Port:        ${CYAN}${SELECTED_PORT}${NC}"
    echo -e "Admin Username:      ${GREEN}${ADMIN_USER}${NC}"
    echo -e "Config Location:     ${YELLOW}${INSTALL_DIR}/.env${NC}"
    echo ""
    echo -e "${BOLD}${YELLOW}Important Next Steps:${NC}"
    echo -e "1. Edit ${CYAN}${INSTALL_DIR}/.env${NC} and insert your ${YELLOW}VIRTUALIZOR_API_KEY${NC} and ${YELLOW}VIRTUALIZOR_API_PASS${NC}."
    echo -e "2. Apply changes: ${CYAN}systemctl restart virturoll${NC}"
    echo -e "3. Reverse proxy port ${CYAN}${SELECTED_PORT}${NC} securely from your external server."
    echo ""
else
    echo -e "${RED}Service failed to start. View debug logs: journalctl -u virturoll -n 50 -e${NC}"
fi
