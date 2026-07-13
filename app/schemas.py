from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    score: float
    document: str
    article: str | None = None
    section: str | None = None
    source: str | None = None


class RetrieveResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceCitation(BaseModel):
    chunk_id: str
    document: str
    article: str | None = None
    section: str | None = None
    source: str | None = None
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[SourceCitation]
