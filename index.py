"""
Assignment 3: build the index (`main.py index`).

So far this stage downloads the corpus into corpus/ (git-ignored), extracts the
text of each PDF, cleans it and splits it into articles. It then cuts the
articles into chunks, embeds the chunks that have no saved vector yet and
stores everything in ChromaDB. All of it is saved in index/:

- articles.jsonl, cleaning_report.json: the cleaned articles and what was removed
- embeddings.jsonl: every chunk vector received from the API, by hash
- query_embeddings.jsonl: the same for questions
- chroma/: the search index (vectors, text and metadata of every chunk)

Running the stage again sends nothing that already has a saved vector.
server.py imports `add_document` from here, so a document added later goes
through exactly the same steps.

The per-file steps are functions so that server.py's add-document tool can
import them.
"""

import atexit
import json
import re
import shutil
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

import chromadb
import httpx
import pdfplumber
from chromadb.config import Settings
from pypdf import PdfReader

import embeddings

ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "corpus"
INDEX_DIR = ROOT / "index"
ARTICLES_FILE = INDEX_DIR / "articles.jsonl"
REPORT_FILE = INDEX_DIR / "cleaning_report.json"
EMBEDDINGS_FILE = INDEX_DIR / "embeddings.jsonl"  # chunk vectors, by hash of the embedded text
QUERY_EMBEDDINGS_FILE = INDEX_DIR / "query_embeddings.jsonl"  # question vectors, same format
CHROMA_DIR = INDEX_DIR / "chroma"
COLLECTION = "corpus"
CHUNK_LIMIT = 400  # words per chunk, chosen from the dry run in CORPUS.md

Line = tuple[int, str]  # (page number, text)

# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

# pdfplumber's default tolerance of 3 leaves words fused in these scans, and 1
# splits words apart in the law. 1.5 was the best of the three on every file.
X_TOLERANCE = 1.5


