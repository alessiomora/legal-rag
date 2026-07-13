from types import SimpleNamespace

from evaluation.evaluate_retrieval import article_labels, expected_rank, reciprocal_rank


def test_article_labels_supports_plural_and_legacy_singular() -> None:
    assert article_labels({"expected_articles": ["Article 7"]}, "expected_articles") == [
        "Article 7"
    ]
    assert article_labels({"expected_article": "Article 7"}, "expected_articles") == [
        "Article 7"
    ]


def test_expected_rank_accepts_any_expected_article() -> None:
    results = [
        SimpleNamespace(article="Article 5"),
        SimpleNamespace(article="Article 34"),
        SimpleNamespace(article="Article 33"),
    ]

    assert expected_rank(results, ["Article 33", "Article 34"]) == 2
    assert expected_rank(results, ["Article 99"]) is None


def test_reciprocal_rank() -> None:
    assert reciprocal_rank(1) == 1.0
    assert reciprocal_rank(4) == 0.25
    assert reciprocal_rank(None) == 0.0
