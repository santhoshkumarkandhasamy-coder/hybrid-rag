from fastapi import (
    APIRouter,
    HTTPException,
)

from backend.models.schemas import (
    SearchRequest,
)

from backend.retrieval.hybrid_search import (
    hybrid_search,
)


router = APIRouter(
    prefix="/hybrid",
    tags=["Hybrid Search"],
)


@router.post("/search")
async def hybrid_search_endpoint(
    request: SearchRequest,
):

    try:

        result = hybrid_search(
            document_id=request.document_id,
            query=request.query,
            vector_top_k=request.top_k,
            graph_top_k=request.top_k,
        )

        return result

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Hybrid search failed: {exc}",
        )