"""
Write TOC.md: the título / capítulo / sección tree of every indexed document,
with each article's number, title, start page and word count.
`uv run python scripts/write_toc.py`

It reads index/articles.jsonl, which `uv run python main.py index` writes, and
calls no API. The norma is left out because it is not in the index.

The last section pairs articles of the law with the articles of its two
reglamentos that cite them, and lists the law articles that defer to the
reglamento. Both are found by pattern, not by reading.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import index  # noqa: E402  (the index stage, for its documents and its article records)

OUTPUT = ROOT / "TOC.md"
LAW = "ley-168-21.pdf"
REGLAMENTOS = ("decreto-755-22.pdf", "decreto-609-24.pdf")
TERM = re.compile(r"\d+\)\s*(.+?):")  # "3) Admisión temporal: La Admisión ..." -> the term before the first colon
PREVIEW_WORDS = 12  # of the start of an article that has no title

# --- the law deferring to the reglamento ---
MENTION = re.compile(r"reglament", re.IGNORECASE)  # reglamento(s), reglamentariamente, reglamentarias
# The reglamento named next to the law or another body of rules, not instead of it: "esta ley y su reglamento",
# "legales y reglamentarias", "la ley, su reglamento y ...", "la misma y su reglamento".
GENERAL_FORMULA = re.compile(
    r"(?:\b(?:ley|leyes|decretos|legales)\s+[yo]\s+(?:\S+\s+){0,3}"
    r"|\bley,\s+su\w*\s+(?:\S+\s+){0,2}"
    r"|\by\s+su\w*\s+(?:\S+\s+){0,2})$",
    re.IGNORECASE,
)
WORDS_BEFORE, WORDS_AFTER = 6, 3  # of a mention, shown with it

# --- a reglamento citing numbered articles of the law ---
# "artículo 88", "artículos 168, 169 y 170", "articulos 264 al 266", and the OCR's "artíeulo".
CITATION = re.compile(r"\bart[íi][ce]u[l1]os?\s+(\d+(?:\s*(?:,|y|e|al)\s*\d+)*)", re.IGNORECASE)
# What the text names after the numbers. "ley" is searched without word boundaries because the OCR fuses "delaLeynúm.".
INSTRUMENT = re.compile(
    r"(?P<same>de\s+la\s+misma)|(?P<law>ley)"
    r"|(?P<other>reglamento|decreto|c[óo]digo|constituci[óo]n|resoluci[óo]n|norma|acuerdo|convenio)",
    re.IGNORECASE,
)
# Only words like these may stand between the numbers and the instrument: "..., numeral 2, de la [Ley]".
QUALIFIERS = (
    r"y|e|o|de|del|dela|la|las|los|el|al|en|su|sus|siguientes?|numeral(?:es)?|p[áa]rrafos?|literal(?:es)?"
    r"|incisos?|ordinal(?:es)?|cap[íi]tulos?|t[íi]tulos?|art[íi][ce]u[l1]os?|presente|este|esta|dicha|dicho"
    r"|referida|citada|mencionada|[ivxl]+|\d+"
)
BRIDGE = re.compile(rf"(?:[\s,.;:]*(?:{QUALIFIERS})(?=[\s,.;:]|$))*[\s,.;:]*", re.IGNORECASE)
AFTER_LEY = re.compile(r"(?:es)?\s*(?:(?:n[úu]m\.?|no\.?)\s*)?(?:(?P<number>\d+)|(?P<de>de\s+(?P<name>\w+)))", re.IGNORECASE)
WINDOW = 90  # characters after the numbers in which the instrument is looked for


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


def deferrals(text: str) -> list[tuple[str, str]]:
    """Every mention of the reglamento in an article of the law, as (kind, the words around it).

    The kind is "general" for the formula that names the reglamento next to the
    law ("esta ley y su reglamento"), and "specific" when the reglamento alone
    is where the rule is to be found ("que establezca el reglamento").
    """
    words = text.split()
    found = []
    for position, word in enumerate(words):
        if not MENTION.search(word):
            continue
        before = " ".join(words[max(0, position - WORDS_BEFORE) : position])
        kind = "general" if GENERAL_FORMULA.search(before + " ") else "specific"
        found.append((kind, " ".join(words[max(0, position - WORDS_BEFORE) : position + 1 + WORDS_AFTER])))
    return found


def cited_articles(text: str, own_articles: int) -> dict[int, bool]:
    """The articles of the law a reglamento article cites: number -> whether the text names the law right there.

    A citation counts when the law is named after the numbers ("artículo 88 de
    la Ley núm. 168-21"), with only qualifiers in between. A citation that
    names nothing counts too, as implied, when the number is beyond the
    reglamento's own last article or the same article cites it elsewhere with
    the law named. Citations of the reglamento itself, of other laws and of
    decrees are left out.
    """
    cited: dict[int, bool] = {}
    unnamed: list[int] = []
    previous_is_law = False
    for match in CITATION.finditer(text):
        numbers = [int(number) for number in re.findall(r"\d+", match.group(1))]
        if re.search(r"\bal\b", match.group(1)) and len(numbers) == 2:
            numbers = list(range(numbers[0], numbers[1] + 1))
        tail = text[match.end() : match.end() + WINDOW]
        instrument = INSTRUMENT.search(tail)
        if instrument is None or not BRIDGE.fullmatch(tail[: instrument.start()]):
            unnamed += numbers
            continue
        if instrument.lastgroup == "law":
            after = AFTER_LEY.match(tail[instrument.end() :])
            another_law = after is not None and (
                (after.group("number") is not None and after.group("number") != "168")
                or (after.group("de") is not None and after.group("name").lower() != "aduanas")
            )
            previous_is_law = not another_law
        elif instrument.lastgroup == "other":
            previous_is_law = False
        # "de la misma" keeps whatever the citation before it named
        if previous_is_law:
            cited.update(dict.fromkeys(numbers, True))
    for number in unnamed:
        if number not in cited and number > own_articles:
            cited[number] = False
    return dict(sorted(cited.items()))


def law_citations(text: str, own_articles: int) -> list[int]:
    """The numbers of the articles of the law that a reglamento article cites."""
    return list(cited_articles(text, own_articles))


def render_cross_references(articles: list[index.Article]) -> list[str]:
    law = {article.number: article for article in articles if article.source == LAW}
    pairs = []  # (law article, reglamento article, whether the law is named in the citation)
    unknown = []
    for source in REGLAMENTOS:
        own = [article for article in articles if article.source == source]
        for article in own:
            body = index.HEADING_MARKER.sub("", " ".join(article.text.split()), count=1)
            for number, named in cited_articles(body, max(a.number for a in own)).items():
                if number in law:
                    pairs.append((law[number], article, named))
                else:
                    unknown.append(f"{label(article)} cites article {number}")
    pairs.sort(key=lambda pair: (pair[0].number, REGLAMENTOS.index(pair[1].source), pair[1].number))
    cited_by: dict[int, list[str]] = {}
    for law_article, reglamento_article, _ in pairs:
        cited_by.setdefault(law_article.number, []).append(label(reglamento_article))

    mentions = {number: deferrals(article.text) for number, article in law.items()}
    specific = {number: [phrase for kind, phrase in found if kind == "specific"] for number, found in mentions.items()}
    specific = {number: phrases for number, phrases in specific.items() if phrases}
    general = {
        number: [phrase for _, phrase in found] for number, found in mentions.items() if found and number not in specific
    }

    def cell(text: str) -> str:
        return text.replace("|", "\\|")

    def shown(phrases: list[str]) -> str:
        return cell(f"... {phrases[0]}" + (f" (+{len(phrases) - 1} more)" if len(phrases) > 1 else ""))

    out = [
        "## Cross-references between the law and its reglamentos",
        "",
        "Found by pattern in the cleaned text, not by reading, so check a pair before relying on it. The text is "
        "OCR: a citation or a deferral whose words were misread is not here.",
        "",
        "### Pairs: a reglamento article that cites a numbered article of the law",
        "",
        f"{len(pairs)} pairs: {len({(b.source, b.number) for _, b, _ in pairs})} reglamento articles cite "
        f"{len(cited_by)} articles of the law. ★ marks a law article that also defers to the reglamento in its "
        "own words (next table). *(implied)* marks a citation that does not name the law next to the number: it "
        "is counted because the number is beyond the reglamento's own last article.",
        "",
        "| Law art. | Law title | Page | Cited by | Its title | Page |",
        "| ---: | --- | ---: | --- | --- | ---: |",
    ]
    for law_article, reglamento_article, named in pairs:
        star = " ★" if law_article.number in specific else ""
        out.append(
            f"| {law_article.number}{star} | {cell(law_article.title or '(no title)')} | {law_article.page} "
            f"| {label(reglamento_article)}{'' if named else ' *(implied)*'} "
            f"| {cell(reglamento_article.title or '(no title)')} | {reglamento_article.page} |"
        )
    if unknown:
        out += ["", "Citations of an article number the law does not have, left out: " + "; ".join(unknown) + "."]
    out += [
        "",
        "### Law articles that defer to the reglamento",
        "",
        f"{len(specific) + len(general)} articles of the law mention the reglamento. The column of words shows "
        f"{WORDS_BEFORE} words before the mention and {WORDS_AFTER} after it.",
        "",
        f"#### Specific deferrals ({len(specific)})",
        "",
        "The reglamento alone is named as where the rule is set (`que establezca el reglamento`, `mediante "
        "reglamento`, `reglamentariamente`). The last column lists the reglamento articles that cite the law "
        "article by number; many deferrals are answered by articles that do not cite it, so an empty cell does "
        "not mean the reglamento is silent.",
        "",
        "| Art. | Title | Page | Words of the deferral | Reglamento articles that cite it |",
        "| ---: | --- | ---: | --- | --- |",
    ]
    for number, phrases in sorted(specific.items()):
        out.append(
            f"| {number} | {cell(law[number].title or '(no title)')} | {law[number].page} | {shown(phrases)} "
            f"| {', '.join(cited_by.get(number, []))} |"
        )
    out += [
        "",
        f"#### General formula only ({len(general)})",
        "",
        "The reglamento is only named in passing, next to the law or another body of rules (`esta ley y su "
        "reglamento`, `la ley, su reglamento y ...`, `legales y reglamentarias`).",
        "",
        "| Art. | Title | Page | Words |",
        "| ---: | --- | ---: | --- |",
    ]
    for number, phrases in sorted(general.items()):
        out.append(f"| {number} | {cell(law[number].title or '(no title)')} | {law[number].page} | {shown(phrases)} |")
    out.append("")
    return out


def label(article: index.Article) -> str:
    """A reglamento article in few words: "Decreto 755-22 art. 70"."""
    return f"{index.document_for(article.source).name.split(',')[0]} art. {article.number}"


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
        "- The last section, **Cross-references between the law and its reglamentos**, pairs law articles with "
        "the reglamento articles that cite them.",
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
    if any(article.source == LAW for article in articles):
        out += render_cross_references(articles)
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
