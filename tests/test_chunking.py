"""The chunking rule. Inputs are short texts modelled on the corpus, so every word count can be checked by hand."""

import pytest

from index import Article, chunk_article, split_pieces

OPENING = "Artículo 10.- Plazo. El plazo es de treinta días."  # 9 words
PARRAFO_I = "Párrafo I.- El plazo puede prorrogarse una vez."  # 8 words
PARRAFO_II = "Párrafo II.- La prórroga se solicita por escrito."  # 8 words
PARRAFO_III = "Párrafo III.- No hay segunda prórroga."  # 6 words

DEFINICIONES = (
    "Artículo 4.- Definiciones. Para los fines de la presente ley, los",  # 11 words
    "términos que se indican tienen los siguientes significados:",  # 8
    "1) Bulto: Mercancía o unidad utilizada para contener ésta.",  # 9
    "2) Buque: Comprende toda embarcación de cinco o más toneladas",  # 10
    "brutas.",  # 1
    "3) Gravamen: Es un derecho de Aduanas de aplicación general.",  # 10
)


def article(*lines: str, source: str = "decreto-755-22.pdf", number: int = 10) -> Article:
    text = "\n".join(lines)
    return Article(
        source=source,
        number=number,
        title="Plazo",
        titulo="TÍTULO II: DE ADUANAS Y EL CONTROL ADUANERO",
        capitulo="CAPÍTULO I: DEL TERRITORIO ADUANERO",
        seccion="SECCIÓN I: OBJETO",
        page=7,
        words=len(text.split()),
        text=text,
    )


def test_an_article_at_the_limit_is_one_chunk_with_its_text_unchanged():
    whole = article(OPENING, PARRAFO_I, PARRAFO_II, PARRAFO_III)  # 31 words

    chunks = chunk_article(whole, 31)

    assert [chunk.text for chunk in chunks] == [whole.text]
    assert chunks[0].words == 31


def test_an_article_over_the_limit_is_cut_at_parrafos_and_packed_up_to_the_limit():
    chunks = chunk_article(article(OPENING, PARRAFO_I, PARRAFO_II, PARRAFO_III), 30)

    assert [chunk.text for chunk in chunks] == [
        "\n".join([OPENING, PARRAFO_I, PARRAFO_II]),
        PARRAFO_III,
    ]
    assert [chunk.words for chunk in chunks] == [25, 6]


def test_packing_fills_a_chunk_exactly_to_the_limit_and_no_further():
    chunks = chunk_article(article(OPENING, PARRAFO_I, PARRAFO_II, PARRAFO_III), 17)

    assert [chunk.words for chunk in chunks] == [17, 14]


def test_numbered_items_are_boundaries_and_keep_their_continuation_lines():
    chunks = chunk_article(
        article(
            "Artículo 8.- Requisitos. El solicitante debe:",  # 6 words
            "1) Presentar copia de su cédula.",  # 6
            "2) Completar el formulario destinado a estos fines",  # 8
            "por la DGA.",  # 3, the rest of item 2
            "3) Pagar la tasa.",  # 4
        ),
        12,
    )

    assert [chunk.text for chunk in chunks] == [
        "Artículo 8.- Requisitos. El solicitante debe:\n1) Presentar copia de su cédula.",
        "2) Completar el formulario destinado a estos fines\npor la DGA.",
        "3) Pagar la tasa.",
    ]


def test_a_piece_with_no_boundary_inside_stays_whole_even_over_the_limit():
    long_parrafo = "Párrafo II.- Este párrafo es largo y no tiene dónde cortarse en absoluto."  # 13 words
    chunks = chunk_article(
        article(
            "Artículo 12.- Alcance. Esta disposición rige en todo el territorio.",  # 10 words
            "Párrafo I.- Breve.",  # 3
            long_parrafo,
            "Párrafo III.- Corto.",  # 3
        ),
        12,
    )

    assert [chunk.words for chunk in chunks] == [10, 3, 13, 3]
    assert chunks[2].text == long_parrafo


def test_an_article_over_the_limit_with_no_boundary_is_one_chunk():
    whole = article(
        "Artículo 12.- Alcance. Esta disposición rige en todo el territorio",
        "nacional sin excepción alguna.",
    )

    chunks = chunk_article(whole, 5)

    assert [chunk.text for chunk in chunks] == [whole.text]


