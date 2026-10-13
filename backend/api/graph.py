from fastapi import APIRouter, Depends, HTTPException

from backend.core.deps import get_current_user, get_owned_document

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@router.get("/{document_id}")
def get_graph(document_id: str, user=Depends(get_current_user)):

    get_owned_document(document_id, user)

    try:
        from backend.graph.store import get_document_graph

        return get_document_graph(document_id)

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Knowledge graph unavailable: {exc}",
        )
