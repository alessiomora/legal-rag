from openai import OpenAI

from app.config import get_settings
from app.schemas import RetrievedChunk, SourceCitation


SYSTEM_PROMPT = """You are a careful legal-document RAG assistant.
Answer only from the provided context.
If the context is insufficient, say that the provided context is insufficient.
Do not provide legal advice.
Use citations in square brackets, e.g. [Article 7]."""


def build_context(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        label = chunk.article or chunk.chunk_id
        parts.append(
            f"Source {index}: {label}\n"
            f"Document: {chunk.document}\n"
            f"Chunk ID: {chunk.chunk_id}\n"
            f"Text:\n{chunk.text}"
        )
    return "\n\n---\n\n".join(parts)


def citations_from_chunks(chunks: list[RetrievedChunk]) -> list[SourceCitation]:
    return [
        SourceCitation(
            chunk_id=chunk.chunk_id,
            document=chunk.document,
            article=chunk.article,
            section=chunk.section,
            source=chunk.source,
            score=chunk.score,
        )
        for chunk in chunks
    ]


def answer_question(question: str, chunks: list[RetrievedChunk]) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        return (
            "OPENAI_API_KEY is not configured. Retrieval succeeded, but answer "
            "generation requires an OpenAI API key."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    # /ask sends only retrieved chunks, so generation stays tied to visible evidence.
    user_prompt = (
        f"Question: {question}\n\n"
        f"Retrieved context:\n{build_context(chunks)}\n\n"
        "Write a concise answer grounded only in the retrieved context."
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message.content or ""
