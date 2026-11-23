"""
Describe the corpus before and after cleaning. `uv run python scripts/describe_corpus.py`

Run `uv run python main.py index` first. This script then writes CORPUS.md in two parts.

Before cleaning, for every PDF in corpus/: page count and file size, whether the
pages carry a real text layer or are scanned images, the word count of the
extracted text, the "Artículo N" headings and whether their numbers run
consecutively, the most repeated lines, random samples of the raw text, and
chunk-count estimates.

After cleaning, from the files the index stage saves in index/: words and
articles per document, what each removal rule took out, the spread of article
lengths, the longest and shortest articles, and a few random articles in full.

Last, a dry run of the chunking rule (`index.chunk_article`) at several chunk
sizes: how many chunks it would give and which pieces it cannot cut.

Diagnosis only. It saves no chunk, embeds and OCRs nothing and calls no API.
"""

import bisect
import json
import math
import random
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import pypdf
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import index  # noqa: E402  (the index stage, for its paths and rule settings)

RAW_DIR = index.CORPUS_DIR
OUTPUT = ROOT / "CORPUS.md"

MIN_TEXT_CHARS = 20  # a page with fewer non-space characters counts as having no text
WORDS_PER_CHUNK = 150
TOP_LINES = 10
SAMPLES = 3
SAMPLE_CHARS = 300
SEED = 0  # fixed, so reruns pick the same samples
CONTEXT_LIMIT = 10  # out-of-order headings shown with the heading before them
EXTREMES = 10  # longest and shortest articles listed
RANDOM_ARTICLES = 5
SHORT_LINE_CHARS = 6  # lines this short that survive cleaning are listed as possible debris
SHORT_LINES_SHOWN = 12
EXTRACTION_LABELS = {"pdfplumber_pages": "pdfplumber", "pypdf_page_layer": "pypdf, page layer only"}
CHUNK_LIMITS = (200, 300, 400, 500)  # chunk sizes, in words, tried by the dry run
ADDED_LATER = tuple(d.filename for d in index.DOCUMENTS.values() if not d.in_initial_index)  # left for the add-document tool
LETTERED_ITEM = re.compile(r"[a-zñ]\)\s*\S")  # "a) ...", which the chunking rule does not cut at
PREVIEW_CHARS = 60  # of the start of a piece, to identify it

# A heading starts a line with a capitalised "Artículo" and a number. The accent
# and the space are optional because OCR drops them. Lower-case line starts
# ("artículo 50 de esta ley") are cross-references wrapped onto a new line.
ARTICLE_HEADING = re.compile(r"^[ \t]*(?:Art[íi]culo|ART[ÍI]CULO)[ \t]*(\d+)", re.MULTILINE)


def image_sizes(resources, seen: set[int]) -> list[tuple[int, int]]:
    """Pixel sizes of the images under a /Resources dictionary, form XObjects included."""
    if resources is None:
        return []
    xobjects = resources.get_object().get("/XObject")
    if xobjects is None:
        return []
    sizes = []
    for ref in xobjects.get_object().values():
        idnum = getattr(ref, "idnum", None)
        if idnum is not None:
            if idnum in seen:
                continue
            seen.add(idnum)
        xobject = ref.get_object()
        if xobject.get("/Subtype") == "/Image":
            sizes.append((int(xobject["/Width"]), int(xobject["/Height"])))
        elif xobject.get("/Subtype") == "/Form":
            sizes.extend(image_sizes(xobject.get("/Resources"), seen))
    return sizes


def has_page_image(page) -> bool:
    """True when the page holds an image big enough to be a scan of the whole page (72 dpi or more)."""
    short, long = sorted((float(page.mediabox.width), float(page.mediabox.height)))
    return any(
        min(size) >= short and max(size) >= long
        for size in image_sizes(page.get("/Resources"), set())
    )


def has_invisible_text(page) -> bool:
    """True when the page stream sets text render mode 3 (invisible), which is how OCR layers are stored."""
    contents = page.get_contents()
    if contents is None:
        return False
    return any(operator == b"Tr" and int(operands[0]) == 3 for operands, operator in contents.operations)


