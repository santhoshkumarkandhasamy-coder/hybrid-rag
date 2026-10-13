"""FastAPI dependencies for authentication and authorisation."""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.db import get_conn
from backend.core.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
):

    unauthorized = HTTPException(
        status_code=401,
        detail="Not authenticated.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
        version = int(payload["ver"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized

    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    if (
        user is None
        or not user["is_active"]
        or user["token_version"] != version
    ):
        raise unauthorized

    return user


def require_admin(user=Depends(get_current_user)):

    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator rights required.",
        )

    return user


def get_owned_document(
    document_id: str, user, admin_override: bool = False
) -> dict:
    """Return a document row if the user owns it.

    Admins only bypass ownership when `admin_override` is set
    (management actions), never for reading content in chat.
    """

    with get_conn() as conn:
        doc = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()

    if doc is None or (
        doc["owner_id"] != user["id"]
        and not (admin_override and user["role"] == "admin")
    ):
        # Same response for missing and foreign documents.
        raise HTTPException(
            status_code=404, detail="Document not found."
        )

    return dict(doc)
