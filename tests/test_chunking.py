from ingestion.chunking import chunk_text, split_by_article


def test_split_by_article_preserves_article_metadata() -> None:
    text = """Article 7 Conditions for consent
Consent must be demonstrable.

Article 15 Right of access
The data subject can access personal data."""

    blocks = split_by_article(text)

    assert [block["article"] for block in blocks] == ["Article 7", "Article 15"]
    assert blocks[0]["section"] == "Conditions for consent"


def test_chunk_text_uses_overlap_and_stable_ids() -> None:
    text = "Article 7 Conditions for consent\n" + " ".join(f"word{i}" for i in range(12))

    chunks = chunk_text(
        text,
        document="gdpr",
        source="data/raw/gdpr.md",
        chunk_size=8,
        overlap=2,
    )

    assert len(chunks) == 3
    assert chunks[0].article == "Article 7"
    assert chunks[0].chunk_id == "gdpr:article-7:001"
    assert chunks[1].text.split()[:2] == chunks[0].text.split()[-2:]