def pdfplumber_pages(path: Path) -> list[str]:
    """Text of each page, with spaces placed from the position of the characters."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text(x_tolerance=X_TOLERANCE))
            page.close()
    return pages


def pypdf_page_layer(path: Path) -> list[str]:
    """Text each page draws itself, without the second copy held in its form XObjects.

    decreto-755-22 carries two OCR passes of every page: one in the page's own
    content stream and one inside the embedded scan object. pypdf returns the
    embedded copy first, so it is cut off the front of the page text.
    """
    pages = []
    for number, page in enumerate(PdfReader(path).pages, 1):
        text = page.extract_text()
        for xobject in page["/Resources"]["/XObject"].values():
            xobject = xobject.get_object()
            if xobject.get("/Subtype") == "/Form":
                embedded = page.extract_xform_text(xobject)
                if not text.startswith(embedded):
                    raise ValueError(
                        f"{path.name}, page {number}: the embedded text copy is not at the start of the page text."
                    )
                text = text[len(embedded) :]
        pages.append(text)
    return pages


# ---------------------------------------------------------------------------
# Page furniture
# ---------------------------------------------------------------------------

HEADER_WINDOW = 6  # header rules only look at the first non-empty lines of a page
PAGE_NUMBER_MAX_CHARS = 8  # a garbled page number after "PAG." is never longer
GLYPH_PLACEHOLDER = re.compile(r"\(cid:\d+\)")  # pdfplumber's text for a glyph it cannot map
THREE_LETTERS = re.compile(r"[^\W\d_]{3}")

RULE_ONLY_PLACEHOLDERS = "only glyph placeholders"
RULE_PAGE_NUMBER_AFTER_PAG = "page number after PAG."
RULE_PAGE_NUMBER = "page number"
RULE_PAGE_NUMBER_STRAY = "page number with a stray character"
RULE_STRAY_CHARACTER = "single stray character"

# The law's running header, including the ways the OCR misreads it: "CONGI L",
# "iSO NACIONAL", "AbUNIO. Lgy ¿g Aduanas de la República Dominicana.", "PAG- 17C".
NOT_A_LETTER = r"[^\sA-Za-zÀ-ÿ]"
LEY_HEADERS = (
    (
        "header: CONGRESO NACIONAL",
        re.compile(
            rf"CON|CONG\S*(?: .{{0,14}})?|CON \S*{NOT_A_LETTER}\S*"
            r"|(?:C?ONGRESO |\S{1,5} )?(?:NACIONAL|ACIONAL|CIONAL|IONAL|ONAL|NAL)"
        ),
    ),
    (
        "header: ASUNTO: Ley de Aduanas de la República Dominicana.",
        re.compile(r"(?:ASUNTO|AbUNIU)[:.]|.{0,20}Aduanas de la República Dominicana\."),
    ),
    ("header: PAG.", re.compile(r"PAG[.^\-](?: ?\S{1,4})?")),
)

# The letterhead on every page of both decrees.
DECREE_HEADERS = (
    ("header: LUIS ABINADER", re.compile(r"LUIS ?ABINADER")),
    ("header: PRESIDENTE DE LA REPÚBLICA DOMINICANA", re.compile(r"PRESIDENTE DE LA REP[ÚU]BLICA DOMINICANA")),
)


@dataclass(frozen=True)
class Document:
    filename: str
    url: str
    name: str  # how the document is called in the heading line of its chunks
    extract: Callable[[Path], list[str]] = pdfplumber_pages  # returns the text of each page
    headers: tuple[tuple[str, re.Pattern[str]], ...] = ()  # (rule name, whole-line pattern)
    page_number_after: str | None = None  # header rule that is followed by a garbled page number
    fixes: tuple[tuple[str, str], ...] = ()  # hand corrections: (text as extracted, corrected text)
    ordinal_headings: bool = False  # provisions are headed PRIMERO:, SEGUNDO: ... instead of Artículo N
    one_item_per_chunk: frozenset[int] = frozenset()  # articles chunked one numbered item at a time
    in_initial_index: bool = True  # False for a document left to be added later through the add-document tool
    table_row: re.Pattern[str] | None = None  # a line that is one row of a table, in a document that has tables


@dataclass
class Cleaned:
    lines: list[Line]
    removed: Counter = field(default_factory=Counter)  # rule name -> lines removed
    placeholders: int = 0  # "(cid:N)" glyph placeholders deleted inside lines


DOCUMENTS = {
    document.filename: document
    for document in (
        Document(
            filename="ley-168-21.pdf",
            url="https://oea.aduanas.gob.do/media/1499/ley_general_aduanas_168-21.pdf",
            name="Ley 168-21 de Aduanas",
            headers=LEY_HEADERS,
            page_number_after="header: PAG.",
            fixes=(("Artículo 22 9.-", "Artículo 229.-"),),
            one_item_per_chunk=frozenset({4}),  # Definiciones: one definition per chunk
        ),
        Document(
            filename="decreto-755-22.pdf",
            url=(
                "https://oea.aduanas.gob.do/media/1500/decreto-755-22-reglamento-de-aplicaci%C3%B3n"
                "-de-la-ley-n%C3%BAm-168-21-de-aduanas.pdf"
            ),
            name="Decreto 755-22, Reglamento de aplicación de la Ley 168-21 de Aduanas",
            extract=pypdf_page_layer,
            headers=DECREE_HEADERS,
        ),
        Document(
            filename="decreto-609-24.pdf",
            url="https://aduanas.gob.do/media/zcflhflg/decreto-609-24-reglamento-operadores-aduaneros.pdf",
            name="Decreto 609-24, Reglamento de aplicación del Título III de la Ley 168-21 de Aduanas",
            headers=DECREE_HEADERS,
        ),
        Document(
            filename="norma-01-2023.pdf",
            url="https://aduanas.gob.do/media/as3hx2ml/norma-general-01-2023-ajuste-tasas-por-servicios.pdf",
            name="Norma General 01-2023, ajuste de las tasas por servicios de la DGA",
            ordinal_headings=True,
            in_initial_index=False,
            table_row=re.compile(r"(?:RD|US)\$ [\d,]+\.\d\d$"),  # a fee: "... RD$ 4,000.00"
        ),
    )
}


def document_for(filename: str) -> Document:
    """The settings of a file: its own when it is a document of the corpus, the defaults otherwise."""
    return DOCUMENTS.get(filename) or Document(filename=filename, url="", name=Path(filename).stem)


def removal_rule(document: Document, text: str, page_number: int, position: int, previous_rule: str | None) -> str | None:
    """Name of the furniture rule that removes this line, or None to keep it.

    `position` counts the non-empty lines of the page from 0; `previous_rule`
    is the rule that removed the line just before, if one did.
    """
    if position < HEADER_WINDOW:
        for name, pattern in document.headers:
            if pattern.fullmatch(text):
                return name
    if (
        previous_rule is not None
        and previous_rule == document.page_number_after
        and len(text) <= PAGE_NUMBER_MAX_CHARS
        and not THREE_LETTERS.search(text)
    ):
        return RULE_PAGE_NUMBER_AFTER_PAG
    if text == str(page_number):
        return RULE_PAGE_NUMBER
    if re.fullmatch(rf"\S\s+{page_number}", text):
        return RULE_PAGE_NUMBER_STRAY
    if len(text) == 1:
        return RULE_STRAY_CHARACTER
    return None


def clean_pages(document: Document, pages: list[str]) -> Cleaned:
    """Drop page furniture from the extracted pages, counting what each rule removes."""
    cleaned = Cleaned(lines=[])
    for page_number, page_text in enumerate(pages, 1):
        position, previous_rule = 0, None
        for raw in page_text.splitlines():
            text, deleted = GLYPH_PLACEHOLDER.subn("", raw)
            cleaned.placeholders += deleted
            text = text.strip()
            if not text:
                if deleted:
                    cleaned.removed[RULE_ONLY_PLACEHOLDERS] += 1
                continue
            previous_rule = removal_rule(document, text, page_number, position, previous_rule)
            position += 1
            if previous_rule is None:
                cleaned.lines.append((page_number, text))
            else:
                cleaned.removed[previous_rule] += 1
    return cleaned


def apply_fixes(document: Document, lines: list[Line]) -> list[Line]:
    """Apply the document's hand corrections. Each must match exactly one line."""
    lines = list(lines)
    for wrong, right in document.fixes:
        hits = [index for index, (_, text) in enumerate(lines) if wrong in text]
        if len(hits) != 1:
            raise ValueError(
                f"{document.filename}: the hand fix for {wrong!r} must match exactly one line, "
                f"but it matches {len(hits)}."
            )
        page, text = lines[hits[0]]
        lines[hits[0]] = (page, text.replace(wrong, right))
    return lines


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

