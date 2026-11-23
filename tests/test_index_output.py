"""Checks on index/articles.jsonl, the file `main.py index` writes from the real PDFs."""

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from index import Article, chunk_article, split_pieces

ARTICLES_FILE = Path(__file__).resolve().parent.parent / "index" / "articles.jsonl"
LIMITS = (200, 300, 400, 500)  # the chunk sizes of the dry run in CORPUS.md
FURNITURE ={"CONGRESO NACIONAL", "PAG.", "LUIS ABINADER", "PRESIDENTE DE LA REPÚBLICA DOMINICANA", "PRESIDENTE DE LA REPUBLICA DOMINICANA"}
AMOUNT = re.compile(r"(?:RD|US)\$ [\d,]+\.\d\d$")


@pytest.fixture(scope="module")
def articles() -> list[dict]:
    with ARTICLES_FILE.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def of(articles: list[dict], source: str) -> list[dict]:
    return [article for article in articles if article["source"] == source]


@pytest.mark.parametrize(
    ("source", "count"),
    [("ley-168-21.pdf", 420), ("decreto-755-22.pdf", 318), ("decreto-609-24.pdf", 64), ("norma-01-2023.pdf", 4)],
)
def test_every_article_number_appears_exactly_once_and_in_order(articles, source, count):
    assert [article["number"] for article in of(articles, source)] == list(range(1, count + 1))


def test_every_record_has_the_agreed_fields(articles):
    for article in articles:
        assert set(article) == {"source", "number", "title", "titulo", "capitulo", "seccion", "page", "words", "text"}
        assert article["words"] == len(article["text"].split()) > 0
        assert article["page"] >= 1


def test_only_one_text_layer_of_decreto_755_survives(articles):
    second = of(articles, "decreto-755-22.pdf")[1]

    assert second["text"].count("Ámbito de aplicación") == 1
    assert sum(article["words"] for article in of(articles, "decreto-755-22.pdf")) < 60_000


def test_decreto_609_words_are_no_longer_fused(articles):
    text = "\n".join(article["text"] for article in of(articles, "decreto-609-24.pdf"))

    assert "PÁRRAFO IV. En cualquier transferencia, ya sea directa o indirecta, y siempre que ésta sea" in text
    assert "14) Copia del contrato de alquiler donde estará localizada la oficina o copia del certificado" in text
    assert "cualquiertransferencia" not in text


def test_articulo_22_9_of_the_law_is_now_229(articles):
    by_number = {article["number"]: article for article in of(articles, "ley-168-21.pdf")}

    assert by_number[229]["title"] == "Verificación, aforo o inspección documental"
    assert by_number[229]["text"].startswith("Artículo 229.- Verificación, aforo o inspección documental.")
    assert by_number[22]["title"] == "Atribuciones de los oficiales de Aduanas"


def test_no_page_furniture_or_single_characters_are_left_in_any_article(articles):
    lines = Counter(line for article in articles for line in article["text"].splitlines())

    assert not FURNITURE & set(lines)
    assert not [line for line in lines if len(line) == 1]


def test_articles_carry_the_headings_they_sit_under(articles):
    ley = {article["number"]: article for article in of(articles, "ley-168-21.pdf")}
    decreto = {article["number"]: article for article in of(articles, "decreto-609-24.pdf")}

    assert ley[1]["titulo"] == "TÍTULO I: DEL OBJETO, OBJETIVOS, ÁMBITO DE APLICACIÓN Y DEFINICIONES"
    assert ley[5]["titulo"] == "TÍTULO II: DE ADUANAS Y EL CONTROL ADUANERO"
    assert ley[5]["capitulo"] == "CAPÍTULO I: DEL TERRITORIO ADUANERO"
    assert decreto[1]["capitulo"] == "CAPÍTULO I: DISPOSICIONES GENERALES"
    assert decreto[1]["seccion"] == "SECCIÓN I: OBJETO Y ÁMBITO DE APLICACIÓN"


def test_the_fee_table_of_the_norma_keeps_its_149_rows_one_per_line(articles):
    first = of(articles, "norma-01-2023.pdf")[0]
    lines = first["text"].splitlines()

    assert sum(1 for line in lines if AMOUNT.search(line)) == 149
    assert "ADQUISICIÓN CERTIFICADO DIGITAL RD$ 4,000.00" in lines
    assert not [line for line in lines if line.isdigit()]


def test_closing_formulas_and_signatures_are_not_part_of_the_last_article(articles):
    for source in ("ley-168-21.pdf", "decreto-755-22.pdf", "decreto-609-24.pdf", "norma-01-2023.pdf"):
        last = of(articles, source)[-1]
        assert not re.search(r"(?im)^dad[ao] en\b", last["text"]), source


def test_the_fourteen_titulos_of_the_law_appear_in_order(articles):
    seen = []
    for article in of(articles, "ley-168-21.pdf"):
        label = article["titulo"].split(":")[0]
        if not seen or seen[-1] != label:
            seen.append(label)

    assert seen == [
        "TÍTULO I", "TÍTULO II", "TÍTULO III", "TÍTULO IV", "TÍTULO V", "TÍTULO VI", "TÍTULO VII",
        "TÍTULO VIII", "TÍTULO IX", "TÍTULO X", "TÍTULO XI", "TÍTULO XII", "TÍTULO XIII", "TÍTULO XIV",
    ]


@pytest.mark.parametrize("limit", LIMITS)
def test_the_chunks_of_every_article_rejoin_into_the_article_and_keep_its_fields(articles, limit):
    for record in articles:
        chunks = chunk_article(Article(**record), limit)

        assert "\n".join(chunk.text for chunk in chunks) == record["text"]
        for part, chunk in enumerate(chunks, 1):
            assert chunk.part == part
            assert chunk.words == len(chunk.text.split())
            for name in ("source", "number", "title", "titulo", "capitulo", "seccion"):
                assert getattr(chunk, name) == record[name]


@pytest.mark.parametrize("limit", LIMITS)
def test_article_4_of_the_law_gives_one_chunk_for_each_of_its_89_definitions(articles, limit):
    definiciones = next(article for article in of(articles, "ley-168-21.pdf") if article["number"] == 4)

    chunks = chunk_article(Article(**definiciones), limit)

    assert len(chunks) == 89
    assert chunks[0].text.startswith("Artículo 4.- Definiciones.")
    assert "\n1) Abandono de hecho:" in chunks[0].text
    assert [chunk.text.split(")")[0] for chunk in chunks[1:]] == [str(number) for number in range(2, 90)]


@pytest.mark.parametrize("limit", LIMITS)
def test_a_chunk_over_the_limit_is_a_single_piece_with_nowhere_to_cut(articles, limit):
    for record in articles:
        for chunk in chunk_article(Article(**record), limit):
            if chunk.words > limit:
                assert split_pieces(chunk.text) == [chunk.text]
