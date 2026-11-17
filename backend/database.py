from datetime import datetime
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class VPSTraffic(Base):
    __tablename__ = "vps_traffic"

    vpsid = Column(String(32), primary_key=True, index=True)
    hostname = Column(String(128), default="")
    ip = Column(String(64), default="")
    
    # Traffic metrics (in Gigabytes)
    total_purchased_gb = Column(Float, default=0.0)
    current_virtualizor_limit_gb = Column(Float, default=0.0)
    current_month_used_gb = Column(Float, default=0.0)
    last_known_used_gb = Column(Float, default=0.0)
    remaining_gb = Column(Float, default=0.0)
    
    last_rollover_period = Column(String(16), default="")
    is_suspended = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "vpsid": self.vpsid,
            "hostname": self.hostname,
            "ip": self.ip,
            "total_purchased_gb": round(self.total_purchased_gb, 2),
            "current_virtualizor_limit_gb": round(self.current_virtualizor_limit_gb, 2),
            "current_month_used_gb": round(self.current_month_used_gb, 2),
            "remaining_gb": round(self.remaining_gb, 2),
            "used_percentage": round((self.current_month_used_gb / self.current_virtualizor_limit_gb * 100) if self.current_virtualizor_limit_gb > 0 else 0, 1),
            "last_rollover_period": self.last_rollover_period,
            "is_suspended": self.is_suspended,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else ""
        }

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(32), index=True) # ROLLOVER, ADD_TRAFFIC, SYNC, AUTH, SYSTEM
    vpsid = Column(String(32), nullable=True)
    message = Column(String(512), nullable=False)
    details = Column(Text, default="{}")

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": self.event_type,
            "vpsid": self.vpsid or "-",
            "message": self.message,
            "details": json.loads(self.details) if self.details else {}
        }

class NodeSetting(Base):
    __tablename__ = "node_settings"

    key = Column(String(64), primary_key=True, index=True)
    value = Column(Text, default="")

def get_setting(db, key: str, default: str = "") -> str:
    item = db.query(NodeSetting).filter(NodeSetting.key == key).first()
    return item.value if item and item.value is not None else default

def set_setting(db, key: str, value: str):
    item = db.query(NodeSetting).filter(NodeSetting.key == key).first()
    if not item:
        item = NodeSetting(key=key, value=value)
        db.add(item)
    else:
        item.value = value
    db.commit()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
