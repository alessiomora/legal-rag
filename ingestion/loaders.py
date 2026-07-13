from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_text_documents(raw_dir: str | Path) -> list[dict]:
    """Load plain-text or Markdown legal documents from a directory."""
    base = Path(raw_dir)
    paths = sorted(base.iterdir())
    official_gdpr = base / "gdpr.md"
    if official_gdpr.exists():
        paths = [path for path in paths if path.name != "gdpr_starter.md"]

    documents: list[dict] = []
    for path in paths:
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        documents.append(
            {
                "document": path.stem,
                "source": str(path),
                "text": path.read_text(encoding="utf-8"),
            }
        )
    return documents