# A heading starts a line with a capitalised "Artículo" and a number. The accent
# and the space are optional because OCR drops them. Lower-case line starts
# ("artículo 50 de esta ley.") are cross-references wrapped onto a new line.
ARTICLE_HEADING = re.compile(r"(?:Art[íi]culo|ART[ÍI]CULO)\s*(\d+)")
HEADING_MARKER = re.compile(r"(?:Art[íi]culo|ART[ÍI]CULO)\s*\d+[\s.,:\-]*")
ORDINALS = {"PRIMERO": 1, "SEGUNDO": 2, "TERCERO": 3, "CUARTO": 4}
ORDINAL_NAMES = {number: name for name, number in ORDINALS.items()}
ORDINAL_HEADING = re.compile(r"(PRIMERO|SEGUNDO|TERCERO|CUARTO):")

# "TÍTULO II", "CAPITULO v", "Sección I", "SECCIÓN ÚNICA", alone on a line. One trailing token is
# tolerated only if it is not a word, as in the OCR debris "SECCIÓN IV C/>" and
# "TÍTULO V 5". The numeral is upper-cased, reading a lower-case l as I, because
# the OCR turns "TÍTULO VII" into "TÍTULO Vil".
STRUCTURE_HEADING = re.compile(
    rf"(T[ÍI]TULO|CAP[ÍI]TULO|SECCI[ÓO]N)\s+([IVXLC]+|[ÚU]NIC[AO])(?:\s+\S*{NOT_A_LETTER}\S*)?", re.IGNORECASE
)
LEVELS = {"T": ("titulo", "TÍTULO"), "C": ("capitulo", "CAPÍTULO"), "S": ("seccion", "SECCIÓN")}
LEVEL_ORDER = ("titulo", "capitulo", "seccion")

CLOSING = re.compile(r"dad[ao] en\b", re.IGNORECASE)  # "Dada en la Sala de Sesiones...", "DADO en Santo Domingo..."
# A full stop followed by the start of a sentence or of a numbered list ("1) Cuando ...").
TITLE_END = re.compile(r"\.(?=\s+(?:[A-ZÁÉÍÓÚÑ¿(\"“]|\d+\)))")
MAX_TITLE_WORDS = 20  # a longer first sentence is the article's text, not an epigraph

