from backend.ingestion.vector_store import (
    load_vector_store,
)


def search_vector_store(
    document_id: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:

    # ==========================================
    # Validate Query
    # ==========================================

    if not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )


    # ==========================================
    # Load Document-Specific FAISS Index
    # ==========================================

    vector_store = load_vector_store(
        document_id
    )


    # ==========================================
    # Perform Similarity Search
    # ==========================================

    results = (
        vector_store.similarity_search_with_score(
            query,
            k=top_k,
        )
    )


    # ==========================================
    # Format Results
    # ==========================================

    formatted_results = []

    for document, score in results:

        formatted_results.append(
            {
                "content": document.page_content,
                "score": float(score),
            }
        )


    return formatted_results