def text_layer_verdict(pages: int, with_text: int, with_page_image: int) -> str:
    if with_page_image == 0:
        return "Real text layer (born-digital)" if with_text else "No text and no page images"
    if with_text == 0:
        return "SCANNED IMAGES, NO TEXT LAYER (needs OCR)"
    if with_page_image == pages:
        return "Scanned page images with an OCR text layer"
    return "Mixed: some pages are scans, some are not"


def check_numbering(headings: list[tuple[int, int]]) -> dict:
    """Gaps, repeats and backward steps in (article number, page) pairs given in reading order."""
    numbers = [number for number, _ in headings]
    counts = Counter(numbers)
    return {
        "distinct": len(counts),
        "highest": max(numbers),
        "missing": [n for n in range(1, max(numbers) + 1) if n not in counts],
        "repeated": sorted(n for n, count in counts.items() if count > 1),
        "repeated_on_one_page": sorted({n for (n, _), count in Counter(headings).items() if count > 1}),
        "out_of_order": [
            (number, previous, page)
            for (previous, _), (number, page) in zip(headings, headings[1:])
            if number < previous
        ],
    }


def describe(path: Path, rng: random.Random) -> dict:
    reader = PdfReader(path)
    pages = list(reader.pages)
    texts = [page.extract_text() for page in pages]
    with_text = [len("".join(text.split())) >= MIN_TEXT_CHARS for text in texts]
    with_page_image = [has_page_image(page) for page in pages]
    metadata = reader.metadata

    doc = {
        "name": path.name,
        "pages": len(pages),
        "size_mb": path.stat().st_size / 1e6,
        "creator": metadata.creator if metadata else None,
        "producer": metadata.producer if metadata else None,
        "text_pages": sum(with_text),
        "image_pages": sum(with_page_image),
        "invisible_pages": sum(has_invisible_text(page) for page in pages),
        "pages_without_text": [number for number, has in enumerate(with_text, 1) if not has],
    }
    doc["verdict"] = text_layer_verdict(doc["pages"], doc["text_pages"], doc["image_pages"])
    doc["has_text"] = doc["text_pages"] > 0
    if not doc["has_text"]:
        return doc

    text = "\n".join(texts)
    doc["words"] = len(text.split())
    doc["chunks_by_words"] = math.ceil(doc["words"] / WORDS_PER_CHUNK)

    headings = [
        (int(match.group(1)), page_number)
        for page_number, page_text in enumerate(texts, 1)
        for match in ARTICLE_HEADING.finditer(page_text)
    ]
    doc["headings"] = len(headings)
    doc["numbering"] = check_numbering(headings) if headings else None

    lines = Counter(line.strip() for page_text in texts for line in page_text.splitlines() if line.strip())
    doc["repeated_lines"] = [(line, count) for line, count in lines.most_common(TOP_LINES) if count > 1]

    page_starts, offset = [], 0  # where each page begins inside `text`
    for page_text in texts:
        page_starts.append(offset)
        offset += len(page_text) + 1
    last_start = max(len(text) - SAMPLE_CHARS, 0)
    doc["samples"] = [
        (bisect.bisect_right(page_starts, start), start, text[start : start + SAMPLE_CHARS])
        for start in sorted(rng.randint(0, last_start) for _ in range(SAMPLES))
    ]
    return doc


def ranges(numbers: list[int]) -> str:
    """[1, 2, 3, 7] -> '1–3, 7'. Expects sorted, distinct numbers."""
    if not numbers:
        return "none"
    spans, start, end = [], numbers[0], numbers[0]
    for number in numbers[1:]:
        if number == end + 1:
            end = number
            continue
        spans.append((start, end))
        start = end = number
    spans.append((start, end))
    return ", ".join(str(a) if a == b else f"{a}–{b}" for a, b in spans)


