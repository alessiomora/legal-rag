import argparse
import json
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from ingestion.chunking import chunk_text
from ingestion.loaders import load_text_documents


def build_chunks(raw_dir: Path, chunk_size: int, overlap: int) -> list[dict]:
    chunks: list[dict] = []
    for document in load_text_documents(raw_dir):
        document_chunks = chunk_text(
            document["text"],
            document=document["document"],
            source=document["source"],
            chunk_size=chunk_size,
            overlap=overlap,
        )
        chunks.extend(chunk.to_dict() for chunk in document_chunks)
    return chunks


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def ensure_collection(client, collection_name: str, vector_size: int) -> None:
    from qdrant_client.models import Distance, VectorParams

    existing = {collection.name for collection in client.get_collections().collections}
    if collection_name in existing:
        client.delete_collection(collection_name=collection_name)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def upsert_chunks(chunks: list[dict]) -> None:
    try:
        from app.config import get_settings
        from app.embedding_model import load_embedding_model
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required package"
        raise SystemExit(
            f"Missing Python dependency: {missing}\n\n"
            "The chunks were written successfully, but indexing into Qdrant "
            "requires the project dependencies.\n\n"
            "Run these commands from the repository root:\n"
            "  python3 -m venv .venv\n"
            "  source .venv/bin/activate\n"
            "  python -m pip install -r requirements.txt\n"
            "  docker compose up -d\n"
            "  ./scripts/ingest.sh"
        ) from exc

    settings = get_settings()
    model = load_embedding_model()
    vectors = model.encode(
        [chunk["text"] for chunk in chunks],
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, settings.qdrant_collection, len(vectors[0]))

    points = [
        PointStruct(
            id=str(uuid5(NAMESPACE_URL, chunk["chunk_id"])),
            vector=vector.tolist(),
            payload=chunk,
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    client.upsert(collection_name=settings.qdrant_collection, points=points)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest legal documents into Qdrant.")
    parser.add_argument("--raw-dir", default="data/raw", type=Path)
    parser.add_argument("--processed", default="data/processed/gdpr_chunks.jsonl", type=Path)
    parser.add_argument("--chunk-size", default=220, type=int)
    parser.add_argument("--overlap", default=40, type=int)
    parser.add_argument("--skip-qdrant", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chunks = build_chunks(args.raw_dir, args.chunk_size, args.overlap)
    if not chunks:
        raise SystemExit(f"No .txt or .md documents found in {args.raw_dir}")

    write_jsonl(args.processed, chunks)
    print(f"Wrote {len(chunks)} chunks to {args.processed}")

    if args.skip_qdrant:
        print("Skipped Qdrant upsert.")
        return

    upsert_chunks(chunks)
    print("Upserted chunks into Qdrant.")


if __name__ == "__main__":
    main()
