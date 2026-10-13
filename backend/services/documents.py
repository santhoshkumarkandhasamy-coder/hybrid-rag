"""Document lifecycle: ingest, list, delete."""

import logging
import re
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from backend.core import config
from backend.core.db import audit, get_conn, now_iso, storage_used_bytes
from backend.ingestion.chunker import split_text
from backend.ingestion.file_loader import (
    SUPPORTED_EXTENSIONS,
    extract_file_data,
)

logger = logging.getLogger(__name__)

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._ \-()]")


def safe_filename(name: str) -> str:

    cleaned = _SAFE_NAME.sub("_", Path(name).name).strip(" .")

    return cleaned[:150] or "file"


def document_dir(user_id: int, document_id: str) -> Path:
    return config.UPLOAD_DIR / str(user_id) / document_id


def save_stream(upload, destination: Path, limit_bytes: int) -> int:
    """Copy an uploaded file to disk, enforcing the size limit."""

    size = 0

    with open(destination, "wb") as out:
        while chunk := upload.read(1024 * 1024):
            size += len(chunk)

            if size > limit_bytes:
                out.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "File exceeds the "
                        f"{config.MAX_FILE_SIZE_MB} MB limit."
                    ),
                )

            out.write(chunk)

    return size


def ingest_upload(user, upload) -> dict:
    """Store one uploaded file and index it. Returns a result dict;
    raises HTTPException for per-file problems."""

    filename = safe_filename(upload.filename or "")
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{extension}'. Supported: "
                + ", ".join(sorted(SUPPORTED_EXTENSIONS))
            ),
        )

    document_id = str(uuid4())
    directory = document_dir(user["id"], document_id)
    directory.mkdir(parents=True, exist_ok=True)

    file_path = directory / filename

    try:
        size = save_stream(
            upload.file,
            file_path,
            config.MAX_FILE_SIZE_MB * 1024 * 1024,
        )

        # ---- storage quota ------------------------------------
        quota = user["quota_mb"] * 1024 * 1024

        if storage_used_bytes(user["id"]) + size > quota:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Storage quota of {user['quota_mb']} MB "
                    "exceeded. Delete files or ask an admin."
                ),
            )

        # ---- read ---------------------------------------------
        try:
            extracted = extract_file_data(str(file_path))
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Could not read file: {exc}",
            )

        text = extracted["text"]

        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail="No readable text was found in the file.",
            )

        (directory / "text.txt").write_text(text, encoding="utf-8")

        # ---- vector index -------------------------------------
        chunks = split_text(text)

        from backend.ingestion.vector_store import (
            create_vector_store,
            save_vector_store,
        )

        try:
            store = create_vector_store(
                chunks,
                metadatas=[
                    {"filename": filename, "chunk": i}
                    for i in range(len(chunks))
                ],
            )
            save_vector_store(store, document_id)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Vector indexing failed: {exc}",
            )

        # ---- knowledge graph (best effort) --------------------
        entities = relationships = 0
        warning = None

        try:
            from backend.graph.service import ingest_document_graph

            graph = ingest_document_graph(
                document_id=document_id,
                filename=filename,
                text=text,
            )
            entities = graph["entities"]
            relationships = graph["relationships"]

        except Exception as exc:
            logger.warning("Graph ingestion failed: %s", exc)
            warning = f"Knowledge graph unavailable: {exc}"

        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO documents
                    (id, owner_id, filename, file_type, size_bytes,
                     pages, characters, chunks, entities,
                     relationships, status, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed',
                        ?, ?)
                """,
                (
                    document_id, user["id"], filename,
                    extracted["file_type"], size,
                    extracted.get("pages"), len(text), len(chunks),
                    entities, relationships, warning, now_iso(),
                ),
            )

        audit(user, "document.upload", f"{filename} ({document_id})")

        return {
            "document_id": document_id,
            "filename": filename,
            "file_type": extracted["file_type"],
            "size_bytes": size,
            "characters": len(text),
            "chunks": len(chunks),
            "entities": entities,
            "relationships": relationships,
            "warning": warning,
        }

    except BaseException:
        # Leave nothing behind on failure.
        shutil.rmtree(directory, ignore_errors=True)
        try:
            from backend.ingestion.vector_store import (
                delete_vector_store,
            )
            delete_vector_store(document_id)
        except Exception:
            pass
        raise


def delete_document(doc: dict) -> None:
    """Remove a document's files, indexes, graph and DB row."""

    shutil.rmtree(
        document_dir(doc["owner_id"], doc["id"]),
        ignore_errors=True,
    )

    try:
        from backend.ingestion.vector_store import delete_vector_store

        delete_vector_store(doc["id"])
    except Exception as exc:
        logger.warning("Vector delete failed: %s", exc)

    try:
        from backend.graph.neo4j_store import delete_document_graph

        delete_document_graph(doc["id"])
    except Exception as exc:
        logger.warning("Graph delete failed: %s", exc)

    with get_conn() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc["id"],))
