from __future__ import annotations
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt
import jwt
from jwt.exceptions import PyJWTError as JWTError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    POLL_INTERVAL_MINUTES,
    PORT,
    HOST
)
from backend.database import init_db, get_db, SessionLocal, User, VPSTraffic, AuditLog, VirtualizorPanel
from backend.virtualizor_api import virtualizor_client
from backend.guardian import guardian

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("virturoll.server")

# Security helpers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# App initialization
app = FastAPI(title="Virtualizor Traffic Rollover", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()

def run_scheduled_sync():
    logger.info("Executing scheduled traffic guardian sync...")
    db = SessionLocal()
    try:
        res = guardian.sync_and_check(db)
        logger.info(f"Sync complete: {res}")
    except Exception as e:
        logger.error(f"Error in background sync: {e}")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()
    
    # Initialize default admin if not exists & load dynamic settings
    db = SessionLocal()
    try:
        virtualizor_client.load_from_db(db)
        admin = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not admin:
            hashed = get_password_hash(ADMIN_PASSWORD)
            new_admin = User(username=ADMIN_USERNAME, hashed_password=hashed)
            db.add(new_admin)
            db.commit()
            logger.info(f"Default admin user '{ADMIN_USERNAME}' created.")
    finally:
        db.close()

    # Start background polling scheduler
    scheduler.add_job(run_scheduled_sync, "interval", minutes=POLL_INTERVAL_MINUTES, id="traffic_sync")
    scheduler.start()
    logger.info(f"Background traffic watcher scheduled every {POLL_INTERVAL_MINUTES} minutes.")

@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()

# Dependency: Current User Authentication
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("virturoll_token")
    auth_header = request.headers.get("Authorization")
    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required."
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user

# --- Pydantic Request Models ---
class LoginRequest(BaseModel):
    username: str
    password: str

class AddTrafficRequest(BaseModel):
    extra_gb: float

# --- Authentication Endpoints ---
@app.post("/api/auth/login")
def login(creds: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == creds.username).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(data={"sub": user.username})
    response.set_cookie(
        key="virturoll_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # can be True behind HTTPS reverse proxy
    )
    return {"success": True, "token": token, "username": user.username}

@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(key="virturoll_token")
    return {"success": True, "message": "Logged out successfully."}

@app.get("/api/auth/me")
def get_me(user: User = Depends(get_current_user)):
    return {"username": user.username, "last_login": user.last_login}

# --- VPS & Traffic Endpoints ---
@app.get("/api/vps")
def list_vps(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(VPSTraffic).all()
    return {"vps": [rec.to_dict() for rec in records]}

@app.post("/api/vps/{vpsid}/add-traffic")
def add_traffic(vpsid: str, payload: AddTrafficRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.extra_gb <= 0:
        raise HTTPException(status_code=400, detail="Bandwidth to add must be greater than 0.")
    res = guardian.add_bandwidth(db, vpsid, payload.extra_gb)
    if not res.get("success"):
        return JSONResponse(status_code=400, content=res)
    return res

@app.post("/api/system/sync")
def trigger_sync(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    res = guardian.sync_and_check(db)
    return res

@app.get("/api/logs")
def list_logs(limit: int = 50, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return {"logs": [l.to_dict() for l in logs]}

@app.get("/api/system/status")
def system_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_vps = db.query(VPSTraffic).count()
    records = db.query(VPSTraffic).all()
    total_managed_bw = sum(r.total_purchased_gb for r in records)
    total_used_bw = sum(r.current_month_used_gb for r in records)
    total_remaining_bw = sum(r.remaining_gb for r in records)
    total_panels = db.query(VirtualizorPanel).count()

    return {
        "status": "online",
        "api_configured": virtualizor_client.is_configured(),
        "total_vps": total_vps,
        "total_panels": total_panels or (1 if virtualizor_client.is_configured() else 0),
        "total_managed_bw_gb": round(total_managed_bw, 2),
        "total_used_bw_gb": round(total_used_bw, 2),
        "total_remaining_bw_gb": round(total_remaining_bw, 2),
        "poll_interval_minutes": POLL_INTERVAL_MINUTES,
        "port": PORT
    }

# --- Multi-Panel Virtualizor Management Endpoints ---
class PanelCreateRequest(BaseModel):
    name: str
    ip: str
    port: int = 4085
    api_key: str
    api_pass: str

class PanelUpdateRequest(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    api_key: Optional[str] = None
    api_pass: Optional[str] = None

@app.get("/api/panels")
def list_panels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    panels = db.query(VirtualizorPanel).all()
    if not panels and virtualizor_client.is_configured():
        p = VirtualizorPanel(
            name="Primary Node",
            ip=virtualizor_client.ip,
            port=virtualizor_client.port or 4085,
            api_key=virtualizor_client.api_key or "",
            api_pass=virtualizor_client.api_pass or "",
            is_active=True,
            last_status="online",
            vps_count=db.query(VPSTraffic).count()
        )
        db.add(p)
        db.commit()
        panels = [p]
    return {"panels": [p.to_dict() for p in panels]}

@app.post("/api/panels")
def create_panel(payload: PanelCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.virtualizor_api import clean_host_and_port
    clean_ip, clean_port = clean_host_and_port(payload.ip, payload.port)
    test_res = virtualizor_client.test_connection_params(clean_ip, clean_port, payload.api_key, payload.api_pass)
    status_str = "online" if test_res.get("success") else "error"
    vps_cnt = test_res.get("vps_count", 0)

    panel = VirtualizorPanel(
        name=payload.name.strip() or clean_ip,
        ip=clean_ip,
        port=clean_port,
        api_key=payload.api_key.strip(),
        api_pass=payload.api_pass.strip(),
        last_status=status_str,
        vps_count=vps_cnt,
        last_sync=datetime.utcnow() if test_res.get("success") else None
    )
    db.add(panel)
    db.commit()
    db.refresh(panel)
    return {"success": True, "panel": panel.to_dict(), "test_result": test_res}

@app.put("/api/panels/{panel_id}")
def update_panel(panel_id: int, payload: PanelUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.virtualizor_api import clean_host_and_port
    panel = db.query(VirtualizorPanel).filter(VirtualizorPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found.")
    if payload.name:
        panel.name = payload.name.strip()
    if payload.ip:
        p_val = payload.port or panel.port
        clean_ip, clean_port = clean_host_and_port(payload.ip, p_val)
        panel.ip = clean_ip
        panel.port = clean_port
    elif payload.port:
        panel.port = payload.port
    if payload.api_key:
        panel.api_key = payload.api_key.strip()
    if payload.api_pass and payload.api_pass.strip():
        panel.api_pass = payload.api_pass.strip()

    db.commit()
    return {"success": True, "panel": panel.to_dict()}

@app.delete("/api/panels/{panel_id}")
def delete_panel(panel_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    panel = db.query(VirtualizorPanel).filter(VirtualizorPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found.")
    db.delete(panel)
    db.commit()
    return {"success": True, "message": "Panel deleted successfully."}

@app.post("/api/panels/{panel_id}/test")
def test_panel_connection(panel_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    panel = db.query(VirtualizorPanel).filter(VirtualizorPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found.")
    res = virtualizor_client.test_connection_params(panel.ip, panel.port, panel.api_key, panel.api_pass)
    panel.last_status = "online" if res.get("success") else "error"
    if res.get("success"):
        panel.vps_count = res.get("vps_count", panel.vps_count)
    db.commit()
    return res

@app.post("/api/panels/{panel_id}/sync")
def sync_specific_panel(panel_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    panel = db.query(VirtualizorPanel).filter(VirtualizorPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found.")
    virtualizor_client.update_credentials(panel.ip, panel.port, panel.api_key, panel.api_pass)
    res = guardian.sync_and_check(db)
    panel.last_sync = datetime.utcnow()
    if res.get("status") == "success":
        panel.last_status = "online"
        panel.vps_count = res.get("total_vps", panel.vps_count)
    else:
        panel.last_status = "error"
    db.commit()
    return res

# --- Virtualizor Node Management Endpoints ---
class NodeSettingsRequest(BaseModel):
    ip: str
    port: int = 4085
    api_key: str
    api_pass: str

@app.get("/api/settings/node")
def get_node_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.database import get_setting
    ip = get_setting(db, "virtualizor_ip", virtualizor_client.ip)
    port = int(get_setting(db, "virtualizor_port", str(virtualizor_client.port)))
    api_key = get_setting(db, "virtualizor_api_key", virtualizor_client.api_key)
    return {
        "ip": ip,
        "port": port,
        "api_key": api_key,
        "is_configured": virtualizor_client.is_configured()
    }

@app.post("/api/settings/node")
def save_node_settings(payload: NodeSettingsRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.database import set_setting, get_setting
    from backend.virtualizor_api import clean_host_and_port
    
    clean_ip, clean_port = clean_host_and_port(payload.ip, payload.port)
    set_setting(db, "virtualizor_ip", clean_ip)
    set_setting(db, "virtualizor_port", str(clean_port))
    set_setting(db, "virtualizor_api_key", payload.api_key.strip())
    
    if payload.api_pass and payload.api_pass.strip():
        final_pass = payload.api_pass.strip()
        set_setting(db, "virtualizor_api_pass", final_pass)
    else:
        final_pass = get_setting(db, "virtualizor_api_pass", virtualizor_client.api_pass)
    
    virtualizor_client.update_credentials(clean_ip, clean_port, payload.api_key, final_pass)
    return {"success": True, "message": "Virtualizor credentials saved successfully!"}

@app.post("/api/settings/test-connection")
def test_node_connection(payload: NodeSettingsRequest, user: User = Depends(get_current_user)):
    return virtualizor_client.test_connection_params(payload.ip, payload.port, payload.api_key, payload.api_pass)

# --- Hardware Telemetry ---
from backend.telemetry import get_system_telemetry
from backend.telegram_notifier import telegram_notifier

@app.get("/api/system/telemetry")
def system_telemetry(user: User = Depends(get_current_user)):
    return get_system_telemetry()

# --- Telegram Bot Alert Settings ---
class TelegramSettingsRequest(BaseModel):
    enabled: bool
    token: str
    chat_id: str
    proxy: Optional[str] = ""
    api_server: Optional[str] = "https://api.telegram.org"
    lang: Optional[str] = "fa"

@app.get("/api/settings/telegram")
def get_telegram_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return telegram_notifier.get_config(db)

@app.post("/api/settings/telegram")
def save_telegram_settings(payload: TelegramSettingsRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.database import set_setting
    set_setting(db, "tg_enabled", "true" if payload.enabled else "false")
    set_setting(db, "tg_token", payload.token.strip())
    set_setting(db, "tg_chat_id", payload.chat_id.strip())
    set_setting(db, "tg_proxy", payload.proxy.strip() if payload.proxy else "")
    set_setting(db, "tg_api_server", payload.api_server.strip() if payload.api_server else "https://api.telegram.org")
    set_setting(db, "tg_lang", payload.lang.strip() if payload.lang else "fa")
    return {"success": True, "message": "Telegram settings saved successfully!"}

class TelegramTestRequest(BaseModel):
    token: Optional[str] = ""
    chat_id: Optional[str] = ""
    proxy: Optional[str] = ""
    api_server: Optional[str] = "https://api.telegram.org"

@app.post("/api/settings/telegram/test")
def test_telegram(payload: Optional[TelegramTestRequest] = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cfg = telegram_notifier.get_config(db)
    tok = (payload.token.strip() if payload and payload.token else "") or cfg["token"]
    cid = (payload.chat_id.strip() if payload and payload.chat_id else "") or cfg["chat_id"]
    prx = (payload.proxy.strip() if payload and payload.proxy is not None else "") or cfg["proxy"]
    srv = (payload.api_server.strip() if payload and payload.api_server else "") or cfg["api_server"]

    if not tok or not cid:
        raise HTTPException(status_code=400, detail="Bot Token and Chat ID are required to test notification.")

    test_msg = (
        "🔔 <b>VirtuRoll Notification Test</b>\n\n"
        "✅ ارتباط ربات تلگرام با سامانه مدیریت ترافیک با موفقیت برقرار شد!\n"
        "از این پس کلیه هشدارهای رول‌اور و شارژ ترافیک در این کانال/گروه ارسال خواهند شد."
        if cfg["lang"] == "fa" else
        "🔔 <b>VirtuRoll Notification Test</b>\n\n"
        "✅ Telegram bot connected successfully to VirtuRoll!\n"
        "Real-time rollover and top-up alerts will be delivered here."
    )
    res = telegram_notifier.send_message(test_msg, db, token=tok, chat_id=cid, proxy=prx, api_server=srv, force=True)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

# --- Admin Password Change ---
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@app.post("/api/auth/change-password")
def change_password(payload: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"success": True, "message": "Password updated successfully!"}

# --- Dashboard Web Port Change ---
class PortChangeRequest(BaseModel):
    port: int

@app.post("/api/settings/port")
def change_port(payload: PortChangeRequest, user: User = Depends(get_current_user)):
    if payload.port < 1024 or payload.port > 65535:
        raise HTTPException(status_code=400, detail="Port must be between 1024 and 65535.")
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        import re
        new_content = re.sub(r"^PORT=\d+", f"PORT={payload.port}", content, flags=re.MULTILINE)
        env_path.write_text(new_content, encoding="utf-8")
    
    # Also update systemd service if running natively on Linux
    service_file = Path("/etc/systemd/system/virturoll.service")
    if service_file.exists():
        try:
            s_content = service_file.read_text(encoding="utf-8")
            import re
            s_content = re.sub(r"--port \d+", f"--port {payload.port}", s_content)
            service_file.write_text(s_content, encoding="utf-8")
            import subprocess
            subprocess.run(["systemctl", "daemon-reload"], check=False)
        except Exception:
            pass

    return {
        "success": True,
        "message": f"Port set to {payload.port}. Please run 'systemctl restart virturoll' to apply changes."
    }

# --- Backup & Restore ---
@app.get("/api/settings/backup")
def download_backup(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vps_data = [v.to_dict() for v in db.query(VPSTraffic).all()]
    from backend.database import NodeSetting
    settings_data = {s.key: s.value for s in db.query(NodeSetting).all()}
    backup = {
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "settings": settings_data,
        "vps": vps_data
    }
    return JSONResponse(
        content=backup,
        headers={"Content-Disposition": f"attachment; filename=virturoll-backup-{datetime.utcnow().strftime('%Y%m%d-%H%M')}.json"}
    )

@app.post("/api/settings/backup/send-telegram")
def send_backup_to_telegram(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cfg = telegram_notifier.get_config(db)
    if not cfg["enabled"]:
        raise HTTPException(status_code=400, detail="Telegram bot is not enabled.")
    vps_count = db.query(VPSTraffic).count()
    msg = (
        f"📦 <b>نسخه پشتیبان سامانه ویرتو رول</b>\n\n"
        f"📅 تاریخ: <code>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>\n"
        f"🖥️ تعداد سرورها: <b>{vps_count}</b>\n"
        f"✅ دیتابیس و تنظیمات فعال است."
    )
    res = telegram_notifier.send_message(msg, db)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return {"success": True, "message": "Backup summary sent to Telegram!"}

# --- Serve Static Frontend ---
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{catchall:path}")
    def serve_spa(catchall: str):
        path = FRONTEND_DIR / catchall
        if path.is_file():
            return FileResponse(path)
        return FileResponse(FRONTEND_DIR / "index.html")
