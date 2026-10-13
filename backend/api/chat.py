import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.core import config
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

        if config.USE_OPENAI:
            from backend.llm.answer_generator import generate_answer
        elif config.USE_OLLAMA:
            try:
                return _ollama_reply(
                    request, user, document_ids, results
                )
            except Exception as exc:  # fall back to offline mode
                logging.getLogger(__name__).warning(
                    "Ollama unavailable: %s", exc
                )
            from backend.llm.local_answer import generate_answer
        else:
            from backend.llm import local_answer
            from backend.llm.local_answer import generate_answer

            if local_answer.wants_overview(request.query):
                overview = _offline_overview(
                    user, document_ids, results["vector_results"]
                )
                if overview:
                    return {
                        "document_ids": document_ids,
                        "query": request.query,
                        "answer": overview["answer"],
                        "sources": overview["sources"],
                        "vector_result_count": len(
                            results["vector_results"]
                        ),
                        "graph_result_count": len(
                            results["graph_results"]
                        ),
                    }

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

    # Only list files whose name the answer actually cites / quotes
    # (offline mode); LLM mode may cite any retrieved file.
    retrieved = {
        r["filename"] for r in results["vector_results"]
        if r.get("filename")
    }
    sources = sorted(
        name for name in retrieved
        if config.USE_OPENAI or f"({name})" in answer
    )

    return {
        "document_ids": document_ids,
        "query": request.query,
        "answer": answer,
        "sources": sources,
        "vector_result_count": len(results["vector_results"]),
        "graph_result_count": len(results["graph_results"]),
    }


def _offline_overview(user, document_ids, vector_results, raw=False):
    """Overview of the best-matching documents (or the only one)."""

    from backend.llm.local_answer import build_overview
    from backend.services.documents import document_dir

    ordered = []
    for r in vector_results:
        if r["document_id"] not in ordered:
            ordered.append(r["document_id"])
    for doc_id in document_ids:
        if doc_id not in ordered:
            ordered.append(doc_id)

    docs, names = [], []

    for doc_id in ordered[:3]:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT filename FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
        path = document_dir(user["id"], doc_id) / "text.txt"
        if row and path.exists():
            docs.append((row["filename"], path.read_text("utf-8")))
            names.append(row["filename"])

    if not docs:
        return None

    if raw:  # plain text for an LLM prompt
        return {
            "answer": "\n\n".join(f"[{n}]\n{t}" for n, t in docs),
            "sources": names,
        }

    return {"answer": build_overview(docs), "sources": names}


def _ollama_reply(request, user, document_ids, results):

    from backend.llm.local_answer import wants_overview
    from backend.llm.ollama_answer import generate_answer

    overview_text = None

    if wants_overview(request.query):
        found = _offline_overview(
            user, document_ids, results["vector_results"],
            raw=True,
        )
        overview_text = found["answer"] if found else None

    answer = generate_answer(
        question=request.query,
        vector_results=results["vector_results"],
        graph_results=results["graph_results"],
        overview_text=overview_text,
    )

    sources = sorted(
        {r["filename"] for r in results["vector_results"]
         if r.get("filename")}
    )

    audit(user, "chat.query", f"{len(document_ids)} document(s)")

    return {
        "document_ids": document_ids,
        "query": request.query,
        "answer": answer,
        "sources": sources,
        "vector_result_count": len(results["vector_results"]),
        "graph_result_count": len(results["graph_results"]),
    }