RULE_HEADING_JUNK = "junk line inside a heading name"

# The name under a heading written in capitals is in capitals too, so any other
# token on those lines is OCR debris ("DE LAS FALTAS Lyti"). A lone letter is
# debris as well unless it is a Spanish one-letter word.
CAPITALS_TOKEN = re.compile(r"[A-ZÁÉÍÓÚÑÜ0-9.,;:()\-/]+")
ONE_LETTER_WORDS = frozenset("YAOEU")


@dataclass
class Article:
    source: str
    number: int
    title: str  # "" when the article has no epigraph
    titulo: str  # "" when the article sits under none; same for capitulo and seccion
    capitulo: str
    seccion: str
    page: int  # page the article starts on
    words: int
    text: str


@dataclass
class Split:
    articles: list[Article]
    preamble_words: int = 0  # words before the first article
    closing_words: int = 0  # words from the closing formula on
    removed: Counter = field(default_factory=Counter)  # rule name -> lines removed
    heading_tokens_deleted: int = 0  # debris tokens taken out of heading names that were kept


def article_number(document: Document, text: str) -> int | None:
    """The number of the article this line opens, or None if it opens none."""
    if document.ordinal_headings:
        match = ORDINAL_HEADING.match(text)
        return ORDINALS[match.group(1)] if match else None
    match = ARTICLE_HEADING.match(text)
    return int(match.group(1)) if match else None


def split_title(text: str) -> str:
    """The epigraph of an article: the short phrase between its number and the first sentence end."""
    marker = HEADING_MARKER.match(text)
    if marker is None:
        return ""
    body = " ".join(text[marker.end() :].split())
    end = TITLE_END.search(body)
    if end is None:
        return ""
    title = body[: end.start()]
    if ":" in title or len(title.split()) > MAX_TITLE_WORDS:
        return ""  # a sentence that opens a list, or one too long to be an epigraph
    return title


def split_articles(document: Document, lines: list[Line]) -> Split:
    """Split cleaned lines into articles, tracking the título, capítulo and sección above each."""
    headings = [index for index, (_, text) in enumerate(lines) if article_number(document, text) is not None]
    if not headings:
        raise ValueError(f"{document.filename}: no article heading found.")
    end = next(
        (index for index in range(headings[-1] + 1, len(lines)) if CLOSING.match(lines[index][1])),
        len(lines),
    )
    split = Split(articles=[], closing_words=sum(len(text.split()) for _, text in lines[end:]))

    labels = dict.fromkeys(LEVEL_ORDER, "")  # "CAPÍTULO IV"
    names: dict[str, list[str]] = {level: [] for level in LEVEL_ORDER}  # the lines of its name
    naming: str | None = None  # the level whose name lines are being read
    in_capitals = False  # whether that heading is written in capitals
    opened: list[tuple[int, int, dict[str, str], list[str]]] = []  # number, page, levels, lines
    inside_article = False

    for page, text in lines[:end]:
        number = article_number(document, text)
        structure = STRUCTURE_HEADING.fullmatch(text)
        if number is not None:
            levels = {
                level: f"{labels[level]}: {' '.join(names[level])}" if names[level] else labels[level]
                for level in LEVEL_ORDER
            }
            opened.append((number, page, levels, [text]))
            naming, inside_article = None, True
        elif structure:
            level, label = LEVELS[structure.group(1)[0].upper()]
            numeral = structure.group(2).replace("l", "I").upper().replace("UNIC", "ÚNIC")
            labels[level], names[level] = f"{label} {numeral}", []
            for lower in LEVEL_ORDER[LEVEL_ORDER.index(level) + 1 :]:
                labels[lower], names[lower] = "", []
            naming, in_capitals, inside_article = level, structure.group(1).isupper(), False
        elif naming:
            words = text.split()
            if in_capitals:
                kept = [
                    word
                    for word in words
                    if CAPITALS_TOKEN.fullmatch(word) and (len(word) > 1 or word in ONE_LETTER_WORDS)
                ]
            else:
                kept = words
            if THREE_LETTERS.search(" ".join(kept)):
                names[naming].append(" ".join(kept))
                split.heading_tokens_deleted += len(words) - len(kept)
            else:
                split.removed[RULE_HEADING_JUNK] += 1
        elif inside_article:
            opened[-1][3].append(text)
        else:
            split.preamble_words += len(text.split())

    for number, page, levels, article_lines in opened:
        text = "\n".join(article_lines)
        split.articles.append(
            Article(
                source=document.filename,
                number=number,
                title=split_title(text),
                page=page,
                words=len(text.split()),
                text=text,
                **levels,
            )
        )
    return split


