from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.admin import router as admin_router
from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.graph import router as graph_router
from backend.api.upload import router as upload_router
from backend.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Hybrid RAG API",
    description=(
        "Secure multi-user Hybrid RAG using FAISS, Neo4j and OpenAI"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(graph_router)
app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"message": "Hybrid RAG API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
