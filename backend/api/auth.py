from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from backend.core import config
from backend.core.db import audit, get_conn, now_iso, signup_allowed
from backend.core.deps import get_current_user
from backend.core.security import (
    create_token,
    hash_password,
    validate_password_strength,
    validate_username,
    verify_password,
)
from backend.models.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Hash used to keep login timing similar for unknown usernames
_DUMMY_HASH = hash_password("dummy-password-1")


def public_user(user) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "is_active": bool(user["is_active"]),
        "quota_mb": user["quota_mb"],
        "created_at": user["created_at"],
        "last_login": user["last_login"],
    }


@router.post("/login")
def login(request: LoginRequest):

    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (request.username.strip(),),
        ).fetchone()

        invalid = HTTPException(
            status_code=401, detail="Invalid username or password."
        )

        if user is None:
            verify_password(request.password, _DUMMY_HASH)
            audit(None, "login.failed", request.username[:64])
            raise invalid

        now = datetime.now(timezone.utc)

        if user["locked_until"] and (
            datetime.fromisoformat(user["locked_until"]) > now
        ):
            raise HTTPException(
                status_code=429,
                detail="Account temporarily locked. Try again later.",
            )

        if not verify_password(request.password, user["password_hash"]):

            attempts = user["failed_attempts"] + 1
            locked_until = None

            if attempts >= config.MAX_FAILED_LOGINS:
                locked_until = (
                    now + timedelta(minutes=config.LOCKOUT_MINUTES)
                ).isoformat()
                attempts = 0

            conn.execute(
                "UPDATE users SET failed_attempts = ?, "
                "locked_until = ? WHERE id = ?",
                (attempts, locked_until, user["id"]),
            )
            conn.commit()
            audit(user, "login.failed")
            raise invalid

        if not user["is_active"]:
            raise HTTPException(
                status_code=403, detail="Account is disabled."
            )

        conn.execute(
            "UPDATE users SET failed_attempts = 0, "
            "locked_until = NULL, last_login = ? WHERE id = ?",
            (now_iso(), user["id"]),
        )

    audit(user, "login.success")

    return {
        "access_token": create_token(
            user["id"], user["token_version"]
        ),
        "token_type": "bearer",
        "user": public_user(user),
    }


@router.get("/config")
def auth_config():
    """Public: lets the UI know whether to show the sign-up form."""
    return {"allow_signup": signup_allowed()}


@router.post("/register", status_code=201)
def register(request: RegisterRequest):

    if not signup_allowed():
        raise HTTPException(
            status_code=403,
            detail="Self-registration is disabled. Ask an admin.",
        )

    username = request.username.strip()

    try:
        validate_username(username)
        validate_password_strength(request.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    with get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()

        if exists:
            raise HTTPException(
                status_code=409, detail="Username already taken."
            )

        conn.execute(
            "INSERT INTO users "
            "(username, password_hash, role, quota_mb, created_at) "
            "VALUES (?, ?, 'user', ?, ?)",
            (
                username,
                hash_password(request.password),
                config.DEFAULT_USER_QUOTA_MB,
                now_iso(),
            ),
        )

    audit({"id": None, "username": username}, "user.register")

    return {"message": "Account created. You can now sign in."}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return public_user(user)


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    user=Depends(get_current_user),
):

    if not verify_password(
        request.current_password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=400, detail="Current password is incorrect."
        )

    try:
        validate_password_strength(request.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, "
            "token_version = token_version + 1 WHERE id = ?",
            (hash_password(request.new_password), user["id"]),
        )
        refreshed = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user["id"],)
        ).fetchone()

    audit(user, "password.change")

    # Old tokens are now invalid; hand back a fresh one.
    return {
        "access_token": create_token(
            refreshed["id"], refreshed["token_version"]
        ),
        "token_type": "bearer",
    }