def check_numbering(articles: list[Article]) -> None:
    """Raise unless the articles are numbered 1..N, each number once and in order."""
    numbers = [article.number for article in articles]
    counts = Counter(numbers)
    missing = [number for number in range(1, max(numbers) + 1) if number not in counts]
    repeated = sorted(number for number, count in counts.items() if count > 1)
    if missing or repeated or numbers != sorted(numbers):
        raise ValueError(
            f"{articles[0].source}: article numbers do not run 1 to {max(numbers)} once each and in order: "
            f"missing {missing}, repeated {repeated}."
        )


# ---------------------------------------------------------------------------
# Chunks
# ---------------------------------------------------------------------------


# A piece of an article starts at a line that opens a párrafo ("Párrafo I.-",
# "Párrafo:", "PÁRRAFO II.", "PARRAFO 11.") or a numbered item ("1) ...",
# "4. Caso fortuito ..."). Lower-case "párrafo" at a line start is a
# cross-reference wrapped onto a new line. A marker with no text after it
# ("9)") is stamp debris, and the "N." form stops at two digits so that a
# wrapped year ("2018. Que ...") is not taken for an item.
PIECE_START = re.compile(r"(?:P[áa]rrafo|P[ÁA]RRAFO)\b|\d+\)\s*\S|\d{1,2}\.\s+\S")


@dataclass
class Chunk:
    source: str
    number: int  # of the article the chunk comes from
    title: str
    titulo: str
    capitulo: str
    seccion: str
    part: int  # position of the chunk inside its article, from 1
    page: int  # page the article starts on
    words: int
    text: str


def split_pieces(text: str) -> list[str]:
    """Cut an article's text before every line that opens a párrafo or a numbered item."""
    pieces: list[list[str]] = []
    for line in text.splitlines():
        if not pieces or PIECE_START.match(line):
            pieces.append([])
        pieces[-1].append(line)
    return ["\n".join(piece) for piece in pieces]


def pack(pieces: list[str], limit: int) -> list[str]:
    """Join consecutive pieces while the total stays at or under `limit` words."""
    packed: list[str] = []
    size = 0
    for piece in pieces:
        words = len(piece.split())
        if packed and size + words <= limit:
            packed[-1] += "\n" + piece
            size += words
        else:
            packed.append(piece)
            size = words
    return packed


def split_table(piece: str, row: re.Pattern[str], limit: int) -> list[str]:
    """Cut a table that is over the limit between its rows, never inside one.

    Every part starts with what comes before the first row (the sentence of the
    provision and the column headings), so a part read alone still says what
    its rows are. That opening counts towards the limit.
    """
    lines = piece.splitlines()
    first = next((position for position, line in enumerate(lines) if row.search(line)), None)
    if first is None:
        return [piece]
    opening = "\n".join(lines[:first])
    parts = pack(lines[first:], limit - len(opening.split()))
    return [f"{opening}\n{part}" if opening else part for part in parts]


def chunk_article(article: Article, limit: int) -> list[Chunk]:
    """Cut an article into chunks of at most `limit` words, where its boundaries allow.

    At or under the limit the article is one chunk. Over it, the article is cut
    into pieces (see PIECE_START) and consecutive pieces are packed together up
    to the limit; a piece that is over the limit by itself stays whole. Articles
    named in the document's `one_item_per_chunk` ignore the limit: every piece
    is a chunk, the opening lines going with the first one. In a document with
    tables, a piece still over the limit is cut between table rows.
    """
    document = document_for(article.source)
    if article.number in document.one_item_per_chunk:
        opening, *items = split_pieces(article.text)
        if not items:
            raise ValueError(
                f"{article.source}, article {article.number}: set to one numbered item per chunk, "
                "but no line in it opens a numbered item."
            )
        texts = [f"{opening}\n{items[0]}", *items[1:]]
    elif article.words <= limit:
        texts = [article.text]
    else:
        texts = pack(split_pieces(article.text), limit)
        if document.table_row:
            texts = [
                part
                for text in texts
                for part in (split_table(text, document.table_row, limit) if len(text.split()) > limit else [text])
            ]
    return [
        Chunk(
            source=article.source,
            number=article.number,
            title=article.title,
            titulo=article.titulo,
            capitulo=article.capitulo,
            seccion=article.seccion,
            part=part,
            page=article.page,
            words=len(text.split()),
            text=text,
        )
        for part, text in enumerate(texts, 1)
    ]


