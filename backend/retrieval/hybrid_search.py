import logging

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

    from backend.ingestion.vector_store import search_documents

    vector_results = search_documents(
        document_ids=document_ids,
        query=query,
        top_k=vector_top_k,
    )

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
