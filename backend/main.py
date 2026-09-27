from fastapi import FastAPI
from dotenv import load_dotenv

from backend.api.chat import (
    router as chat_router,
)

load_dotenv()

from backend.api.upload import (
    router as upload_router,
)

from backend.api.graph import (
    router as graph_router,
)

from backend.api.hybrid import (
    router as hybrid_router,
)

app = FastAPI(
    title="Hybrid RAG API",
    description=(
        "Hybrid RAG using FAISS, Neo4j and OpenAI"
    ),
    version="1.0.0",
)


# ============================================================
# Register Routers
# ============================================================

app.include_router(
    upload_router
)

app.include_router(
    graph_router
)

app.include_router(hybrid_router)

app.include_router(chat_router)

# ============================================================
# Root
# ============================================================

@app.get("/")
async def root():

    return {
        "message": "Hybrid RAG API is running"
    }


# ============================================================
# Health
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy"
    }