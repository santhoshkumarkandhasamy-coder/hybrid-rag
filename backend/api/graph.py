from fastapi import APIRouter, HTTPException

from backend.graph.service import ingest_document_graph
from backend.graph.neo4j_store import get_document_graph

router = APIRouter(
    prefix="/graph",
    tags=["Knowledge Graph"],
)


# ============================================================
# GRAPH INGESTION
# ============================================================

@router.post("/ingest")
def ingest_graph(
    payload: dict,
):
    try:

        document_id = payload.get(
            "document_id"
        )

        filename = payload.get(
            "filename"
        )

        text = payload.get(
            "text"
        )

        # -----------------------------------------
        # Validation
        # -----------------------------------------

        if not document_id:
            raise HTTPException(
                status_code=400,
                detail="document_id is required.",
            )

        if not filename:
            raise HTTPException(
                status_code=400,
                detail="filename is required.",
            )

        if not text:
            raise HTTPException(
                status_code=400,
                detail="text is required.",
            )

        # -----------------------------------------
        # Send extracted text directly to KG
        # -----------------------------------------

        result = ingest_document_graph(
            document_id=document_id,
            filename=filename,
            text=text,
        )

        return {
            "document_id": document_id,
            "filename": filename,
            "status": "completed",
            **result,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Graph ingestion failed: {str(e)}",
        )


# ============================================================
# GET DOCUMENT KNOWLEDGE GRAPH
# ============================================================

@router.get("/{document_id}")
def get_graph(
    document_id: str,
):
    try:

        if not document_id:
            raise HTTPException(
                status_code=400,
                detail="document_id is required.",
            )

        graph = get_document_graph(
            document_id
        )

        return graph

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load document graph: {str(e)}",
        )