def initial_chunks(articles: list[Article]) -> list[Chunk]:
    """The chunks of the initial index: every document except those left for the add-document tool."""
    return [
        chunk
        for article in articles
        if DOCUMENTS[article.source].in_initial_index
        for chunk in chunk_article(article, CHUNK_LIMIT)
    ]


# ---------------------------------------------------------------------------
# The search index
# ---------------------------------------------------------------------------


def heading_path(chunk: Chunk) -> str:
    """The título, capítulo and sección above a chunk, in one string."""
    return " / ".join(level for level in (chunk.titulo, chunk.capitulo, chunk.seccion) if level)


def article_label(source: str, number: int) -> str:
    """How a provision is named: "Artículo 80", or its ordinal in a document headed by ordinals."""
    if document_for(source).ordinal_headings:
        return ORDINAL_NAMES[number]
    return f"Artículo {number}"


def heading(chunk: Chunk) -> str:
    """One line that places a chunk: its document, article, title and the headings above it."""
    parts = (
        document_for(chunk.source).name,
        article_label(chunk.source, chunk.number),
        chunk.title,
        heading_path(chunk),
    )
    return " — ".join(part for part in parts if part)


def citation(metadata: Mapping) -> str:
    """Where a stored chunk comes from: document, article, title, part, the article's start page and file."""
    parts = (
        document_for(metadata["source"]).name,
        article_label(metadata["source"], metadata["article"]),
        metadata["title"],
        f"part {metadata['part']}",
        f"page {metadata['page']}",
        metadata["source"],
    )
    return " — ".join(part for part in parts if part)


def embedded_text(chunk: Chunk) -> str:
    """Exactly what is sent to the embedding model for a chunk: its heading as title, then its text."""
    return embeddings.document_prompt(heading(chunk), chunk.text)


def chunk_record(chunk: Chunk) -> tuple[str, str, dict]:
    """A chunk's id, text and metadata, as the collection stores them."""
    text = embedded_text(chunk)
    metadata = {
        "source": chunk.source,
        "article": chunk.number,
        "part": chunk.part,
        "title": chunk.title,
        "path": heading_path(chunk),
        "page": chunk.page,
        "embedded_text": text,
        "embedding_key": embeddings.cache_key(text),  # where its vector is in the embedding cache
    }
    return f"{chunk.source}#{chunk.number}#{chunk.part}", chunk.text, metadata


def open_collection(folder: Path = CHROMA_DIR, create: bool = False):
    """Open the saved search index. It reads files only: nothing here can call the API."""
    if not create and not folder.is_dir():
        raise FileNotFoundError(f"{folder} is missing. Run `uv run python main.py index` first.")
    client = chromadb.PersistentClient(path=str(folder), settings=Settings(anonymized_telemetry=False))
    if create:
        return client.get_or_create_collection(
            COLLECTION, configuration={"hnsw": {"space": "cosine"}}, embedding_function=None
        )
    return client.get_collection(COLLECTION, embedding_function=None)


def open_snapshot(folder: Path = CHROMA_DIR):
    """Open a temporary copy of the saved search index, for reading.

    ChromaDB writes a lock record into its SQLite file every time it is opened.
    Reading from a copy keeps the committed files in index/ exactly as they are.
    """
    if not folder.is_dir():
        raise FileNotFoundError(f"{folder} is missing. Run `uv run python main.py index` first.")
    parent = Path(tempfile.mkdtemp(prefix="corpus-index-"))
    atexit.register(shutil.rmtree, parent, ignore_errors=True)
    shutil.copytree(folder, parent / "chroma")
    return open_collection(parent / "chroma")


