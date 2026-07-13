import argparse
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_SOURCE_URL = "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
ARTICLE_RE = re.compile(r"^Article\s+(\d+[A-Z]?)$")
RECITAL_RE = re.compile(r"^\((\d+)\)$")
NOISE_PREFIXES = (
    "ELI:",
    "Languages, formats",
    "Multilingual display",
    "All consolidated versions",
    "Access current version",
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            cleaned = " ".join(data.split())
            if cleaned:
                self.parts.append(cleaned)

    def text(self) -> str:
        return "\n".join(self.parts)


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "legal-rag-eval/0.1"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def html_to_lines(html: str) -> list[str]:
    parser = TextExtractor()
    parser.feed(html)
    lines = []
    previous = ""
    for raw_line in parser.text().splitlines():
        line = " ".join(raw_line.split())
        if not line or line == previous:
            continue
        if any(line.startswith(prefix) for prefix in NOISE_PREFIXES):
            continue
        lines.append(line)
        previous = line
    return lines


def slice_regulation_text(lines: list[str]) -> list[str]:
    start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("REGULATION (EU) 2016/679")
    )
    end = next(
        index
        for index, line in enumerate(lines[start:], start=start)
        if line.startswith("This Regulation shall be binding in its entirety")
    )
    return lines[start : end + 1]


def format_markdown(lines: list[str], source_url: str) -> str:
    output = [
        "# Regulation (EU) 2016/679 (General Data Protection Regulation)",
        "",
        f"Source: {source_url}",
        "Official source: EUR-Lex, Official Journal version.",
        "",
    ]

    skip_next_as_article_title = False
    in_recitals = False
    for index, line in enumerate(lines):
        if line.startswith("REGULATION (EU) 2016/679"):
            output.append("## Regulation Title")
            output.append(line)
            output.append("")
            continue

        if line == "Whereas:":
            in_recitals = True
            output.append("## Recitals")
            continue

        recital_match = RECITAL_RE.match(line)
        if in_recitals and recital_match:
            output.append("")
            output.append(f"### Recital {recital_match.group(1)}")
            continue

        if line.startswith("CHAPTER "):
            in_recitals = False
            output.append("")
            output.append(f"## {line}")
            continue

        article_match = ARTICLE_RE.match(line)
        if article_match:
            title = ""
            if index + 1 < len(lines):
                next_line = lines[index + 1]
                if not ARTICLE_RE.match(next_line) and not next_line.startswith("CHAPTER "):
                    title = next_line
                    skip_next_as_article_title = True
            heading = f"Article {article_match.group(1)}"
            if title:
                heading = f"{heading} {title}"
            output.append("")
            output.append(f"## {heading}")
            continue

        if skip_next_as_article_title:
            skip_next_as_article_title = False
            continue

        output.append(line)

    return "\n".join(output).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download official GDPR text from EUR-Lex.")
    parser.add_argument("--url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--out", default="data/raw/gdpr.md", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    html = fetch_html(args.url)
    lines = slice_regulation_text(html_to_lines(html))
    markdown = format_markdown(lines, args.url)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown, encoding="utf-8")
    article_count = len(re.findall(r"^## Article\s+\d+", markdown, flags=re.MULTILINE))
    recital_count = len(re.findall(r"^### Recital\s+\d+", markdown, flags=re.MULTILINE))
    print(f"Wrote {args.out}")
    print(f"Detected {article_count} articles and {recital_count} recitals")


if __name__ == "__main__":
    main()
