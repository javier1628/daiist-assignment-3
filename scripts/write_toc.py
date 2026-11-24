"""
Write TOC.md: the título / capítulo / sección tree of every indexed document,
with each article's number, title, start page and word count.
`uv run python scripts/write_toc.py`

It reads index/articles.jsonl, which `uv run python main.py index` writes, and
calls no API. The norma is left out because it is not in the index.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import index  # noqa: E402  (the index stage, for its documents and its article records)

OUTPUT = ROOT / "TOC.md"
TERM = re.compile(r"\d+\)\s*(.+?):")  # "3) Admisión temporal: La Admisión ..." -> the term before the first colon
PREVIEW_WORDS = 12  # of the start of an article that has no title


def defined_terms(article: index.Article) -> list[str]:
    """The terms an article of definitions defines, one per numbered item."""
    _, *items = index.split_pieces(article.text)
    terms = []
    for item in items:
        text = " ".join(item.split())
        match = TERM.match(text)
        if match is None:
            raise ValueError(
                f"{article.source}, article {article.number}: this item has no 'N) term:' at its start: {text[:60]!r}"
            )
        terms.append(match.group(1))
    return terms


def title_cell(article: index.Article, definitions: int) -> str:
    """What the Title column shows: the title, a count of definitions, or how an untitled article starts."""
    if definitions:
        return f"{article.title} — **{definitions} definitions**, listed below"
    if article.title:
        return article.title
    words = index.HEADING_MARKER.sub("", " ".join(article.text.split()), count=1).split()
    start = " ".join(words[:PREVIEW_WORDS]) + (" ..." if len(words) > PREVIEW_WORDS else "")
    return f'*(no title; starts: "{start}")*'


def render(articles: list[index.Article]) -> list[str]:
    out = [
        "# Table of contents of the indexed documents",
        "",
        "Written by `scripts/write_toc.py` from `index/articles.jsonl`. Each document is shown as its tree of "
        "títulos, capítulos and secciones, with one row per article.",
        "",
        "- **Page** is the page of the PDF the article starts on. **Words** counts the article after cleaning.",
        "- Titles and headings are as extracted from the scans, so some carry OCR errors. An article without a "
        "title shows how its text starts instead.",
        "- In `eval/questions.csv`, an article is written as its file name in `expected_source` "
        "(for example `ley-168-21.pdf`) and `Artículo N` in `expected_location`.",
        "",
    ]
    for document in index.DOCUMENTS.values():
        own = [article for article in articles if article.source == document.filename]
        if not own or not document.in_initial_index:
            continue
        out += [
            f"## {document.name} (`{document.filename}`)",
            "",
            f"{len(own):,} articles, {sum(article.words for article in own):,} words.",
            "",
        ]
        path = ("", "", "")  # the título, capítulo and sección the rows being collected sit under
        rows: list[str] = []
        lists: list[str] = []  # lists of defined terms, shown after the table they belong to

        def flush() -> None:
            nonlocal rows, lists
            if rows:
                out.extend(["| Art. | Title | Page | Words |", "| ---: | --- | ---: | ---: |", *rows, "", *lists])
            rows, lists = [], []

        for article in own:
            here = (article.titulo, article.capitulo, article.seccion)
            if here != path:
                flush()
                changed = next(level for level in range(3) if here[level] != path[level])
                for level in range(changed, 3):
                    if here[level]:
                        out += [f"{'#' * (3 + level)} {here[level]}", ""]
                path = here
            terms = defined_terms(article) if article.number in document.one_item_per_chunk else []
            cell = title_cell(article, len(terms)).replace("|", "\\|")
            rows.append(f"| {article.number} | {cell} | {article.page} | {article.words:,} |")
            if terms:
                lists += [
                    f"**Artículo {article.number}, the {len(terms)} defined terms.** Each is its own chunk in "
                    "the index.",
                    "",
                    *[f"{number}. {term}" for number, term in enumerate(terms, 1)],
                    "",
                ]
        flush()
    return out


def main() -> None:
    if not index.ARTICLES_FILE.is_file():
        raise FileNotFoundError(f"{index.ARTICLES_FILE} is missing. Run `uv run python main.py index` first.")
    with index.ARTICLES_FILE.open(encoding="utf-8") as file:
        articles = [index.Article(**json.loads(line)) for line in file]
    lines = render(articles)
    OUTPUT.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(lines):,} lines)")


if __name__ == "__main__":
    main()
