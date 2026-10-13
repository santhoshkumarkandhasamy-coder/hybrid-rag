"""SQLite persistence: users, documents, settings, audit log."""

import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from backend.core import config
from backend.core.security import hash_password

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    is_active INTEGER NOT NULL DEFAULT 1,
    quota_mb INTEGER NOT NULL,
    token_version INTEGER NOT NULL DEFAULT 0,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    created_at TEXT NOT NULL,
    last_login TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    owner_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    pages INTEGER,
    characters INTEGER DEFAULT 0,
    chunks INTEGER DEFAULT 0,
    entities INTEGER DEFAULT 0,
    relationships INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'processing',
    error TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    user_id INTEGER,
    username TEXT,
    action TEXT NOT NULL,
    detail TEXT
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:

    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


@contextmanager
def get_conn():

    conn = connect()

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and bootstrap the first admin account."""

    with get_conn() as conn:

        conn.executescript(SCHEMA)

        has_users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        if has_users:
            return

        password = config.ADMIN_PASSWORD
        generated = False

        if not password:
            password = secrets.token_urlsafe(12)
            generated = True

        conn.execute(
            """
            INSERT INTO users
                (username, password_hash, role, quota_mb, created_at)
            VALUES (?, ?, 'admin', ?, ?)
            """,
            (
                config.ADMIN_USERNAME,
                hash_password(password),
                config.DEFAULT_USER_QUOTA_MB,
                now_iso(),
            ),
        )

    if generated:
        print(
            "=" * 60
            + f"\nInitial admin created.\n"
            f"  username: {config.ADMIN_USERNAME}\n"
            f"  password: {password}\n"
            "Set ADMIN_PASSWORD in .env to choose your own.\n"
            + "=" * 60,
            flush=True,
        )


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------

def get_setting(key: str, default: str | None = None):

    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()

    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def signup_allowed() -> bool:

    default = "true" if config.ALLOW_SIGNUP_DEFAULT else "false"

    return get_setting("allow_signup", default) == "true"


# ------------------------------------------------------------------
# Audit
# ------------------------------------------------------------------

def audit(user, action: str, detail: str = "") -> None:
    """Record an event. `user` may be a row/dict or None."""

    user_id = user["id"] if user else None
    username = user["username"] if user else None

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log "
            "(ts, user_id, username, action, detail) "
            "VALUES (?, ?, ?, ?, ?)",
            (now_iso(), user_id, username, action, detail),
        )


def storage_used_bytes(user_id: int) -> int:

    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(size_bytes), 0) AS total "
            "FROM documents WHERE owner_id = ?",
            (user_id,),
        ).fetchone()

    return int(row["total"])
