from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import public_user
from backend.core import config
from backend.core.db import (
    audit,
    get_conn,
    now_iso,
    set_setting,
    signup_allowed,
)
from backend.core.deps import require_admin
from backend.core.security import (
    hash_password,
    validate_password_strength,
    validate_username,
)
from backend.models.schemas import (
    CreateUserRequest,
    SettingsUpdate,
    UpdateUserRequest,
)
from backend.services.documents import delete_document

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)

ROLES = {"admin", "user"}


def _admin_count(conn, excluding: int | None = None) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'admin' "
        "AND is_active = 1 AND id != ?",
        (excluding or -1,),
    ).fetchone()[0]


@router.get("/stats")
def stats():

    with get_conn() as conn:
        users = conn.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(role = 'admin') AS admins, "
            "SUM(is_active = 0) AS disabled FROM users"
        ).fetchone()

        docs = conn.execute(
            "SELECT COUNT(*) AS total, "
            "COALESCE(SUM(size_bytes), 0) AS bytes, "
            "COALESCE(SUM(chunks), 0) AS chunks FROM documents"
        ).fetchone()

        by_type = conn.execute(
            "SELECT file_type, COUNT(*) AS count FROM documents "
            "GROUP BY file_type ORDER BY count DESC"
        ).fetchall()

        per_user = conn.execute(
            "SELECT u.username, u.quota_mb, "
            "COUNT(d.id) AS documents, "
            "COALESCE(SUM(d.size_bytes), 0) AS bytes "
            "FROM users u LEFT JOIN documents d ON d.owner_id = u.id "
            "GROUP BY u.id ORDER BY bytes DESC"
        ).fetchall()

        queries = conn.execute(
            "SELECT COUNT(*) FROM audit_log "
            "WHERE action = 'chat.query'"
        ).fetchone()[0]

    return {
        "users": dict(users),
        "documents": dict(docs),
        "by_type": [dict(r) for r in by_type],
        "per_user": [dict(r) for r in per_user],
        "chat_queries": queries,
        "allow_signup": signup_allowed(),
    }


# ------------------------------------------------------------------
# Users
# ------------------------------------------------------------------

@router.get("/users")
def list_users():

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT u.*, COUNT(d.id) AS documents, "
            "COALESCE(SUM(d.size_bytes), 0) AS storage_bytes "
            "FROM users u LEFT JOIN documents d ON d.owner_id = u.id "
            "GROUP BY u.id ORDER BY u.created_at"
        ).fetchall()

    return {
        "users": [
            {
                **public_user(r),
                "documents": r["documents"],
                "storage_bytes": r["storage_bytes"],
            }
            for r in rows
        ]
    }


@router.post("/users", status_code=201)
def create_user(request: CreateUserRequest, admin=Depends(require_admin)):

    username = request.username.strip()

    if request.role not in ROLES:
        raise HTTPException(status_code=400, detail="Invalid role.")

    try:
        validate_username(username)
        validate_password_strength(request.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    with get_conn() as conn:
        if conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone():
            raise HTTPException(
                status_code=409, detail="Username already exists."
            )

        conn.execute(
            "INSERT INTO users "
            "(username, password_hash, role, quota_mb, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                username,
                hash_password(request.password),
                request.role,
                request.quota_mb or config.DEFAULT_USER_QUOTA_MB,
                now_iso(),
            ),
        )

    audit(admin, "admin.user.create", f"{username} ({request.role})")

    return {"created": username}


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    request: UpdateUserRequest,
    admin=Depends(require_admin),
):

    with get_conn() as conn:
        target = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if target is None:
            raise HTTPException(status_code=404, detail="No such user.")

        updates, params = [], []
        revoke = False

        if request.role is not None:
            if request.role not in ROLES:
                raise HTTPException(
                    status_code=400, detail="Invalid role."
                )
            updates.append("role = ?")
            params.append(request.role)

        if request.is_active is not None:
            updates.append("is_active = ?")
            params.append(int(request.is_active))
            revoke = revoke or not request.is_active

        if request.quota_mb is not None:
            updates.append("quota_mb = ?")
            params.append(request.quota_mb)

        if request.new_password is not None:
            try:
                validate_password_strength(request.new_password)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
            updates.append("password_hash = ?")
            params.append(hash_password(request.new_password))
            updates.append("failed_attempts = 0")
            updates.append("locked_until = NULL")
            revoke = True

        # Never lock the system out of administration.
        loses_admin = target["role"] == "admin" and (
            request.role == "user" or request.is_active is False
        )

        if loses_admin and _admin_count(conn, excluding=user_id) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one active admin must remain.",
            )

        if revoke or request.role is not None:
            updates.append("token_version = token_version + 1")

        if updates:
            conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                (*params, user_id),
            )

    changed = request.model_dump(exclude_none=True)
    changed.pop("new_password", None)
    if request.new_password is not None:
        changed["password"] = "reset"

    audit(admin, "admin.user.update", f"{target['username']}: {changed}")

    return {"updated": user_id}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin=Depends(require_admin)):

    if user_id == admin["id"]:
        raise HTTPException(
            status_code=400, detail="You cannot delete yourself."
        )

    with get_conn() as conn:
        target = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if target is None:
            raise HTTPException(status_code=404, detail="No such user.")

        if (
            target["role"] == "admin"
            and _admin_count(conn, excluding=user_id) == 0
        ):
            raise HTTPException(
                status_code=400,
                detail="At least one active admin must remain.",
            )

        docs = conn.execute(
            "SELECT * FROM documents WHERE owner_id = ?", (user_id,)
        ).fetchall()

    for doc in docs:
        delete_document(dict(doc))

    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    audit(admin, "admin.user.delete", target["username"])

    return {"deleted": user_id, "documents_removed": len(docs)}


# ------------------------------------------------------------------
# Documents (all users)
# ------------------------------------------------------------------

@router.get("/documents")
def all_documents():

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT d.*, u.username AS owner FROM documents d "
            "JOIN users u ON u.id = d.owner_id "
            "ORDER BY d.created_at DESC"
        ).fetchall()

    return {"documents": [dict(r) for r in rows]}


@router.delete("/documents/{document_id}")
def admin_delete_document(
    document_id: str, admin=Depends(require_admin)
):

    with get_conn() as conn:
        doc = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()

    if doc is None:
        raise HTTPException(status_code=404, detail="No such document.")

    delete_document(dict(doc))
    audit(admin, "admin.document.delete", f"{doc['filename']} ({document_id})")

    return {"deleted": document_id}


# ------------------------------------------------------------------
# Settings + audit
# ------------------------------------------------------------------

@router.put("/settings")
def update_settings(
    request: SettingsUpdate, admin=Depends(require_admin)
):

    set_setting(
        "allow_signup", "true" if request.allow_signup else "false"
    )
    audit(admin, "admin.settings", f"allow_signup={request.allow_signup}")

    return {"allow_signup": request.allow_signup}


@router.get("/audit")
def audit_log(limit: int = 200, action: str | None = None):

    limit = max(1, min(limit, 1000))

    query = "SELECT * FROM audit_log"
    params: list = []

    if action:
        query += " WHERE action LIKE ?"
        params.append(f"{action}%")

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    return {"events": [dict(r) for r in rows]}
