from app.config import get_settings
from app.embedding_model import load_embedding_model
from app.qdrant_client import get_qdrant_client
from app.schemas import RetrievedChunk


_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = load_embedding_model()
    return _embedding_model


def embed_query(query: str) -> list[float]:
    return get_embedding_model().encode(query, normalize_embeddings=True).tolist()


def search_chunks(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    settings = get_settings()
    client = get_qdrant_client()
    query_vector = embed_query(query)
    hits = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )
    return [qdrant_hit_to_chunk(hit) for hit in hits]


def qdrant_hit_to_chunk(hit) -> RetrievedChunk:
    payload = hit.payload or {}
    return RetrievedChunk(
        chunk_id=payload.get("chunk_id", str(hit.id)),
        text=payload.get("text", ""),
        score=float(hit.score),
        document=payload.get("document", ""),
        article=payload.get("article"),
        section=payload.get("section"),
        source=payload.get("source"),
    )
