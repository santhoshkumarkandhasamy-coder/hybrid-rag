import logging

from backend.retrieval.vector_search import (
    search_vector_store,
)

logger = logging.getLogger(__name__)


def hybrid_search(
    document_ids: list[str],
    query: str,
    vector_top_k: int = 5,
    graph_top_k: int = 10,
) -> dict:
    """Search the vector indexes and knowledge graphs of
    one or more documents and merge the results."""

    if not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    if not document_ids:
        raise ValueError(
            "No documents to search."
        )

    # ==========================================
    # 1. Vector Search (all documents)
    # ==========================================

    vector_results = []

    for document_id in document_ids:

        try:
            vector_results.extend(
                search_vector_store(
                    document_id=document_id,
                    query=query,
                    top_k=vector_top_k,
                )
            )
        except FileNotFoundError:
            logger.warning(
                "No vector index for %s", document_id
            )

    # FAISS scores are distances: lower is better.
    vector_results.sort(key=lambda r: r["score"])
    vector_results = vector_results[:vector_top_k]

    # ==========================================
    # 2. Knowledge Graph Search (best effort)
    # ==========================================

    graph_results = []

    try:
        from backend.graph.store import search_graph

        for document_id in document_ids:
            graph_results.extend(
                search_graph(
                    document_id=document_id,
                    query=query,
                    limit=graph_top_k,
                )
            )

        graph_results = graph_results[:graph_top_k]

    except Exception as exc:
        logger.warning("Graph search unavailable: %s", exc)

    return {
        "document_ids": document_ids,
        "query": query,
        "vector_results": vector_results,
        "graph_results": graph_results,
    }
