from types import SimpleNamespace

from app.retrieval import qdrant_hit_to_chunk


def test_qdrant_hit_to_chunk_maps_payload() -> None:
    hit = SimpleNamespace(
        id="point-1",
        score=0.82,
        payload={
            "chunk_id": "gdpr:article-7:001",
            "text": "Consent must be demonstrable.",
            "document": "gdpr",
            "article": "Article 7",
            "section": "Conditions for consent",
            "source": "data/raw/gdpr.md",
        },
    )

    chunk = qdrant_hit_to_chunk(hit)

    assert chunk.chunk_id == "gdpr:article-7:001"
    assert chunk.score == 0.82
    assert chunk.article == "Article 7"
