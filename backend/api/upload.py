from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse

from backend.core import config
from backend.core.db import audit, get_conn, storage_used_bytes
from backend.core.deps import get_current_user, get_owned_document
from backend.ingestion.file_loader import SUPPORTED_EXTENSIONS
from backend.services.documents import (
    delete_document,
    document_dir,
    ingest_upload,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILES_PER_REQUEST = 20


@router.get("/supported-types")
def supported_types():
    return {
        "extensions": sorted(SUPPORTED_EXTENSIONS),
        "max_file_mb": config.MAX_FILE_SIZE_MB,
    }


# Plain `def` so blocking ingestion runs in the threadpool.
@router.post("/upload")
def upload_documents(
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    """Upload one or many files. Each file is processed
    independently and reported separately."""

    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Max {MAX_FILES_PER_REQUEST} files per upload.",
        )

    results = []

    for upload in files:
        try:
            result = ingest_upload(user, upload)
            results.append({"status": "completed", **result})

        except HTTPException as exc:
            results.append(
                {
                    "status": "failed",
                    "filename": upload.filename,
                    "error": exc.detail,
                }
            )

        except Exception as exc:
            results.append(
                {
                    "status": "failed",
                    "filename": upload.filename,
                    "error": f"Ingestion failed: {exc}",
                }
            )

    return {"results": results}


@router.get("")
def list_documents(user=Depends(get_current_user)):

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM documents WHERE owner_id = ? "
            "ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()

    return {
        "documents": [dict(r) for r in rows],
        "storage_used_bytes": storage_used_bytes(user["id"]),
        "quota_bytes": user["quota_mb"] * 1024 * 1024,
    }


@router.get("/{document_id}/text")
def document_text(document_id: str, user=Depends(get_current_user)):

    doc = get_owned_document(document_id, user)

    path = document_dir(doc["owner_id"], doc["id"]) / "text.txt"

    if not path.exists():
        raise HTTPException(status_code=404, detail="Text not found.")

    return {
        "filename": doc["filename"],
        "text": path.read_text(encoding="utf-8"),
    }


@router.get("/{document_id}/download")
def download_document(
    document_id: str, user=Depends(get_current_user)
):

    doc = get_owned_document(document_id, user)

    path = (
        document_dir(doc["owner_id"], doc["id"]) / doc["filename"]
    )

    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing.")

    return FileResponse(path, filename=doc["filename"])


@router.delete("/{document_id}")
def remove_document(document_id: str, user=Depends(get_current_user)):

    doc = get_owned_document(document_id, user)

    delete_document(doc)
    audit(user, "document.delete", f"{doc['filename']} ({doc['id']})")

    return {"deleted": document_id}
