import os
from pathlib import Path
import random

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Load environment variables manually if python-dotenv is not installed
def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

HOST = os.getenv("HOST", "0.0.0.0")
# If no port is specified, generate a stable random port in high range (25000-58000)
DEFAULT_RANDOM_PORT = random.randint(25000, 58000)
PORT = int(os.getenv("PORT", DEFAULT_RANDOM_PORT))

SECRET_KEY = os.getenv("SECRET_KEY", "virturoll-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123456")

# Virtualizor API connection
VIRTUALIZOR_IP = os.getenv("VIRTUALIZOR_IP", "127.0.0.1")
VIRTUALIZOR_PORT = int(os.getenv("VIRTUALIZOR_PORT", 4085))
VIRTUALIZOR_API_KEY = os.getenv("VIRTUALIZOR_API_KEY", "")
VIRTUALIZOR_API_PASS = os.getenv("VIRTUALIZOR_API_PASS", "")

POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", 5))
ROLLOVER_WINDOW_START_DAY = int(os.getenv("ROLLOVER_WINDOW_START_DAY", 27))
ROLLOVER_WINDOW_END_DAY = int(os.getenv("ROLLOVER_WINDOW_END_DAY", 5))

DATABASE_URL = f"sqlite:///{DATA_DIR / 'app.db'}"
