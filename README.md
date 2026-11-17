# ⚡ VirtuRoll (Virtualizor-Traffic-Rollover)

<p align="center">
  <img src="https://img.shields.io/badge/VirtuRoll-v2.0.0-6366f1?style=for-the-badge&logo=fastapi&logoColor=white" alt="VirtuRoll Version" />
  <img src="https://img.shields.io/badge/Virtualizor-Multi--Panel%204085-06b6d4?style=for-the-badge&logo=linux&logoColor=white" alt="Virtualizor" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Telegram-Bot%20Document%20Alerts-229ed9?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot" />
  <img src="https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge" alt="License MIT" />
</p>

<p align="center">
  <b>Enterprise-grade, automated bandwidth rollover engine and multi-node fleet management for Virtualizor.</b><br>
  <i>Eliminates calendar-month bandwidth reset leaks for prepaid VPS packages. 100% Native Bare-Metal (No Docker Required).</i>
</p>

<p align="center">
  <b>🌐 Choose Language / انتخاب زبان:</b><br>
  <a href="README.md"><b>English</b></a> •
  <a href="README.fa.md"><b>فارسی (Persian)</b></a> •
  <a href="README.ru.md"><b>Русский (Russian)</b></a> •
  <a href="README.zh.md"><b>简体中文 (Chinese)</b></a> •
  <a href="README.tr.md"><b>Türkçe (Turkish)</b></a> •
  <a href="README.ar.md"><b>العربية (Arabic)</b></a>
</p>

---

