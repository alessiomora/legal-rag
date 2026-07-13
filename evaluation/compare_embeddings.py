import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd


DEFAULT_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "BAAI/bge-small-en-v1.5",
]


def slugify_model_name(model_name: str) -> str:
    slug = model_name.split("/")[-1].lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug or "embedding-model"


def run_command(command: list[str], env: dict[str, str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, env=env, check=True)


def summarize_results(model_name: str, csv_path: Path) -> dict:
    df = pd.read_csv(csv_path)
    found = df["found_rank"].dropna()
    return {
        "model": model_name,
        "questions": len(df),
        "recall@1": float(df["recall_at_1"].mean()),
        "recall@3": float(df["recall_at_3"].mean()),
        "recall@5": float(df["recall_at_5"].mean()),
        "mrr": float(df["mrr"].mean()),
        "average_rank_when_found": float(found.mean()) if not found.empty else None,
        "results_file": str(csv_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare retrieval metrics across embedding models."
    )
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Embedding model to evaluate. Can be passed multiple times.",
    )
    parser.add_argument("--top-k", default=5, type=int)
    parser.add_argument("--questions", default="evaluation/questions.jsonl", type=Path)
    parser.add_argument("--results-dir", default="evaluation/results", type=Path)
    parser.add_argument(
        "--qdrant-url",
        default=os.getenv("QDRANT_URL", "http://localhost:6333"),
        help="Qdrant URL used by ingestion and evaluation.",
    )
    parser.add_argument(
        "--embedding-device",
        default=os.getenv("EMBEDDING_DEVICE", "auto"),
        help="Embedding device used by sentence-transformers.",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Only re-run evaluation. Use when Qdrant already contains the matching model vectors.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    models = args.models or DEFAULT_MODELS
    args.results_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for model_name in models:
        slug = slugify_model_name(model_name)
        out_path = args.results_dir / f"{slug}.csv"

        env = os.environ.copy()
        env["EMBEDDING_MODEL"] = model_name
        env["EMBEDDING_DEVICE"] = args.embedding_device
        env["QDRANT_URL"] = args.qdrant_url

        print(f"\n=== Evaluating {model_name} ===", flush=True)
        if not args.skip_ingest:
            run_command([sys.executable, "-m", "ingestion.ingest_documents"], env)

        run_command(
            [
                sys.executable,
                "-m",
                "evaluation.evaluate_retrieval",
                "--questions",
                str(args.questions),
                "--out",
                str(out_path),
                "--top-k",
                str(args.top_k),
            ],
            env,
        )
        summaries.append(summarize_results(model_name, out_path))

    summary_df = pd.DataFrame(summaries)
    summary_path = args.results_dir / "embedding_comparison.csv"
    summary_df.to_csv(summary_path, index=False)

    print("\nEmbedding comparison")
    print(summary_df.to_string(index=False))
    print(f"\nWrote summary to {summary_path}")


if __name__ == "__main__":
    main()
