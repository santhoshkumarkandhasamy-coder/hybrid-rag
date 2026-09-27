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

from backend.llm.answer_generator import (
    generate_answer,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("")
async def chat(
    request: SearchRequest,
):

    try:

        # ==========================================
        # 1. Hybrid Retrieval
        # ==========================================

        hybrid_results = hybrid_search(
            document_id=request.document_id,
            query=request.query,
            vector_top_k=request.top_k,
            graph_top_k=request.top_k,
        )

        # ==========================================
        # 2. Extract Results
        # ==========================================

        vector_results = hybrid_results.get(
            "vector_results",
            [],
        )

        graph_results = hybrid_results.get(
            "graph_results",
            [],
        )

        # ==========================================
        # 3. Generate Final Answer
        # ==========================================

        answer = generate_answer(
            question=request.query,
            vector_results=vector_results,
            graph_results=graph_results,
        )

        # ==========================================
        # 4. Return Final Response
        # ==========================================

        return {
            "document_id": request.document_id,
            "query": request.query,
            "answer": answer,
            "vector_result_count": len(
                vector_results
            ),
            "graph_result_count": len(
                graph_results
            ),
        }

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
            detail=f"Chat failed: {exc}",
        )