from fastapi import APIRouter, Depends, HTTPException

from backend.core.db import audit, get_conn
from backend.core.deps import get_current_user, get_owned_document
from backend.models.schemas import SearchRequest
from backend.retrieval.hybrid_search import hybrid_search

router = APIRouter(prefix="/chat", tags=["Chat"])


def resolve_document_ids(request: SearchRequest, user) -> list[str]:
    """Only ever return documents the user owns."""

    if request.document_ids:
        return [
            get_owned_document(doc_id, user)["id"]
            for doc_id in request.document_ids
        ]

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id FROM documents WHERE owner_id = ? "
            "AND status = 'completed'",
            (user["id"],),
        ).fetchall()

    ids = [r["id"] for r in rows]

    if not ids:
        raise HTTPException(
            status_code=400,
            detail="Upload at least one document first.",
        )

    return ids


@router.post("/search")
def hybrid_search_endpoint(
    request: SearchRequest, user=Depends(get_current_user)
):

    document_ids = resolve_document_ids(request, user)

    try:
        return hybrid_search(
            document_ids=document_ids,
            query=request.query,
            vector_top_k=request.top_k,
            graph_top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Hybrid search failed: {exc}"
        )


@router.post("")
def chat(request: SearchRequest, user=Depends(get_current_user)):

    document_ids = resolve_document_ids(request, user)

    try:
        results = hybrid_search(
            document_ids=document_ids,
            query=request.query,
            vector_top_k=request.top_k,
            graph_top_k=request.top_k,
        )

        from backend.llm.answer_generator import generate_answer

        answer = generate_answer(
            question=request.query,
            vector_results=results["vector_results"],
            graph_results=results["graph_results"],
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Chat failed: {exc}"
        )

    audit(user, "chat.query", f"{len(document_ids)} document(s)")

    sources = sorted(
        {r["filename"] for r in results["vector_results"]
         if r.get("filename")}
    )

    return {
        "document_ids": document_ids,
        "query": request.query,
        "answer": answer,
        "sources": sources,
        "vector_result_count": len(results["vector_results"]),
        "graph_result_count": len(results["graph_results"]),
    }