def test_every_chunk_keeps_the_source_number_title_and_heading_path_of_its_article():
    chunks = chunk_article(article(OPENING, PARRAFO_I, PARRAFO_II, PARRAFO_III), 17)

    assert len(chunks) == 2
    for part, chunk in enumerate(chunks, 1):
        assert (chunk.source, chunk.number, chunk.title) == ("decreto-755-22.pdf", 10, "Plazo")
        assert (chunk.titulo, chunk.capitulo, chunk.seccion) == (
            "TÍTULO II: DE ADUANAS Y EL CONTROL ADUANERO",
            "CAPÍTULO I: DEL TERRITORIO ADUANERO",
            "SECCIÓN I: OBJETO",
        )
        assert chunk.part == part


@pytest.mark.parametrize("limit", [5, 12, 17, 30, 31])
def test_no_text_is_lost_or_repeated_when_an_article_is_cut(limit):
    whole = article(OPENING, PARRAFO_I, PARRAFO_II, PARRAFO_III)

    chunks = chunk_article(whole, limit)

    assert "\n".join(chunk.text for chunk in chunks) == whole.text
    assert sum(chunk.words for chunk in chunks) == 31


@pytest.mark.parametrize(
    "line",
    [
        "Párrafo I.- La DGA podrá requerir información adicional.",
        "Párrafo: La metodología se establecerá mediante reglamento.",
        "Párrafo.- Lo anterior no aplica a las zonas francas.",
        "PÁRRAFO II. Los operadores deberán renovar su licencia.",
        "PÁRRAFO. La solicitud se hará en línea.",
        "PARRAFO 11. La Administración aduanera designará una comisión.",  # the OCR's reading of PÁRRAFO II
        "1) Intercambiar información de forma automática.",
        "1)Facilitar y agilizar las operaciones de comercio exterior;",
        "14) Desaduanamiento de los envíos expresos.",
        "4. Caso fortuito o fuerza mayor.",
    ],
)
def test_a_line_that_opens_a_parrafo_or_a_numbered_item_starts_a_new_piece(line):
    assert split_pieces(f"{OPENING}\n{line}") == [OPENING, line]


@pytest.mark.parametrize(
    "line",
    [
        "párrafo anterior, la DGA otorgará o rechazará la solicitud.",  # a cross-reference wrapped onto a new line
        "a) La Dirección General de Aduanas (DGA), que lo coordinará.",  # lettered item
        "ii. En el marco del desarrollo de una de las operaciones.",
        "9)",  # stamp debris: a marker with no text
        "3.",
        "30 días a partir de la recepción de la comunicación.",
        "168-21, de Aduanas de la República Dominicana.",
        "2018. Que establece los procedimientos y requisitos.",  # a year wrapped onto a new line
    ],
)
def test_any_other_line_stays_in_the_piece_before_it(line):
    assert split_pieces(f"{OPENING}\n{line}") == [f"{OPENING}\n{line}"]


@pytest.mark.parametrize("limit", [20, 500])
def test_article_4_of_the_law_is_one_definition_per_chunk_whatever_the_limit(limit):
    definiciones = article(*DEFINICIONES, source="ley-168-21.pdf", number=4)  # 49 words

    chunks = chunk_article(definiciones, limit)

    assert [chunk.text for chunk in chunks] == [
        "\n".join(DEFINICIONES[:3]),  # the opening sentence goes with the first definition
        "\n".join(DEFINICIONES[3:5]),
        DEFINICIONES[5],
    ]
    assert [chunk.words for chunk in chunks] == [28, 11, 10]


@pytest.mark.parametrize(("source", "number"), [("ley-168-21.pdf", 5), ("decreto-755-22.pdf", 4)])
def test_only_article_4_of_the_law_is_cut_one_item_per_chunk(source, number):
    same_text = article(*DEFINICIONES, source=source, number=number)

    assert len(chunk_article(same_text, 500)) == 1


def test_an_article_set_to_one_item_per_chunk_that_has_no_items_is_an_error():
    without_items = article(OPENING, source="ley-168-21.pdf", number=4)

    with pytest.raises(ValueError, match="article 4"):
        chunk_article(without_items, 500)
