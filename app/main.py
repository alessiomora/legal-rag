from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.generation import answer_question, citations_from_chunks
from app.retrieval import search_chunks
from app.schemas import AskRequest, AskResponse, RetrieveRequest, RetrieveResponse


app = FastAPI(title="Legal RAG Evaluation Mini-System")
WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    results = search_chunks(request.query, request.top_k)
    return RetrieveResponse(query=request.query, results=results)


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    chunks = search_chunks(request.question, request.top_k)
    answer = answer_question(request.question, chunks)
    return AskResponse(
        question=request.question,
        answer=answer,
        citations=citations_from_chunks(chunks),
    )
