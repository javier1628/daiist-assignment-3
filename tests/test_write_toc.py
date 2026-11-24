"""The table of contents written for finding articles (scripts/write_toc.py)."""

import pytest

from index import Article
from write_toc import defined_terms, deferrals, law_citations, render

TITULO = "TÍTULO I: DEL OBJETO"
CAPITULO = "CAPÍTULO I: DEL TERRITORIO ADUANERO"


def article(number: int, text: str, source: str = "ley-168-21.pdf", **fields) -> Article:
    values = dict(title="", titulo="", capitulo="", seccion="", page=number + 6)
    return Article(source=source, number=number, words=len(text.split()), text=text, **(values | fields))


DEFINICIONES = article(
    4,
    "Artículo 4.- Definiciones. Los términos tienen los siguientes significados:\n"
    "1) Bulto: Mercancía o unidad utilizada para contener ésta.\n"
    "2) Admisión temporal para perfeccionamiento\n"
    "activo: La Admisión Temporal es el régimen: uno de varios.\n"
    '3) Términos de Comercio Internacional o "INCOTERMS": Son reglas.',
    title="Definiciones",
    titulo=TITULO,
)


def test_the_defined_terms_are_what_stands_before_the_first_colon_of_each_item():
    assert defined_terms(DEFINICIONES) == [
        "Bulto",
        "Admisión temporal para perfeccionamiento activo",
        'Términos de Comercio Internacional o "INCOTERMS"',
    ]


def test_an_item_without_a_colon_is_an_error():
    broken = article(4, "Artículo 4.- Definiciones. Significados:\n1) Bulto es una unidad.", title="Definiciones")

    with pytest.raises(ValueError, match="Bulto es una unidad"):
        defined_terms(broken)


def test_each_document_is_a_tree_of_headings_with_one_row_per_article():
    lines = render([
        article(1, "Artículo 1.- Objeto. Regular el régimen.", title="Objeto", titulo=TITULO),
        DEFINICIONES,
        article(5, "Artículo 5.- Los plazos se cuentan en días hábiles.", titulo="TÍTULO II: DE ADUANAS", capitulo=CAPITULO),
        article(6, "Artículo 6.- Zona. La zona primaria.", title="Zona", titulo="TÍTULO II: DE ADUANAS", capitulo=CAPITULO),
        article(1, "ARTÍCULO 1. Objeto. Regular a los operadores.", source="decreto-609-24.pdf", title="Objeto", capitulo="CAPÍTULO I: DISPOSICIONES GENERALES"),
    ])
    text = "\n".join(lines)

    headings = [line for line in lines if line.startswith("#")]
    tree = headings[: headings.index("## Cross-references between the law and its reglamentos")]
    assert tree == [
        "# Table of contents of the indexed documents",
        "## Ley 168-21 de Aduanas (`ley-168-21.pdf`)",
        f"### {TITULO}",
        "### TÍTULO II: DE ADUANAS",
        f"#### {CAPITULO}",
        "## Decreto 609-24, Reglamento de aplicación del Título III de la Ley 168-21 de Aduanas (`decreto-609-24.pdf`)",
        "#### CAPÍTULO I: DISPOSICIONES GENERALES",
    ]
    assert "| 1 | Objeto | 7 | 6 |" in lines
    assert "| 4 | Definiciones — **3 definitions**, listed below | 10 | 42 |" in lines
    assert '| 5 | *(no title; starts: "Los plazos se cuentan en días hábiles.")* | 11 | 9 |' in lines
    assert "1. Bulto\n2. Admisión temporal para perfeccionamiento activo\n3. Términos de Comercio" in text
    assert "norma-01-2023" not in text  # only the documents of the initial index


