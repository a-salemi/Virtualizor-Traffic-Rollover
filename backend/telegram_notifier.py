from __future__ import annotations
import logging
import requests
from typing import Optional
from backend.database import SessionLocal, get_setting

logger = logging.getLogger("virturoll.telegram")

class TelegramNotifier:
    def get_config(self, db=None):
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            enabled = get_setting(db, "tg_enabled", "false").lower() == "true"
            token = get_setting(db, "tg_token", "").strip()
            chat_id = get_setting(db, "tg_chat_id", "").strip()
            proxy = get_setting(db, "tg_proxy", "").strip()
            api_server = get_setting(db, "tg_api_server", "https://api.telegram.org").strip().rstrip("/")
            lang = get_setting(db, "tg_lang", "fa").strip()
            return {
                "enabled": enabled,
                "token": token,
                "chat_id": chat_id,
                "proxy": proxy,
                "api_server": api_server or "https://api.telegram.org",
                "lang": lang
            }
        finally:
            if close_db:
                db.close()

    def send_message(self, text: str, db=None, token: str = None, chat_id: str = None, proxy: str = None, api_server: str = None, force: bool = False) -> dict:
        cfg = self.get_config(db)
        if token:
            cfg["token"] = token
        if chat_id:
            cfg["chat_id"] = chat_id
        if proxy is not None:
            cfg["proxy"] = proxy
        if api_server:
            cfg["api_server"] = api_server

        if not cfg["enabled"] and not force:
            return {"success": False, "message": "Telegram notifications are disabled."}
        if not cfg["token"] or not cfg["chat_id"]:
            return {"success": False, "message": "Telegram Bot Token or Chat ID is missing."}

        url = f"{cfg['api_server']}/bot{cfg['token']}/sendMessage"
        payload = {
            "chat_id": cfg["chat_id"],
            "text": text,
            "parse_mode": "HTML"
        }

        proxies = {}
        if cfg["proxy"]:
            proxy_url = cfg["proxy"].strip()
            # If socks5 is used, socks5h ensures DNS resolution happens remotely through the proxy
            if proxy_url.startswith("socks5://"):
                proxy_url = "socks5h://" + proxy_url[9:]
            elif proxy_url.startswith("socks4://"):
                proxy_url = "socks4a://" + proxy_url[9:]
            proxies = {"http": proxy_url, "https": proxy_url}

        try:
            res = requests.post(url, json=payload, proxies=proxies, timeout=12)
            data = res.json()
            if res.ok and data.get("ok"):
                logger.info("Telegram notification delivered successfully.")
                return {"success": True, "message": "Notification sent successfully!"}
            else:
                err = data.get("description", "Unknown Telegram API error")
                logger.error(f"Telegram API error: {err}")
                return {"success": False, "message": f"Telegram Error: {err}"}
        except requests.exceptions.ProxyError as e:
            return {"success": False, "message": f"SOCKS5 Proxy connection failed: {e}"}
        except requests.exceptions.ConnectTimeout:
            return {"success": False, "message": "Telegram connection timed out. If Telegram is filtered, please configure a SOCKS5 proxy or custom API server."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def notify_rollover(self, vpsid: str, hostname: str, prev_limit: float, prev_used: float, new_limit: float):
        cfg = self.get_config()
        if not cfg["enabled"]:
            return

        if cfg["lang"] == "fa":
            msg = (
                f"🛡️ <b>ویرتو رول | رول‌اور خودکار ترافیک</b>\n\n"
                f"🖥️ سرور: <b>{hostname}</b> (شناسه: <code>#{vpsid}</code>)\n"
                f"📊 سقف دوره قبل: <b>{prev_limit:,.1f} GB</b>\n"
                f"📉 مصرف دوره قبل: <b>{prev_used:,.1f} GB</b>\n"
                f"✅ <b>سقف جدید اعمال‌شده: {new_limit:,.1f} GB</b>\n\n"
                f"<i>ترافیک باقیمانده بدون ریست ماهانه برای کاربر حفظ شد.</i>"
            )
        else:
            msg = (
                f"🛡️ <b>VirtuRoll | Bandwidth Rollover Alert</b>\n\n"
                f"🖥️ VPS: <b>{hostname}</b> (ID: <code>#{vpsid}</code>)\n"
                f"📊 Previous Quota: <b>{prev_limit:,.1f} GB</b>\n"
                f"📉 Consumed: <b>{prev_used:,.1f} GB</b>\n"
                f"✅ <b>New Active Limit: {new_limit:,.1f} GB</b>\n\n"
                f"<i>Remaining traffic retained across monthly reset.</i>"
            )
        self.send_message(msg)

    def notify_topup(self, vpsid: str, hostname: str, added_gb: float, new_limit: float):
        cfg = self.get_config()
        if not cfg["enabled"]:
            return

        if cfg["lang"] == "fa":
            msg = (
                f"⚡ <b>ویرتو رول | شارژ ترافیک سرور مجازی</b>\n\n"
                f"🖥️ سرور: <b>{hostname}</b> (شناسه: <code>#{vpsid}</code>)\n"
                f"➕ حجم اضافه شده: <b>+{added_gb:,.1f} GB</b>\n"
                f"📈 سقف ترافیک جدید: <b>{new_limit:,.1f} GB</b>\n"
            )
        else:
            msg = (
                f"⚡ <b>VirtuRoll | Traffic Top-Up Alert</b>\n\n"
                f"🖥️ VPS: <b>{hostname}</b> (ID: <code>#{vpsid}</code>)\n"
                f"➕ Added Traffic: <b>+{added_gb:,.1f} GB</b>\n"
                f"📈 New Active Quota: <b>{new_limit:,.1f} GB</b>\n"
            )
        self.send_message(msg)

telegram_notifier = TelegramNotifier()
