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
from backend.database import init_db, get_db, SessionLocal, User, VPSTraffic, AuditLog
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
        raise HTTPException(status_code=404, detail=res.get("message", "Error adding traffic."))
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

    return {
        "status": "online",
        "api_configured": virtualizor_client.is_configured(),
        "total_vps": total_vps,
        "total_managed_bw_gb": round(total_managed_bw, 2),
        "total_used_bw_gb": round(total_used_bw, 2),
        "total_remaining_bw_gb": round(total_remaining_bw, 2),
        "poll_interval_minutes": POLL_INTERVAL_MINUTES,
        "port": PORT
    }

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