def fenced(text: str) -> list[str]:
    """A Markdown code block whose fence is longer than any run of backticks inside it."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return [f"{fence}text", text, fence]


def is_consecutive(numbering: dict) -> bool:
    return not (numbering["missing"] or numbering["repeated"] or numbering["out_of_order"])


def looks_doubled(numbering: dict | None) -> bool:
    """Most article numbers appearing twice on one page means the page text is stored twice."""
    return bool(numbering) and len(numbering["repeated_on_one_page"]) > numbering["distinct"] / 2


def render_warnings(docs: list[dict]) -> list[str]:
    warnings = []
    for doc in docs:
        name = f"`{doc['name']}`"
        if doc["image_pages"] and not doc["has_text"]:
            warnings.append(f"- {name} is a scan with **no text layer**. It needs OCR, which this script does not run.")
        elif doc["image_pages"]:
            warnings.append(
                f"- {name} is a **scan**. Its text comes from an OCR layer already inside the PDF, "
                f"so the figures below describe OCR output, not the original text."
            )
        if doc["has_text"] and looks_doubled(doc["numbering"]):
            numbering = doc["numbering"]
            warnings.append(
                f"- {name}: {len(numbering['repeated_on_one_page'])} of its {numbering['distinct']} article numbers "
                f"appear more than once on the same page, so the page text is probably stored twice. "
                f"Its word count and {WORDS_PER_CHUNK}-word chunk estimate are inflated."
            )
    return warnings


def render_summary(docs: list[dict]) -> list[str]:
    rows = [
        f'| File | Pages | Size | Text layer | Words | "Artículo N" headings | Numbers consecutive '
        f"| Chunks, 1 per article | Chunks, {WORDS_PER_CHUNK} words |",
        "|---|---:|---:|---|---:|---:|---|---:|---:|",
    ]
    for doc in docs:
        cells = [f"`{doc['name']}`", str(doc["pages"]), f"{doc['size_mb']:.1f} MB", doc["verdict"]]
        if doc["has_text"]:
            numbering = doc["numbering"]
            cells += [
                f"{doc['words']:,}",
                f"{doc['headings']:,}",
                ("yes" if is_consecutive(numbering) else "no") if numbering else "no headings",
                f"{numbering['distinct'] if numbering else 0:,}",
                f"{doc['chunks_by_words']:,}",
            ]
        else:
            cells += ["none"] * 5
        rows.append("| " + " | ".join(cells) + " |")
    with_text = [doc for doc in docs if doc["has_text"]]
    rows.append(
        f"| **Total** | {sum(doc['pages'] for doc in docs)} | {sum(doc['size_mb'] for doc in docs):.1f} MB | "
        f"| {sum(doc['words'] for doc in with_text):,} | {sum(doc['headings'] for doc in with_text):,} | "
        f"| {sum(doc['numbering']['distinct'] for doc in with_text if doc['numbering']):,} "
        f"| {sum(doc['chunks_by_words'] for doc in with_text):,} |"
    )
    return rows


def render_document(doc: dict) -> list[str]:
    pages = doc["pages"]
    out = [
        f"## {doc['name']}",
        "",
        f"- **Pages:** {pages}",
        f"- **File size:** {doc['size_mb']:.1f} MB",
        f"- **Text layer:** {doc['verdict']}",
        f"  - Pages holding a full-page image: {doc['image_pages']} of {pages}",
        f"  - Pages with extractable text: {doc['text_pages']} of {pages}",
        f"  - Pages whose text is invisible (OCR-style): {doc['invisible_pages']} of {pages}",
        f"  - Pages without text: {ranges(doc['pages_without_text'])}",
        f"- **PDF creator:** {doc['creator'] or 'not recorded'}; **producer:** {doc['producer'] or 'not recorded'}",
    ]
    if not doc["has_text"]:
        return out + ["", "No text can be extracted, so nothing else is reported. OCR was not run.", ""]

    out.append(f"- **Words in the extracted text:** {doc['words']:,}")
    numbering = doc["numbering"]
    if numbering is None:
        out.append('- **"Artículo N" headings:** 0')
        out.append(f"- **Chunk estimate:** 0 at one per article (no headings found); "
                   f"{doc['chunks_by_words']} at {WORDS_PER_CHUNK} words each")
    else:
        out.append(
            f'- **"Artículo N" headings:** {doc["headings"]} found, {numbering["distinct"]} distinct numbers, '
            f"highest {numbering['highest']}"
        )
        out.append(f"- **Numbers run 1 to {numbering['highest']} without gaps:** "
                   f"{'yes' if is_consecutive(numbering) else 'no'}")
        out.append(f"  - Missing: {ranges(numbering['missing'])}")
        repeated = ranges(numbering["repeated"])
        if numbering["repeated"]:
            repeated += (f" (count: {len(numbering['repeated'])}; "
                         f"more than once on a single page: {len(numbering['repeated_on_one_page'])})")
        out.append(f"  - Repeated: {repeated}")
        out_of_order = numbering["out_of_order"]
        if out_of_order:
            out.append(
                f"  - Out of order (lower than the heading before it): "
                f"{ranges(sorted({number for number, _, _ in out_of_order}))} (occurrences: {len(out_of_order)})"
            )
            shown = "; ".join(
                f"Artículo {number} after Artículo {previous} (page {page})"
                for number, previous, page in out_of_order[:CONTEXT_LIMIT]
            )
            label = "In context" if len(out_of_order) <= CONTEXT_LIMIT else f"First {CONTEXT_LIMIT} in context"
            out.append(f"  - {label}: {shown}")
        else:
            out.append("  - Out of order (lower than the heading before it): none")
        out.append(
            f"- **Chunk estimate:** {numbering['distinct']} at one per article (distinct numbers); "
            f"{doc['chunks_by_words']} at {WORDS_PER_CHUNK} words each"
        )

    out += ["", f"### {TOP_LINES} most repeated lines", ""]
    if doc["repeated_lines"]:
        out += fenced("\n".join(f"{count:>5}x  {line}" for line, count in doc["repeated_lines"]))
    else:
        out.append("No line appears more than once.")

    out += ["", f"### {SAMPLES} random {SAMPLE_CHARS}-character samples of the raw text", ""]
    for index, (page, start, sample) in enumerate(doc["samples"], 1):
        out.append(f"Sample {index}: page {page}, characters {start:,} to {start + len(sample):,}")
        out.append("")
        out += fenced(sample)
        out.append("")
    return out


def percentile(values: list[int], fraction: float) -> int:
    """Nearest-rank percentile: the smallest value with at least that share of the values at or below it."""
    ordered = sorted(values)
    return ordered[math.ceil(fraction * len(ordered)) - 1]


def chunk_stats(articles: list[index.Article], limit: int) -> dict:
    """What chunking these articles at `limit` words would produce. Nothing is saved."""
    per_article = [index.chunk_article(article, limit) for article in articles]
    chunks = [chunk for article_chunks in per_article for chunk in article_chunks]
    words = [chunk.words for chunk in chunks]
    return {
        "chunks": len(chunks),
        "articles_split": sum(len(article_chunks) > 1 for article_chunks in per_article),
        "median": statistics.median(words),
        "max": max(words),
        "over": [chunk for chunk in chunks if chunk.words > limit],  # each is one piece with nowhere to cut
    }


def table(header: list[str], rows: list[list[str]], left: tuple[int, ...] = (0,)) -> list[str]:
    """A Markdown table. Columns listed in `left` are left-aligned, the rest right-aligned."""
    rule = ["---" if position in left else "---:" for position in range(len(header))]
    return ["| " + " | ".join(cells) + " |" for cells in [header, rule, *rows]]


def render_cleaned(articles: list[dict], report: dict, rng: random.Random) -> list[str]:
    sources = list(report)
    by_source = {source: [a for a in articles if a["source"] == source] for source in sources}
    out = [
        "## After extraction and cleaning",
        "",
        f"From `{index.ARTICLES_FILE.relative_to(ROOT)}` and `{index.REPORT_FILE.relative_to(ROOT)}`, which "
        "`uv run python main.py index` writes. Each record of the first file is one article with its source file, "
        "number, title, título, capítulo, sección, start page, word count and text. Line breaks are kept as "
        "extracted, so every row of the norma's fee table is still one line.",
        "",
        "### Words and articles per document",
        "",
    ]
    rows = [
        [
            f"`{source}`",
            EXTRACTION_LABELS.get(report[source]["extraction"], report[source]["extraction"]),
            f"{report[source]['articles']:,}",
            f"{report[source]['article_words']:,}",
            f"{report[source]['preamble_words']:,}",
            f"{report[source]['closing_words']:,}",
        ]
        for source in sources
    ]
    rows.append(
        ["**Total**", ""]
        + [f"{sum(report[source][key] for source in sources):,}"
           for key in ("articles", "article_words", "preamble_words", "closing_words")]
    )
    out += table(
        ["File", "Extraction", "Articles", "Words in articles", "Preamble words left out", "Closing words left out"],
        rows,
        left=(0, 1),
    )
    out += [
        "",
        "The preamble is everything before the first article (considerandos, vistos, the title of the text). The "
        "closing is everything from the formula `Dada en ...` or `DADO en ...` after the last article (date, "
        "signatures, promulgation). Neither is saved as an article.",
        "",
        "### Lines removed, by rule",
        "",
    ]
    rules = list(dict.fromkeys(rule for source in sources for rule in report[source]["lines_removed"]))
    rows = [
        [rule] + [
            f"{report[source]['lines_removed'][rule]:,}" if rule in report[source]["lines_removed"] else "n/a"
            for source in sources
        ]
        for rule in rules
    ]
    rows.append(["**Lines removed**"] + [f"{sum(report[s]['lines_removed'].values()):,}" for s in sources])
    rows.append(["**Lines extracted**"] + [f"{report[s]['lines_extracted']:,}" for s in sources])
    out += table(["Rule"] + [f"`{source}`" for source in sources], rows)
    out += [
        "",
        "What each rule matches (`n/a` means the rule is not applied to that file):",
        "",
        f"- **header: ...** The named running header, only within the first {index.HEADER_WINDOW} non-empty lines "
        "of a page. The law's patterns also accept the ways the OCR misreads its header, such as `CONGI L`, "
        "`AbUNIO. Lgy ¿g Aduanas de la República Dominicana.` and `PAG- 17C`.",
        f"- **{index.RULE_PAGE_NUMBER_AFTER_PAG}** The line right after the law's `PAG.` header, when it has at most "
        f"{index.PAGE_NUMBER_MAX_CHARS} characters and no run of three letters. The stamped page numbers are read "
        "as things like `4-06-` or `??Q`.",
        f"- **{index.RULE_PAGE_NUMBER}** A line made only of the number of the page it is on.",
        f"- **{index.RULE_PAGE_NUMBER_STRAY}** One stray character, spaces and the number of the page, "
        "such as `t  64` on page 64.",
        f"- **{index.RULE_STRAY_CHARACTER}** A line holding a single character.",
        f"- **{index.RULE_ONLY_PLACEHOLDERS}** A line that held nothing but `(cid:N)` glyph placeholders.",
        f"- **{index.RULE_HEADING_JUNK}** A line without three letters in a row, sitting between a título, "
        "capítulo or sección heading and its first article.",
        "",
        "Changes made inside lines, which remove no line:",
        "",
    ]
    for source in sources:
        if report[source]["glyph_placeholders_deleted"]:
            out.append(
                f"- `{source}`: {report[source]['glyph_placeholders_deleted']} `(cid:N)` glyph placeholders deleted."
            )
        if report[source]["heading_name_tokens_deleted"]:
            out.append(
                f"- `{source}`: {report[source]['heading_name_tokens_deleted']} debris tokens deleted from heading "
                "names written in capitals (any token that is not capitals, such as `Lyti`, or a lone letter that "
                "is not a word)."
            )
        for wrong, right in report[source]["hand_fixes"]:
            out.append(f"- `{source}`: hand fix, `{wrong}` changed to `{right}`.")
    out += [
        "- Headings: `TÍTULO`, `CAPÍTULO` and `SECCIÓN` are written with their accent and an upper-case Roman "
        "numeral in the article records, reading a lower-case `l` as `I` (the OCR gives `TÍTULO Vil` for VII).",
        "",
        f"Lines of 2 to {SHORT_LINE_CHARS} characters still inside the articles. No rule removes them: some are "
        "real text, others are debris longer than one character.",
        "",
    ]
    for source in sources:
        short = Counter(
            line for a in by_source[source] for line in a["text"].splitlines() if 2 <= len(line) <= SHORT_LINE_CHARS
        )
        shown = ", ".join(f"`{line}` x{count}" for line, count in short.most_common(SHORT_LINES_SHOWN))
        out.append(f"- `{source}`: {sum(short.values())} lines" + (f". Most frequent: {shown}" if short else ""))

    out += ["", "### Article length in words", ""]
    rows = []
    for label, items in [(f"`{source}`", by_source[source]) for source in sources] + [("**All**", articles)]:
        words = [a["words"] for a in items]
        rows.append([
            label, f"{len(words):,}", f"{min(words):,}", f"{statistics.median(words):,g}",
            f"{percentile(words, 0.9):,}", f"{max(words):,}",
        ])
    out += table(["File", "Articles", "Min", "Median", "P90", "Max"], rows)
    out += ["", "P90 is the length that 90% of the articles do not exceed.", ""]

    ranked = sorted(articles, key=lambda a: a["words"])
    for heading, chosen in (
        (f"### {EXTREMES} longest articles", ranked[: -EXTREMES - 1 : -1]),
        (f"### {EXTREMES} shortest articles", ranked[:EXTREMES]),
    ):
        out += [heading, ""]
        out += table(
            ["File", "Article", "Words", "Page", "Title"],
            [[f"`{a['source']}`", str(a["number"]), f"{a['words']:,}", str(a["page"]), a["title"] or "(none)"] for a in chosen],
            left=(0, 4),
        )
        out.append("")

    out += [
        f"### {RANDOM_ARTICLES} random cleaned articles in full",
        "",
        f"Drawn from all {len(articles):,} articles with a fixed seed ({SEED}), so reruns show the same ones.",
        "",
    ]
    for a in rng.sample(articles, RANDOM_ARTICLES):
        out += [
            f"#### `{a['source']}`, article {a['number']}",
            "",
            f"- **Title:** {a['title'] or '(none)'}",
            f"- **Under:** {' / '.join(level for level in (a['titulo'], a['capitulo'], a['seccion']) if level) or '(no heading)'}",
            f"- **Starts on page:** {a['page']}; **words:** {a['words']:,}",
            "",
        ]
        out += fenced(a["text"])
        out.append("")
    return out


def render_chunking(articles: list[dict]) -> list[str]:
    counted = [index.Article(**a) for a in articles if a["source"] not in ADDED_LATER]
    stats = {limit: chunk_stats(counted, limit) for limit in CHUNK_LIMITS}
    out = [
        "## Chunking dry run",
        "",
        f"Nothing is embedded and no chunk is saved: `index.chunk_article` is applied in memory to the articles in "
        f"`{index.ARTICLES_FILE.relative_to(ROOT)}`. {', '.join(f'`{source}`' for source in ADDED_LATER)} is left "
        f"out because it will be added later through the add-document tool. That leaves {len(counted):,} articles "
        f"and {sum(a.words for a in counted):,} words.",
        "",
        "The rule, for a chunk size of LIMIT words:",
        "",
        "- An article at or under LIMIT is one chunk.",
        "- A longer article is cut before every line that opens a párrafo (`Párrafo I.-`, `Párrafo:`, "
        "`PÁRRAFO II.`) or a numbered item (`1) ...`, `1. ...`). Consecutive pieces are then packed together, in "
        "order, while their total stays at or under LIMIT.",
        "- A piece that is over LIMIT by itself has no boundary inside, so it stays whole as one chunk.",
        "- Lettered items (`a) ...`) are not boundaries.",
    ]
    for article in counted:
        if article.number in index.DOCUMENTS[article.source].one_item_per_chunk:
            out.append(
                f"- `{article.source}` article {article.number} ({article.title}) is one numbered item per chunk at "
                f"every LIMIT: {len(index.chunk_article(article, CHUNK_LIMITS[0])):,} chunks, with the article's "
                "opening sentence in the first."
            )
    out += [
        "- Every chunk keeps the source file, article number, title, título, capítulo and sección of its article.",
        "",
    ]
    out += table(
        ["LIMIT", "Total chunks", "Articles split", "Median chunk words", "Max chunk words", "Chunks over LIMIT"],
        [
            [
                str(limit), f"{entry['chunks']:,}", f"{entry['articles_split']:,}", f"{entry['median']:,g}",
                f"{entry['max']:,}", f"{len(entry['over']):,}",
            ]
            for limit, entry in stats.items()
        ],
        left=(),
    )
    out += [
        "",
        "An article is split when it gives more than one chunk. Chunk words count the text of the chunk only, not "
        "the fields kept with it.",
        "",
        "### Pieces still over LIMIT",
        "",
        "Each of these is a single piece with no párrafo or numbered item inside to cut at. The last column counts "
        "its lines that open a lettered item.",
        "",
    ]
    for limit, entry in stats.items():
        if not entry["over"]:
            out.append(f"LIMIT {limit}: none.")
            out.append("")
            continue
        out.append(f"LIMIT {limit}:")
        out.append("")
        out += table(
            ["File", "Article", "Chunk of the article", "Words", "Starts with", "Lettered items inside"],
            [
                [
                    f"`{chunk.source}`",
                    str(chunk.number),
                    str(chunk.part),
                    f"{chunk.words:,}",
                    " ".join(chunk.text.split())[:PREVIEW_CHARS].replace("|", "\\|") + " ...",
                    str(sum(1 for line in chunk.text.splitlines() if LETTERED_ITEM.match(line))),
                ]
                for chunk in sorted(entry["over"], key=lambda chunk: -chunk.words)
            ],
            left=(0, 4),
        )
        out.append("")
    return out


def render(docs: list[dict], articles: list[dict], report: dict, rng: random.Random) -> list[str]:
    out = [
        "# Corpus description",
        "",
        f"Written by `scripts/describe_corpus.py`. The first part describes the PDFs in "
        f"`{RAW_DIR.relative_to(ROOT)}/` before any cleaning, exactly as pypdf {pypdf.__version__} extracts them. "
        f"\"After extraction and cleaning\" describes the articles the index stage saves, and the last part, "
        f"\"Chunking dry run\", what the chunking rule would make of them.",
        "",
    ]
    warnings = render_warnings(docs)
    if warnings:
        out += ["## Read this first", ""] + warnings + [""]
    out += ["## Summary", ""] + render_summary(docs) + [""]
    out += [
        "How the columns are measured:",
        "",
        f"- **Text layer.** A page has text when pypdf extracts at least {MIN_TEXT_CHARS} non-space characters "
        f"from it. It holds a full-page image when one of its images is large enough to cover the whole page at "
        f"72 dpi or more. Its text is invisible when the page uses text render mode 3, the way OCR layers are stored.",
        '- **"Artículo N" headings.** Lines that start with a capitalised `Artículo` or `ARTÍCULO` (accent '
        "optional) followed by a number. Lower-case line starts are treated as cross-references.",
        f"- **Chunk estimates.** One per article is the count of distinct article numbers. The other is words "
        f"divided by {WORDS_PER_CHUNK}, rounded up, with no overlap.",
        f"- **Samples.** Random positions with a fixed seed ({SEED}), so reruns show the same samples.",
        "",
    ]
    for doc in docs:
        out += render_document(doc)
    out += render_cleaned(articles, report, rng)
    out += render_chunking(articles)
    return out


def main() -> None:
    for path in (index.ARTICLES_FILE, index.REPORT_FILE):
        if not path.is_file():
            raise FileNotFoundError(f"{path} is missing. Run `uv run python main.py index` first.")
    paths = sorted(RAW_DIR.glob("*.pdf"))
    if not paths:
        raise FileNotFoundError(f"No PDFs found in {RAW_DIR}. Run `uv run python main.py index` first.")
    with index.ARTICLES_FILE.open(encoding="utf-8") as file:
        articles = [json.loads(line) for line in file]
    report = json.loads(index.REPORT_FILE.read_text(encoding="utf-8"))
    rng = random.Random(SEED)
    docs = [describe(path, rng) for path in paths]
    lines = render(docs, articles, report, random.Random(SEED))
    OUTPUT.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    for doc in docs:
        print(f"{doc['name']}: {doc['verdict']}")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
