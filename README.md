# ⚡ VirtuRoll (Virtualizor-Traffic-Rollover)

<p align="center">
  <img src="https://img.shields.io/badge/VirtuRoll-v1.0.0-6366f1?style=for-the-badge&logo=fastapi&logoColor=white" alt="VirtuRoll Version" />
  <img src="https://img.shields.io/badge/Virtualizor-API%204085-06b6d4?style=for-the-badge&logo=linux&logoColor=white" alt="Virtualizor" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Telegram-Bot%20Alerts-229ed9?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot" />
  <img src="https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge" alt="License MIT" />
</p>

<p align="center">
  <b>Enterprise-grade, automated bandwidth rollover engine and management suite for Virtualizor nodes.</b><br>
  <i>Eliminates calendar-month bandwidth reset leaks for prepaid VPS packages. 100% Native Bare-Metal (No Docker Required).</i>
</p>

---

## 📖 Table of Contents
- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Key Features](#-key-features)
- [Architecture & Workflow](#-architecture--workflow)
- [One-Line Installation](#-one-line-installation-ubuntu--debian)
- [Quick Update](#-updating-an-existing-server)
- [Virtualizor API Configuration Guide](#-virtualizor-api-configuration-guide)
- [Telegram Bot Notification Setup](#-telegram-bot-notification-setup)
- [Service Management](#-service-management)
- [Security Recommendations](#-security-recommendations)
- [راهنمای فارسی (Persian Quick Guide)](#-راهنمای-فارسی-persian-quick-guide)
- [License](#-license)

---

## 🛑 The Problem

By design, **Virtualizor** treats all bandwidth allocations as recurring monthly subscriptions. On the 1st of every calendar month at 00:00:
1. Virtualizor resets every virtual machine's `used_bandwidth` counter to **`0 GB`**.
2. If a customer bought a **prepaid 5 TB plan** and used 4 TB, on the 1st of next month they receive a fresh 5 TB limit instead of their remaining 1 TB.
3. This creates massive bandwidth leaks, giving prepaid customers free unlimited traffic at the hosting provider's expense.

---

## ✨ The Solution

**VirtuRoll** runs as a native lightweight background daemon alongside your Virtualizor node. It continuously tracks bandwidth deltas without blind timezone dependencies:

$$\text{Persistent Remaining} = \text{Total Purchased} - \text{Total Cumulative Consumed}$$

When Virtualizor's internal month-end reset event fires (detected when used bandwidth drops sharply from the previous cycle), VirtuRoll automatically:
1. Calculates the VM's true remaining bandwidth balance.
2. Updates the active Virtualizor bandwidth limit via the Admin API (`POST /index.php?act=editvs`) to strictly match their actual remaining quota.
3. Excludes unlimited bandwidth servers (`bandwidth = 0`) safely to avoid false restrictions.
4. Logs the rollover event with microsecond audit trails and dispatches an instant alert to your **Telegram Bot**.

---

## 🌟 Key Features

| Capability | Description |
| :--- | :--- |
| 🔄 **Event-Driven Rollover Engine** | Does not rely on rigid clocks or fragile crontabs. Automatically detects when Virtualizor resets traffic and re-applies exact balances. |
| 🛡️ **Zero Unlimited Traffic Leaks** | Servers with unlimited plans (`bandwidth = 0`) are honored and excluded from rollover limits, displaying an `∞ Unlimited` badge. |
| 📊 **Host Hardware Telemetry** | Real-time monitoring of host CPU (usage %, cores, load average), RAM (GB and %), Swap (GB and %), Disk Storage (GB and %), and Live Uptime. |
| 🤖 **Telegram Notification Bot** | Instant notifications on monthly rollover events, top-ups, and node errors. Supports custom API endpoints and **SOCKS5 Proxies** for filtered servers. |
| 💎 **Obsidian Glassmorphic UI** | Obsidian Dark & Clean Light dual themes, dynamic capsule toast alerts, live system clock, and multilingual glass dropdown (EN/FA). |
| 📱 **Mobile-First Responsiveness** | Fully responsive touch layout with slide-out sidebar drawer, touch-friendly action buttons (min 44px), and adaptive metric cards. |
| 💾 **Backup & Restore Hub** | One-click `.json` configuration backups, database restoration, and instant backup report delivery directly to your Telegram bot. |
| 🚀 **100% Bare-Metal (No Docker)** | Runs directly inside an isolated Python virtual environment (`venv`) managed by a native `systemd` daemon (`virturoll.service`). |
| 🎲 **Smart Random Port Installer** | Automatically checks network sockets and allocates a conflict-free 4-digit port (2000–9999) with full customization options. |

---

## 📐 Architecture & Workflow

```mermaid
flowchart TD
    A["Virtualizor Dedicated Node"] -->|Calendar Month Reset| B["Virtualizor Resets Used BW to 0"]
    B -->|Event Detected| C["VirtuRoll Guardian Engine"]
    C -->|Calculate Balance| D["Remaining = Purchased - Used"]
    D -->|Virtualizor Admin API 4085| E["Apply New Bandwidth Quota to VM"]
    D -->|Audit Database| F["SQLite Persistent Store"]
    D -->|Alert Dispatcher| G["Telegram Bot Notification"]
    H["Admin Web Dashboard"] -->|View Telemetry & VPS| C
    H -->|Add Traffic Top-Up| E
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

## ⚙️ Virtualizor API Configuration Guide

VirtuRoll communicates directly with your Virtualizor Master node via port **4085** (Admin API).

### Step 1: Create API Credentials
1. Log in to your **Virtualizor Admin Panel**.
2. Navigate to **Configuration** -> **API Credentials**.
3. Click **Add API Key**.
4. Set the **API Key** and **API Password**.
5. **CRITICAL:** Under **Allowed IPs**, add the IP address of the server running VirtuRoll (or `127.0.0.1` if installed locally).

> [!IMPORTANT]
> If your server's IP is not whitelisted in the Virtualizor API settings, Virtualizor returns an HTML login redirect instead of JSON, resulting in a connection failure.

### Step 2: Connect from VirtuRoll Dashboard
1. Open your VirtuRoll panel (`http://YOUR_SERVER_IP:PORT`).
2. Go to **Settings** -> **Virtualizor Node Connection**.
3. Enter your **Server IP or Domain** (e.g., `185.120.45.67` or `sub.domain.com`), API Port (`4085`), **API Key**, and **API Password**.
4. Click **Test Connection** to verify, then click **Save & Connect**.

---

## 🤖 Telegram Bot Notification Setup

Receive real-time alerts whenever a traffic rollover happens, top-up is applied, or if a connection error occurs.

1. Create a bot using [@BotFather](https://t.me/BotFather) and obtain your **Bot Token**.
2. Obtain your **Chat ID** or Channel ID (e.g., from [@userinfobot](https://t.me/userinfobot) or your group).
3. In VirtuRoll, navigate to **Settings** -> **Telegram Bot Notifications**.
4. Enable **Bot Alerts** and fill in your Token and Chat ID.
5. *(Optional for Iran/Filtered Servers)*: Add your **SOCKS5 Proxy** (e.g., `socks5://user:pass@host:port`) or **Telegram API Server**.
6. Click **Send Test Notification** to confirm!

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

## 🇮🇷 راهنمای فارسی (Persian Quick Guide)

سامانه **ویرتو رول (VirtuRoll)** ابزاری خودکار، سبک و بدون نیاز به داکر برای مدیریت و حفظ ترافیک سرورهای مجازی در مجازی‌ساز **Virtualizor** است.

### ❓ مشکل اصلی ویرچوالایزور چیست؟
به صورت پیش‌فرض در ابتدای هر ماه میلادی (ساعت ۰۰:۰۰ روز اول ماه)، ویرچوالایزور مصرف ترافیک همه ماشین‌های مجازی را **صفر** می‌کند. اگر سرویس‌های خود را با بسته‌های ترافیکی ثابت یا پیش‌پرداخت (مثلاً ۵ ترابایت) می‌فروشید، این ریست خودکار باعث می‌شود مشتریان هر ماه بدون پرداخت هزینه مجدد، ترافیک رایگان دریافت کنند.

### 💡 راهکار ویرتو رول
ویرتو رول با پایش لحظه‌ای و هوشمند ترافیک بدون وابستگی به ساعت یا منطقه زمانی، به محض وقوع ریست اول ماه، مانده واقعی ترافیک هر سرور را محاسبه کرده و سقف مجاز ترافیک آن را دقیقاً برابر با باقیمانده واقعی آن تنظیم می‌کند.

### 🚀 نصب تک خطی (روی اوبونتو و دبیان):
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/a-salemi/Virtualizor-Traffic-Rollover/main/install.sh)"
```

### 🔄 بروزرسانی سریع نسخه نصب شده:
```bash
cd /opt/virturoll && git pull && ./venv/bin/pip install -r backend/requirements.txt && systemctl restart virturoll
```

---

## 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).
Copyright (c) 2026 Amir Salemi.
