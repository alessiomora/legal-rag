# Legal RAG Evaluation

Minimal retrieval-augmented generation system for public legal text, built around the GDPR. The project demonstrates document ingestion, article-aware chunking, vector search, grounded answer generation with citations, and retrieval evaluation.

It is a prototype, not a legal assistant and not legal advice.

## Demo

![Legal RAG demo](docs/assets/demo.gif)

## What It Demonstrates

- Ingestion of official GDPR text from EUR-Lex.
- Chunking with metadata such as document, article, section, source, and chunk id.
- Local embeddings with `sentence-transformers`.
- Vector storage and search with Qdrant.
- FastAPI endpoints for retrieval and grounded Q&A.
- A small browser UI for trying `/retrieve` and `/ask`.
- A retrieval benchmark over GDPR questions mapped to expected articles.
- Embedding-model comparison using Recall@K and MRR.

## Architecture

```text
EUR-Lex GDPR text
  -> ingestion loader
  -> article-aware chunks
  -> sentence-transformers embeddings
  -> Qdrant vector collection
  -> FastAPI /retrieve
  -> FastAPI /ask
  -> OpenAI answer generation with citations
```

## Services

The Docker Compose setup runs three services:

| Service | Role |
| --- | --- |
| `qdrant` | Vector database storing chunk embeddings and metadata. |
| `ingest` | One-shot job that waits for Qdrant, chunks documents, embeds chunks, and writes them to Qdrant. |
| `api` | FastAPI app serving the web UI, `/retrieve`, `/ask`, `/health`, and Swagger docs. |

`api` and `ingest` talk to Qdrant through Docker networking:

```text
http://qdrant:6333
```

Your browser reaches the API at:

```text
http://localhost:8000
```

## Quickstart

Requirements:

- Docker / Docker Compose
- Optional: OpenAI API key for generated answers

Create a local environment file:

```bash
cp .env.example .env
```

Add `OPENAI_API_KEY` in `.env` if you want `/ask` to call OpenAI. Retrieval works without an OpenAI key.

Download and prepare the official GDPR text:

```bash
./scripts/prepare_gdpr.sh
```

Start the system:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

Qdrant dashboard:

```text
http://localhost:6333/dashboard
```

## API Examples

Retrieve relevant source chunks:

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the conditions for valid consent under GDPR?","top_k":5}'
```

Ask a grounded question:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"When must a personal data breach be notified?","top_k":5}'
```

## Evaluation

The retrieval benchmark is in:

```text
evaluation/questions.jsonl
```

Each row maps a GDPR question to one or more expected source articles:

```json
{
  "id": "q024",
  "question": "When must a personal data breach be notified to the supervisory authority?",
  "expected_articles": ["Article 33"],
  "supporting_articles": ["Article 32", "Article 34"],
  "notes": "Article 33 directly governs supervisory authority notification."
}
```

Run a single retrieval evaluation:

```bash
python -m evaluation.evaluate_retrieval
```

Compare embedding models:

```bash
docker compose up -d qdrant
./scripts/compare_embeddings.sh
```

Current comparison on 50 GDPR questions:

| Model | Recall@1 | Recall@3 | Recall@5 | MRR |
| --- | ---: | ---: | ---: | ---: |
| `sentence-transformers/all-MiniLM-L6-v2` | 0.52 | 0.68 | 0.74 | 0.611 |
| `BAAI/bge-small-en-v1.5` | 0.56 | 0.86 | 0.92 | 0.717 |

The benchmark is project-specific and should be treated as a curated evaluation set, not an external gold standard.

## Embedding Models

The default model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Switch models with:

```bash
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5 ./scripts/ingest.sh
```

After changing the embedding model, re-run ingestion. Vectors produced by different embedding models are not comparable.

## Local Development

Use Python 3.11:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run Qdrant only:

```bash
docker compose up -d qdrant
```

Run ingestion and API locally:

```bash
./scripts/ingest.sh
./scripts/run_api.sh
```

## Limitations

- Vector-only retrieval; no BM25 or hybrid search yet.
- The benchmark labels are project-specific and should be manually audited before strong claims.
- Answer faithfulness is not yet evaluated.
- `/ask` depends on OpenAI API availability.
- No authentication or production hardening.

## Future Work

- Hybrid BM25 + vector retrieval.
- Reranking.
- Answer faithfulness and citation-quality evaluation.
- Additional public legal corpora such as the EU AI Act.
- Local LLM backend.
