# VirtuRoll (Virtualizor-Traffic-Rollover)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688.svg)](https://fastapi.tiangolo.com/)

**VirtuRoll** is an automated, event-driven bandwidth rollover engine and management dashboard for **Virtualizor** dedicated nodes. 

Designed specifically for hosting providers and infrastructure administrators who sell **fixed/prepaid bandwidth plans** (e.g., 5 TB persistent quota) rather than recurring calendar-month resets.

---

## The Problem
By default, Virtualizor assumes all bandwidth packages are recurring monthly quotas. On the turn of each calendar month, Virtualizor resets every virtual machine's consumed traffic to `0`, causing prepaid customers to receive fresh bandwidth without purchasing more.

## The Solution
VirtuRoll continuously monitors bandwidth deltas via the official Virtualizor API on localhost. When a monthly reset event is detected, VirtuRoll instantly calculates:
$$\text{Remaining Bandwidth} = \text{Total Limit} - \text{Consumed Bandwidth}$$
and automatically sets the VM's active Virtualizor limit to match their exact remaining balance.

---

## Key Features

- **Event-Driven Rollover Engine:** Does not blindly rely on clocks or specific timezones. Detects Virtualizor's internal reset events dynamically and safely.
- **Bare-Metal & Native:** Runs directly on Ubuntu via an isolated Python virtual environment and a native Systemd daemon—**no Docker required**.
- **Random Port Allocation:** Automatically allocates a randomized high port (between 22000–59000) during installation, ideal for external reverse proxies.
- **Modern Responsive Dashboard:**
  - Dual theme with instant system preference detection (`Obsidian Dark` & `Clean Light`).
  - Bidirectional internationalization (**English LTR** & **فارسی RTL**) with Vazirmatn and Plus Jakarta Sans typography.
  - Real-time Dynamic Island capsule toast notifications.
  - Mobile-first architecture that seamlessly transforms data tables into touch-friendly cards on smaller screens (<868px).
- **One-Click Top-Up:** Easily add persistent traffic buckets to any VM directly from the UI or API.
- **Audit Logging:** Every rollover and manual modification is logged with timestamps and delta metrics.

---

## Quick Installation (Ubuntu / Debian)

Clone the repository and run the automated native installer:

```bash
git clone https://github.com/a-salemi/Virtualizor-Traffic-Rollover.git /opt/virturoll
cd /opt/virturoll
sudo bash install.sh
```

The installer will:
1. Install system prerequisites (`python3`, `python3-venv`, `curl`).
2. Create an isolated virtual environment and install dependencies.
3. Generate a random high port and secure session secrets in `.env`.
4. Register and start the `virturoll.service` systemd service.

---

## Configuration

Edit `/opt/virturoll/.env` to connect to your local Virtualizor node:

```ini
# Server Binding
HOST=0.0.0.0
PORT=48921

# Security
SECRET_KEY=your_generated_secret_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password

# Virtualizor Node API (Localhost on Dedicated Node)
VIRTUALIZOR_IP=127.0.0.1
VIRTUALIZOR_PORT=4085
VIRTUALIZOR_API_KEY=YOUR_ADMIN_API_KEY
VIRTUALIZOR_API_PASS=YOUR_ADMIN_API_PASS

# Watcher Settings
POLL_INTERVAL_MINUTES=5
ROLLOVER_WINDOW_START_DAY=27
ROLLOVER_WINDOW_END_DAY=5
```

After modifying `.env`, restart the daemon:
```bash
sudo systemctl restart virturoll
```

---

## Service Management

- **Check Service Status:**
  ```bash
  sudo systemctl status virturoll
  ```
- **View Live Logs:**
  ```bash
  sudo journalctl -u virturoll -f
  ```
- **Restart Service:**
  ```bash
  sudo systemctl restart virturoll
  ```

---

## Security Recommendations

1. **Virtualizor API Whitelist:** In your Virtualizor Admin Panel (`Configuration -> API Key`), restrict the API key's IP address strictly to `127.0.0.1`.
2. **Reverse Proxy:** Route your external domain or subdomain to `http://127.0.0.1:<RANDOM_PORT>` (or through your external proxy) over HTTPS.
3. **Firewall:** If reverse proxying internally, keep the allocated random port blocked from direct public internet access using UFW or iptables.

---

## License

This project is licensed under the [MIT License](LICENSE).
