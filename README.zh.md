# ⚡ VirtuRoll (Virtualizor VPS 流量结转系统)

<p align="center">
  <img src="https://img.shields.io/badge/VirtuRoll-版本%202.0.0-6366f1?style=for-the-badge&logo=fastapi&logoColor=white" alt="VirtuRoll Version" />
  <img src="https://img.shields.io/badge/Virtualizor-API%204085-06b6d4?style=for-the-badge&logo=linux&logoColor=white" alt="Virtualizor" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Telegram-告警与备份推送-229ed9?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot" />
  <img src="https://img.shields.io/badge/开源协议-MIT-emerald?style=for-the-badge" alt="License MIT" />
</p>

<p align="center">
  <b>专为 Virtualizor 打造的企业级自动化 VPS 流量结转守护引擎与多节点管理系统。</b><br>
  <i>彻底解决预付费 VPS 流量包因自然月重置而导致的流量损耗。100% 原生轻量运行（无需 Docker）。</i>
</p>

<p align="center">
  <b>🌐 语言切换 / Other Languages:</b><br>
  <a href="README.md"><b>English</b></a> •
  <a href="README.fa.md"><b>فارسی (Persian)</b></a> •
  <a href="README.ru.md"><b>Русский (Russian)</b></a> •
  <a href="README.zh.md"><b>简体中文 (Chinese)</b></a> •
  <a href="README.tr.md"><b>Türkçe (Turkish)</b></a> •
  <a href="README.ar.md"><b>العربية (Arabic)</b></a>
</p>

---

## 📖 目录
- [问题背景](#-问题背景)
- [解决方案](#-解决方案)
- [核心特性](#-核心特性)
- [一键极速安装](#-一键极速安装-ubuntu--debian)
- [系统平滑升级](#-系统平滑升级)
- [Virtualizor 多面板配置指南](#-virtualizor-多面板配置指南)
- [Telegram 机器人与备份配置](#-telegram-机器人与备份配置)
- [系统服务管理](#-系统服务管理)
- [开源许可证](#-开源许可证)

---

## 🛑 问题背景

**Virtualizor** 默认将所有流量配额均视为循环的自然月套餐。在每月 1 日凌晨 00:00：
1. Virtualizor 会将每台虚拟机的已用流量计数器重置为 **`0 GB`**。
2. 若用户购买了 **5 TB 预付费流量**且消耗了 4 TB，下月 1 日他们将重新获得 5 TB 满额配额，而非剩余的 1 TB。
3. 这造成了严重的服务商流量外泄与财务损失。

---

## ✨ 解决方案

**VirtuRoll** 作为后台常驻守护进程运行，始终以 Virtualizor 宿主机的实际数据为唯一事实来源：

$$\text{真实剩余流量} = \text{面板额度} - \text{本周期消耗流量}$$

当月初 Virtualizor 重置计数器触发时，VirtuRoll 会自动：
1. 精确计算每台虚拟机的实际剩余额度。
2. 通过 Admin API (`POST /index.php?act=editvs`) 自动将面板带宽上限重置为真实剩余值。
3. 严格保护不限流量主机（`bandwidth = 0`），避免误限制。
4. 记录微秒级审计日志并向 **Telegram 机器人**推送实时通知。

---

## 🌟 核心特性

| 功能模块 | 说明 |
| :--- | :--- |
| 🔄 **事件驱动结转引擎** | 不依赖硬编码时间与 Cron 定时任务，秒级感知月初重置事件并自动平滑处理。 |
| 🎛️ **多面板统一纳管** | 在专用的**面板**页面轻松添加、管理和单独同步多个 Virtualizor 主从节点。 |
| 📊 **宿主机实时硬件监控** | 准确平滑显示 CPU 使用率（无频繁跳变）、内存、SWAP、磁盘及运行时间。 |
| 🤖 **Telegram 文件备份与告警** | 结转告警通知，一键将完整 `.json` 数据库备份文件发送至私人聊天。支持 **SOCKS5** 代理。 |
| 💎 **毛玻璃暗黑设计风格** | 现代化流光 UI，多语言一键切换（英、波斯、俄、中、土耳其、阿拉伯语，支持 RTL）。 |
| 📜 **透明审计日志** | 实时记录所有流量变更、支持日志即时刷新与一键安全清空。 |

---

## ⚡ 一键极速安装 (Ubuntu / Debian)

在服务器上以 `root` 权限执行：

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/a-salemi/Virtualizor-Traffic-Rollover/main/install.sh)"
```

---

## 🔄 系统平滑升级

更新至最新版本且不影响已有配置与数据：

```bash
cd /opt/virturoll && git pull && ./venv/bin/pip install -r backend/requirements.txt && systemctl restart virturoll
```

---

## ⚙️ Virtualizor 多面板配置指南

1. 登录 **Virtualizor 管理后台**，进入 **Configuration** -> **API Credentials** 并创建 API 凭据。
2. **务必注意：** 在 **Allowed IPs** 中填写 VirtuRoll 服务器公网 IP（若本机运行请填 `127.0.0.1`）。
3. 打开 VirtuRoll 控制面板，进入**面板与节点** -> **+ 添加面板**。
4. 填写主机 IP、端口（`4085`）、API Key 及 API Password，保存并完成自动测试。

---

## 🤖 Telegram 机器人与备份配置

1. 在 Telegram 中联系 [@BotFather](https://t.me/BotFather) 获取 **Bot Token**。
2. 通过 [@userinfobot](https://t.me/userinfobot) 获取您的 **Chat ID**。
3. 在 VirtuRoll **系统设置** -> **Telegram 机器人通知** 中填写配置并测试。
4. 在**备份与恢复**区域点击**发送备份至 Telegram**，机器人将直接把完整备份文件发送给您。

---

## 🛠️ 系统服务管理

```bash
sudo systemctl status virturoll   # 查看状态
sudo journalctl -u virturoll -f   # 查看实时日志
sudo systemctl restart virturoll  # 重启服务
sudo systemctl stop virturoll     # 停止服务
```

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。  
Copyright (c) 2026 Amir Salemi.