## 📖 Table of Contents
- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Key Features](#-key-features)
- [Architecture & Workflow](#-architecture--workflow)
- [One-Line Installation](#-one-line-installation-ubuntu--debian)
- [Quick Update](#-updating-an-existing-server)
- [Virtualizor Panels Setup Guide](#-virtualizor-panels-setup-guide)
- [Telegram Bot Notification & Backup Setup](#-telegram-bot-notification--backup-setup)
- [Service Management](#-service-management)
- [Security Recommendations](#-security-recommendations)
- [License](#-license)

---

## 🛑 The Problem

By design, **Virtualizor** treats all bandwidth allocations as recurring monthly subscriptions. On the 1st of every calendar month at 00:00:
1. Virtualizor resets every virtual machine's `used_bandwidth` counter to **`0 GB`**.
2. If a customer bought a **prepaid 5 TB plan** and used 4 TB, on the 1st of next month they receive a fresh 5 TB limit instead of their remaining 1 TB.
3. This creates massive bandwidth leaks, giving prepaid customers free unlimited traffic at the hosting provider's expense.

---

## ✨ The Solution

**VirtuRoll** runs as a native lightweight background daemon alongside your Virtualizor nodes. It continuously monitors bandwidth deltas and treats the Virtualizor hypervisor as the single source of truth:

$$\text{Persistent Remaining} = \text{Virtualizor Limit} - \text{Cumulative Consumed}$$

When Virtualizor's internal month-end reset event fires (detected when used bandwidth drops sharply from the previous cycle within the rollover window), VirtuRoll automatically:
1. Calculates the VM's true remaining bandwidth balance.
2. Updates the active Virtualizor bandwidth limit via the Admin API (`POST /index.php?act=editvs&vpsid={id}&editvps=1&bandwidth={int_gb}`) to strictly match their actual remaining quota.
3. Excludes unlimited bandwidth servers (`bandwidth = 0`) safely to avoid false restrictions.
4. Logs the rollover event with microsecond audit trails and dispatches an instant alert to your **Telegram Bot**.

---

## 🌟 Key Features

| Capability | Description |
| :--- | :--- |
| 🔄 **Event-Driven Rollover Engine** | Does not rely on rigid clocks or fragile crontabs. Automatically detects when Virtualizor resets traffic and re-applies exact balances. |
| 🛡️ **Zero Unlimited Traffic Leaks** | Servers with unlimited plans (`bandwidth = 0`) are honored and excluded from rollover limits, displaying an `∞ Unlimited` badge. |
| 🎛️ **Multi-Panel Virtualizor Management** | Add, edit, delete, test connection, and individually sync unlimited master and slave Virtualizor nodes from a dedicated **Panels** tab. |
| 📊 **Hardware Telemetry** | Real-time monitoring of host CPU (smoothed usage %, cores, load average), RAM (GB and %), Swap (GB and %), Disk Storage (GB and %), and Live Uptime. |
| 🤖 **Telegram Notification & Backup Bot** | Instant notifications on monthly rollover events, top-ups, and errors. One-click instant delivery of complete `.json` backups via Telegram documents. Supports **SOCKS5 Proxies** for filtered hosts. |
| 💎 **Obsidian Glassmorphic UI** | Obsidian Dark & Clean Light dual themes, dynamic capsule toast alerts, live system clock, and multilingual glass dropdown supporting 6 languages: **EN, FA, RU, ZH, TR, AR** with native RTL layout. |
| 📜 **Audit Logs Hub** | Transparent logging with event badges (`ROLLOVER`, `ADD_TRAFFIC`, `SYNC`, `AUTH`, `SYSTEM`), Refresh Logs, and permanent Clear Logs actions. |
| 📱 **Mobile-First Responsiveness** | Fully responsive touch layout with slide-out sidebar drawer, touch-friendly action buttons (min 44px), and adaptive metric cards. |
| 🚀 **100% Bare-Metal (No Docker)** | Runs directly inside an isolated Python virtual environment (`venv`) managed by a native `systemd` daemon (`virturoll.service`). |

---

## 📐 Architecture & Workflow

```mermaid
flowchart TD
    A["Virtualizor Dedicated Nodes"] -->|Calendar Month Reset| B["Virtualizor Resets Used BW to 0"]
    B -->|Reset Event Detected| C["VirtuRoll Guardian Engine"]
    C -->|Calculate Balance| D["Remaining = Purchased - Used"]
    D -->|Virtualizor Admin API 4085| E["Push True Remaining Quota to VM"]
    D -->|Persistent Store| F["SQLite Database"]
    D -->|Alert Dispatcher| G["Telegram Bot Notification"]
    H["Admin Web Dashboard"] -->|View Telemetry & VPS Fleet| C
    H -->|Add Traffic Top-Up| E
    H -->|Export Backup Document| G
```

---

## ⚡ One-Line Installation (Ubuntu / Debian)

Run this single command with `root` privileges on your server:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/a-salemi/Virtualizor-Traffic-Rollover/main/install.sh)"
```

### 🧙‍♂️ Interactive Setup Wizard
1. **Admin Username:** Specify your manager username.
2. **Admin Password:** Choose your dashboard password (minimum 6 characters).
3. **Random Service Port:** The installer auto-detects a clean, available 4-digit port (e.g. `8789`). Press **Enter** to accept or type your custom port.
4. **Idempotent Protection:** If an existing configuration is found, the installer prompts to keep your `.env` and database without overwriting.

---

## 🔄 Updating an Existing Server

To update your VirtuRoll instance to the latest release without losing any data:

```bash
cd /opt/virturoll && git pull && ./venv/bin/pip install -r backend/requirements.txt && systemctl restart virturoll
```

---

## ⚙️ Virtualizor Panels Setup Guide

VirtuRoll communicates directly with your Virtualizor nodes via port **4085** (Admin API).

### Step 1: Create API Credentials
1. Log in to your **Virtualizor Admin Panel**.
2. Navigate to **Configuration** -> **API Credentials**.
3. Click **Add API Key**.
4. Set the **API Key** and **API Password**.
5. **CRITICAL:** Under **Allowed IPs**, add the IP address of the server running VirtuRoll (or `127.0.0.1` if installed locally).

> [!IMPORTANT]
> If your server's IP is not whitelisted in the Virtualizor API settings, Virtualizor returns an HTML login redirect instead of JSON, resulting in a connection failure.

### Step 2: Add Panel in VirtuRoll Dashboard
1. Open your VirtuRoll dashboard (`http://YOUR_SERVER_IP:PORT`).
2. Navigate to the **Panels** tab in the sidebar.
3. Click **+ Add Panel**.
4. Enter Panel Name, IP / Domain, API Port (`4085`), API Key, and API Password.
5. Click **Save Panel**. VirtuRoll tests the connection and syncs instances immediately.

---

## 🤖 Telegram Bot Notification & Backup Setup

Receive real-time alerts whenever a traffic rollover happens, top-up is applied, or deliver automated `.json` database backups directly to your private chat.

1. Create a bot using [@BotFather](https://t.me/BotFather) and obtain your **Bot Token**.
2. Obtain your **Chat ID** or Channel ID (e.g., from [@userinfobot](https://t.me/userinfobot) or your group).
3. In VirtuRoll, navigate to **Settings** -> **Telegram Bot Notifications**.
4. Enable **Bot Alerts** and fill in your Token and Chat ID.
5. *(Optional for Filtered Servers)*: Add your **SOCKS5 Proxy** (e.g., `socks5://user:pass@host:port`) or **Telegram API Server**.
6. Click **Send Test Notification** to confirm!
7. Under **Backup & Restore**, click **Send Backup to Telegram** to dispatch a complete timestamped backup document.

---

## 🛠️ Service Management

```bash
# Check service status
sudo systemctl status virturoll

# View real-time daemon logs
sudo journalctl -u virturoll -f

# Restart daemon
sudo systemctl restart virturoll

# Stop daemon
sudo systemctl stop virturoll
```

---

## 🔒 Security Recommendations

1. **Firewall / Reverse Proxy:** Expose port 80/443 via NGINX or Caddy reverse proxy with an SSL certificate, and restrict direct access to your internal VirtuRoll port via `ufw` or `iptables`.
2. **API Whitelist:** In Virtualizor's Admin Panel, restrict API key access strictly to your VirtuRoll server's IP.
3. **Strong Credentials:** Choose a robust dashboard password. You can change your password anytime under **Settings** -> **User Management**.

---

## 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).  
Copyright (c) 2026 Amir Salemi.