def store_chunks(collection, chunks: list[Chunk], vectors: Mapping[str, Sequence[float]]) -> tuple[int, int]:
    """Make the collection hold exactly these chunks for the documents they come from.

    A chunk already stored unchanged is not touched, a chunk its document no
    longer produces is deleted, and other documents are left alone. `vectors`
    is the embedding cache. Returns how many chunks were written and deleted.
    """
    wanted = {chunk_id: (text, metadata) for chunk_id, text, metadata in map(chunk_record, chunks)}
    sources = sorted({chunk.source for chunk in chunks})
    stored = collection.get(where={"source": {"$in": sources}}, include=["documents", "metadatas"])
    current = dict(zip(stored["ids"], zip(stored["documents"], stored["metadatas"])))
    stale = [chunk_id for chunk_id in current if chunk_id not in wanted]
    changed = [chunk_id for chunk_id, record in wanted.items() if current.get(chunk_id) != record]
    if stale:
        collection.delete(ids=stale)
    if changed:
        collection.upsert(
            ids=changed,
            documents=[wanted[chunk_id][0] for chunk_id in changed],
            metadatas=[wanted[chunk_id][1] for chunk_id in changed],
            embeddings=[vectors[wanted[chunk_id][1]["embedding_key"]] for chunk_id in changed],
        )
    return len(changed), len(stale)


@dataclass
class AddResult:
    source: str
    chunks: int  # chunks the document has in the index after the call
    added: int  # chunks written: new ones, and ones whose content changed
    removed: int  # chunks deleted, and old versions of the ones that changed
    unchanged: int  # chunks that were already stored exactly as they are now
    sent: int  # texts sent to the embedding API
    stopped: str = ""  # why nothing was stored, when the embedding could not finish


def index_document(chunks: list[Chunk], collection, embed: embeddings.Embed, cache_path: Path = EMBEDDINGS_FILE) -> AddResult:
    """Put the chunks of one document in the index, in place of whatever it had there.

    If every chunk is already stored unchanged, nothing is embedded or written.
    Otherwise only the texts without a saved vector are sent to `embed`, and the
    index is updated only once every chunk has its vector.
    """
    sources = {chunk.source for chunk in chunks}
    if len(sources) != 1:
        raise ValueError(f"index_document takes the chunks of exactly one document, not of {len(sources)}.")
    (source,) = sources
    stored = collection.get(where={"source": source}, include=["documents", "metadatas"])
    current = dict(zip(stored["ids"], zip(stored["documents"], stored["metadatas"])))
    wanted = {chunk_id: (text, metadata) for chunk_id, text, metadata in map(chunk_record, chunks)}
    unchanged = sum(current.get(chunk_id) == record for chunk_id, record in wanted.items())
    result = AddResult(source=source, chunks=len(current), added=0, removed=0, unchanged=unchanged, sent=0)
    if unchanged == len(wanted) == len(current):
        return result
    run = embeddings.embed_missing([embedded_text(chunk) for chunk in chunks], cache_path, embed)
    result.sent = run.sent
    if run.remaining:
        result.stopped = run.stopped
        return result
    store_chunks(collection, chunks, embeddings.load_cache(cache_path))
    result.added, result.removed, result.chunks = len(wanted) - unchanged, len(current) - unchanged, len(wanted)
    return result


