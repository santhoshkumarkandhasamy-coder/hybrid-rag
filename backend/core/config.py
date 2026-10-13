"""Central configuration (environment driven)."""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# ------------------------------------------------------------------
# Storage
# ------------------------------------------------------------------

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
FAISS_DIR = DATA_DIR / "faiss"
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "app.db")))

for _directory in (DATA_DIR, UPLOAD_DIR, FAISS_DIR):
    _directory.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Limits
# ------------------------------------------------------------------

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
DEFAULT_USER_QUOTA_MB = int(os.getenv("DEFAULT_USER_QUOTA_MB", "500"))

# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------

TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))
MAX_FAILED_LOGINS = int(os.getenv("MAX_FAILED_LOGINS", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "15"))
MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
ALLOW_SIGNUP_DEFAULT = os.getenv("ALLOW_SIGNUP", "false").lower() == "true"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def _load_secret_key() -> str:
    """Use SECRET_KEY from env, otherwise persist a generated one."""

    from_env = os.getenv("SECRET_KEY")

    if from_env:
        return from_env

    key_file = DATA_DIR / ".secret_key"

    if key_file.exists():
        return key_file.read_text().strip()

    key = secrets.token_urlsafe(64)
    key_file.write_text(key)

    try:
        key_file.chmod(0o600)
    except OSError:
        pass

    return key


SECRET_KEY = _load_secret_key()
JWT_ALGORITHM = "HS256"


# ------------------------------------------------------------------
# Optional external services. With none configured the app runs fully
# offline: local SQLite knowledge graph + extractive answers.
# ------------------------------------------------------------------

USE_OPENAI = bool(
    os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_CHAT_MODEL")
)

USE_NEO4J = bool(
    os.getenv("NEO4J_URI")
    and os.getenv("NEO4J_USERNAME")
    and os.getenv("NEO4J_PASSWORD")
)
