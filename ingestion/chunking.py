import re
from dataclasses import dataclass, asdict


ARTICLE_RE = re.compile(r"^(?:#+\s*)?(Article\s+\d+[A-Z]?)\b[:.\-\s]*(.*)$", re.IGNORECASE)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document: str
    article: str | None
    section: str | None
    source: str | None
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def split_by_article(text: str) -> list[dict]:
    """Split a legal text into article blocks when headings like 'Article 7' exist."""
    blocks: list[dict] = []
    current_article: str | None = None
    current_section: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            blocks.append(
                {
                    "article": current_article,
                    "section": current_section,
                    "text": "\n".join(current_lines).strip(),
                }
            )

    for line in text.splitlines():
        match = ARTICLE_RE.match(line.strip())
        if match:
            flush()
            current_article = match.group(1).title()
            current_section = match.group(2).strip() or None
            current_lines = [line.strip()]
        else:
            current_lines.append(line)
    flush()
    return [block for block in blocks if block["text"]]


def _window_words(words: list[str], chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        # Overlap keeps cross-boundary legal clauses visible to nearby chunks.
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks


def chunk_text(
    text: str,
    *,
    document: str,
    source: str | None = None,
    chunk_size: int = 220,
    overlap: int = 40,
) -> list[Chunk]:
    """Create word-window chunks while preserving article metadata when available."""
    article_blocks = split_by_article(text)
    if not article_blocks:
        article_blocks = [{"article": None, "section": None, "text": text.strip()}]

    chunks: list[Chunk] = []
    for block_index, block in enumerate(article_blocks, start=1):
        words = block["text"].split()
        for window_index, window_text in enumerate(
            _window_words(words, chunk_size, overlap),
            start=1,
        ):
            article = block["article"]
            article_key = (article or f"block-{block_index}").lower().replace(" ", "-")
            chunk_id = f"{document}:{article_key}:{window_index:03d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document=document,
                    article=article,
                    section=block["section"],
                    source=source,
                    text=window_text,
                )
            )
    return chunks
