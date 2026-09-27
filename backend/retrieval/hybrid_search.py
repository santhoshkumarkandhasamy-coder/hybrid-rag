from backend.retrieval.vector_search import (
    search_vector_store,
)

from backend.graph.neo4j_store import (
    search_graph,
)


def hybrid_search(
    document_id: str,
    query: str,
    vector_top_k: int = 5,
    graph_top_k: int = 10,
) -> dict:

    if not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    # ==========================================
    # 1. Vector Search
    # ==========================================

    vector_results = search_vector_store(
        document_id=document_id,
        query=query,
        top_k=vector_top_k,
    )

    # ==========================================
    # 2. Knowledge Graph Search
    # ==========================================

    graph_results = search_graph(
        document_id=document_id,
        query=query,
        limit=graph_top_k,
    )

    # ==========================================
    # 3. Return Combined Results
    # ==========================================

    return {
        "document_id": document_id,
        "query": query,
        "vector_results": vector_results,
        "graph_results": graph_results,
    }