def add_document(path: Path, collection, embed: embeddings.Embed, cache_path: Path = EMBEDDINGS_FILE) -> AddResult:
    """Run a PDF through the whole pipeline (extract, clean, split, chunk, heading, embed, store)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"There is no file at {path}.")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"{path.name} is not a PDF. Only PDF files can be added.")
    articles, _ = process(document_for(path.name), path)
    chunks = [chunk for article in articles for chunk in chunk_article(article, CHUNK_LIMIT)]
    return index_document(chunks, collection, embed, cache_path)


# ---------------------------------------------------------------------------
# The stage
# ---------------------------------------------------------------------------


def fetch_url(url: str) -> bytes:
    response = httpx.get(url, follow_redirects=True, timeout=180)
    response.raise_for_status()
    return response.content


def ensure_corpus(folder: Path = CORPUS_DIR, fetch: Callable[[str], bytes] = fetch_url) -> None:
    """Download into `folder` every corpus PDF that is not there yet."""
    folder.mkdir(parents=True, exist_ok=True)
    for document in DOCUMENTS.values():
        path = folder / document.filename
        if path.exists():
            continue
        print(f"Downloading {document.filename} ...", flush=True)
        content = fetch(document.url)
        if not content.startswith(b"%PDF"):
            raise ValueError(f"What {document.url} returned is not a PDF, so {document.filename} was not saved.")
        path.write_bytes(content)


def rule_names(document: Document) -> list[str]:
    """Every removal rule that applies to this document, in the order they are tried."""
    names = [name for name, _ in document.headers]
    if document.page_number_after:
        names.append(RULE_PAGE_NUMBER_AFTER_PAG)
    return names + [
        RULE_PAGE_NUMBER,
        RULE_PAGE_NUMBER_STRAY,
        RULE_STRAY_CHARACTER,
        RULE_ONLY_PLACEHOLDERS,
        RULE_HEADING_JUNK,
    ]


def process(document: Document, path: Path) -> tuple[list[Article], dict]:
    """Extract, clean and split one PDF. Returns its articles and a report of what was done."""
    pages = document.extract(path)
    cleaned = clean_pages(document, pages)
    split = split_articles(document, apply_fixes(document, cleaned.lines))
    check_numbering(split.articles)
    report = {
        "extraction": document.extract.__name__,
        "pages": len(pages),
        "lines_extracted": sum(1 for page in pages for line in page.splitlines() if line.strip()),
        "lines_removed": dict.fromkeys(rule_names(document), 0) | dict(cleaned.removed + split.removed),
        "glyph_placeholders_deleted": cleaned.placeholders,
        "heading_name_tokens_deleted": split.heading_tokens_deleted,
        "hand_fixes": [list(fix) for fix in document.fixes],
        "preamble_words": split.preamble_words,
        "closing_words": split.closing_words,
        "articles": len(split.articles),
        "article_words": sum(article.words for article in split.articles),
    }
    return split.articles, report


def main() -> None:
    ensure_corpus()
    articles, report = [], {}
    for document in DOCUMENTS.values():
        print(f"Extracting and cleaning {document.filename} ...", flush=True)
        document_articles, report[document.filename] = process(document, CORPUS_DIR / document.filename)
        articles += document_articles

    INDEX_DIR.mkdir(exist_ok=True)
    with ARTICLES_FILE.open("w", encoding="utf-8") as file:
        for article in articles:
            file.write(json.dumps(asdict(article), ensure_ascii=False) + "\n")
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for filename, entry in report.items():
        print(
            f"{filename}: {entry['articles']} articles, {entry['article_words']:,} words, "
            f"{sum(entry['lines_removed'].values())} of {entry['lines_extracted']} lines removed"
        )
    print(f"Wrote {ARTICLES_FILE.relative_to(ROOT)} and {REPORT_FILE.relative_to(ROOT)}")

    chunks = initial_chunks(articles)
    left_out = ", ".join(document.filename for document in DOCUMENTS.values() if not document.in_initial_index)
    print(f"{len(chunks):,} chunks of at most {CHUNK_LIMIT} words (left out: {left_out})", flush=True)
    run = embeddings.embed_missing(
        [embedded_text(chunk) for chunk in chunks], EMBEDDINGS_FILE, embeddings.gemini_embedder()
    )
    print(
        f"Embeddings ({embeddings.MODEL}, {embeddings.DIMENSION} values): {run.sent:,} texts sent to the API in "
        f"this run, {run.saved:,} saved in {EMBEDDINGS_FILE.relative_to(ROOT)}, {run.remaining:,} remaining"
    )
    if run.remaining:
        # Not an error exit: main.py would turn that into a traceback, and nothing is lost.
        print(
            f"STOPPED BEFORE THE END: {run.stopped}\n"
            f"{run.saved:,} texts have a saved vector and {run.remaining:,} do not. Run "
            f"`uv run python main.py index` again and only those {run.remaining:,} are sent. "
            f"{CHROMA_DIR.relative_to(ROOT)}/ was not updated."
        )
        return
    collection = open_collection(create=True)
    written, deleted = store_chunks(collection, chunks, embeddings.load_cache(EMBEDDINGS_FILE))
    print(
        f"{CHROMA_DIR.relative_to(ROOT)}/: {written:,} chunks written, {deleted:,} deleted, "
        f"{collection.count():,} stored"
    )


if __name__ == "__main__":
    main()
