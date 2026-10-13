import shutil
import threading
from collections import OrderedDict
from pathlib import Path

from langchain_community.vectorstores import FAISS

from backend.core import config
from backend.ingestion.embeddings import (
    get_embedding_model,
)


# ==========================================
# FAISS Storage Directory
# ==========================================

FAISS_BASE_DIR = config.FAISS_DIR

_CACHE_SIZE = 64
_store_cache: OrderedDict = OrderedDict()
_cache_lock = threading.Lock()


# ==========================================
# Create Vector Store
# ==========================================

def create_vector_store(
    chunks: list[str],
    metadatas: list[dict] | None = None,
) -> FAISS:

    if not chunks:
        raise ValueError(
            "No text chunks were provided."
        )

    embedding_model = get_embedding_model()

    vector_store = FAISS.from_texts(
        texts=chunks,
        embedding=embedding_model,
        metadatas=metadatas,
    )

    return vector_store


# ==========================================
# Save Vector Store
# ==========================================

def save_vector_store(
    vector_store: FAISS,
    document_id: str,
) -> Path:

    document_faiss_dir = (
        FAISS_BASE_DIR / document_id
    )

    document_faiss_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store.save_local(
        str(document_faiss_dir)
    )

    return document_faiss_dir


# ==========================================
# Load Vector Store
# ==========================================

def load_vector_store(
    document_id: str,
) -> FAISS:

    document_faiss_dir = (
        FAISS_BASE_DIR / document_id
    )

    index_file = (
        document_faiss_dir / "index.faiss"
    )

    if not index_file.exists():
        raise FileNotFoundError(
            f"FAISS index not found for document: "
            f"{document_id}"
        )

    # Indexes are cached in memory (invalidated if the file changes).
    stamp = index_file.stat().st_mtime

    with _cache_lock:
        cached = _store_cache.get(document_id)

        if cached and cached[0] == stamp:
            _store_cache.move_to_end(document_id)
            return cached[1]

    vector_store = FAISS.load_local(
        str(document_faiss_dir),
        get_embedding_model(),
        allow_dangerous_deserialization=True,
    )

    with _cache_lock:
        _store_cache[document_id] = (stamp, vector_store)

        while len(_store_cache) > _CACHE_SIZE:
            _store_cache.popitem(last=False)

    return vector_store


# ==========================================
# Search several documents (query embedded once)
# ==========================================

def search_documents(
    document_ids: list[str],
    query: str,
    top_k: int = 5,
) -> list[dict]:

    query_vector = get_embedding_model().embed_query(query)

    results = []

    for document_id in document_ids:

        try:
            store = load_vector_store(document_id)
        except FileNotFoundError:
            continue

        for doc, score in store.similarity_search_with_score_by_vector(
            query_vector, k=top_k
        ):
            results.append(
                {
                    "content": doc.page_content,
                    "score": float(score),
                    "document_id": document_id,
                    "filename": doc.metadata.get("filename"),
                }
            )

    # FAISS scores are distances: lower is better.
    results.sort(key=lambda r: r["score"])

    return results[:top_k]


def warm_up() -> None:
    """Load the embedding model so the first request isn't slow."""
    get_embedding_model().embed_query("warm up")


# ==========================================
# Delete Vector Store
# ==========================================

def delete_vector_store(document_id: str) -> None:

    with _cache_lock:
        _store_cache.pop(document_id, None)

    shutil.rmtree(
        FAISS_BASE_DIR / document_id,
        ignore_errors=True,
    )
