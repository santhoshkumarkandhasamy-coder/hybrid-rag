from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    document_id: str
    query: str
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class IngestionResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    characters: int
    chunks: int
    status: str


class GraphIngestionRequest(BaseModel):
    document_id: str
    filename: str


class GraphSearchRequest(BaseModel):
    document_id: str
    query: str
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
    )