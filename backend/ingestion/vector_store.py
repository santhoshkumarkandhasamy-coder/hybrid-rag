from pathlib import Path

from langchain_community.vectorstores import FAISS

from backend.ingestion.embeddings import (
    get_embedding_model,
)


# ==========================================
# FAISS Storage Directory
# ==========================================

FAISS_BASE_DIR = Path("data/faiss")


# ==========================================
# Create Vector Store
# ==========================================

def create_vector_store(
    chunks: list[str],
) -> FAISS:

    if not chunks:
        raise ValueError(
            "No text chunks were provided."
        )

    embedding_model = get_embedding_model()

    vector_store = FAISS.from_texts(
        texts=chunks,
        embedding=embedding_model,
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

    embedding_model = get_embedding_model()

    vector_store = FAISS.load_local(
        str(document_faiss_dir),
        embedding_model,
        allow_dangerous_deserialization=True,
    )

    return vector_store