# --- cross-references between the law and its reglamentos --------------------


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("Los depósitos pagarán la tasa que establezca el reglamento de la presente ley.", "specific"),
        ("Los requisitos serán establecidos mediante reglamento.", "specific"),
        ("Las condiciones se fijarán reglamentariamente.", "specific"),
        ("previstos en esta ley, conforme al reglamento.", "specific"),
        ("conforme a lo dispuesto en esta ley y su reglamento.", "general"),
        ("las disposiciones de esta ley y sus cr reglamentos.", "general"),  # with OCR debris in between
        ("cumplir las formalidades legales y reglamentarias.", "general"),
        ("los procedimientos establecidos en esta ley, su reglamento o leyes especiales.", "general"),
        ("las sanciones prescritas en la misma y su reglamento de aplicación;", "general"),
        ("la Dirección General de Aduanas y sus reglamentos de administración interna.", "general"),
        ("la mercancía y su procedimiento se establecerá mediante reglamento.", "specific"),
    ],
)
def test_a_mention_of_the_reglamento_is_specific_unless_it_is_the_formula_this_law_and_its_reglamento(text, kind):
    found = deferrals(text)

    assert [found_kind for found_kind, _ in found] == [kind]
    assert "reglament" in found[0][1].lower()


def test_an_article_that_never_mentions_the_reglamento_defers_nothing():
    assert deferrals("El territorio aduanero es todo el territorio nacional.") == []


@pytest.mark.parametrize(
    ("text", "cited"),
    [
        ("el plazo señalado en el articulo 101 de la Ley de Aduanas, el sujeto pasivo", [101]),
        ("previsto por los artículos 168, 169 y 170 de la Leynúm. 168-21. 2) No podrán", [168, 169, 170]),
        ("lo establecido en el artículo 328, numeral 2, de la Ley de Aduanas", [328]),
        ("en los artículos 25, 26 y el párrafo II del articulo 28 de la Ley núm. 168-21", [25, 26, 28]),
        ("establecido en el articulo 123 y siguientes de la Ley núm. 168-21, las mercancías", [123]),
        ("los regímenes de los artículos 264 al 266 de la Ley", [264, 265, 266]),
        ("las obligaciones del artíeulo 188 delaLeynúm. 168-21", [188]),  # as the OCR reads it
        ("las señaladas en el artículo 183 de dicha ley, y las previstas en el artículo 185 de la misma.", [183, 185]),
        ("el numeral 3 del artículo 112 de la Ley núm. 168-21. En el numeral 2 del articulo 112, es abandono", [112]),
        ("las sanciones aplicables en el artículo 374 por concepto de declaración tardía", [374]),  # the decree has no 374
        ("conforme al artículo 20 de la Ley núm. 107-13, sobre los derechos de las personas", []),  # another law
        ("los requisitos señalados en el articulo 166 del presente Reglamento, la Administración", []),
        ("Artículos 3, 4, 6, 8, 9 y 18 del Decreto núm. 106-96, del 25 de marzo de 1996", []),
        ("las instituciones señaladas en el artículo 304, deberá elaborar un protocolo", []),  # its own article
    ],
)
def test_citations_of_numbered_articles_of_the_law_are_found_and_others_left_out(text, cited):
    assert law_citations(text, own_articles=318) == cited


def test_the_cross_reference_tables_pair_a_law_article_with_the_reglamento_article_that_cites_it():
    lines = render([
        article(88, "Artículo 88.- Trato preferencial. Se aplicará en las condiciones que establezca el reglamento.",
                title="Trato preferencial", titulo=TITULO),
        article(90, "Artículo 90.- Pago. Se hará conforme a esta ley y su reglamento.", title="Pago", titulo=TITULO),
        article(70, "ARTÍCULO 70. Origen. El trato establecido en el artículo 88 de la Ley núm. 168-21 se determina así.",
                source="decreto-755-22.pdf", title="Origen", capitulo="CAPÍTULO V: DEL ORIGEN"),
    ])
    text = "\n".join(lines)

    assert "## Cross-references between the law and its reglamentos" in lines
    assert "| 88 ★ | Trato preferencial | 94 | Decreto 755-22 art. 70 | Origen | 76 |" in lines
    assert "| 88 | Trato preferencial | 94 | ... en las condiciones que establezca el reglamento. | Decreto 755-22 art. 70 |" in lines
    assert "| 90 | Pago | 96 | ... conforme a esta ley y su reglamento. |" in lines
    assert text.index("Specific deferrals (1)") < text.index("General formula only (1)")
