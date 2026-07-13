import argparse
import json
from pathlib import Path

import pandas as pd

from app.retrieval import search_chunks


def load_questions(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def article_labels(item: dict, field: str) -> list[str]:
    plural_value = item.get(field)
    if plural_value:
        return list(plural_value)

    singular_field = field.removesuffix("s")
    singular_value = item.get(singular_field)
    return [singular_value] if singular_value else []


def expected_rank(results, expected_articles: list[str]) -> int | None:
    expected = set(expected_articles)
    for rank, chunk in enumerate(results, start=1):
        if chunk.article in expected:
            return rank
    return None


def reciprocal_rank(rank: int | None) -> float:
    return 0.0 if rank is None else 1.0 / rank


def evaluate(questions: list[dict], top_k: int) -> pd.DataFrame:
    rows = []
    for item in questions:
        expected_articles = article_labels(item, "expected_articles")
        supporting_articles = article_labels(item, "supporting_articles")
        results = search_chunks(item["question"], top_k=top_k)
        rank = expected_rank(results, expected_articles)
        supporting_rank = expected_rank(results, supporting_articles)
        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "expected_articles": "; ".join(expected_articles),
                "supporting_articles": "; ".join(supporting_articles),
                "notes": item.get("notes", ""),
                "found_rank": rank,
                "supporting_found_rank": supporting_rank,
                "mrr": reciprocal_rank(rank),
                "recall_at_1": rank is not None and rank <= 1,
                "recall_at_3": rank is not None and rank <= 3,
                "recall_at_5": rank is not None and rank <= 5,
                "retrieved_articles": "; ".join(
                    chunk.article or "" for chunk in results
                ),
            }
        )
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> dict:
    found = df["found_rank"].dropna()
    return {
        "recall@1": float(df["recall_at_1"].mean()),
        "recall@3": float(df["recall_at_3"].mean()),
        "recall@5": float(df["recall_at_5"].mean()),
        "mrr": float(df["mrr"].mean()),
        "average_rank_when_found": float(found.mean()) if not found.empty else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate legal retriever recall@k.")
    parser.add_argument("--questions", default="evaluation/questions.jsonl", type=Path)
    parser.add_argument("--out", default="evaluation/results/retrieval_results.csv", type=Path)
    parser.add_argument("--top-k", default=5, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    questions = load_questions(args.questions)
    df = evaluate(questions, args.top_k)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    print("Retrieval evaluation")
    for metric, value in summarize(df).items():
        print(f"{metric}: {value}")
    print(f"Wrote detailed results to {args.out}")


if __name__ == "__main__":
    main()
