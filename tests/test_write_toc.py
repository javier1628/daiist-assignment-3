"""The table of contents written for finding articles (scripts/write_toc.py)."""

import pytest

from index import Article
from write_toc import defined_terms, render

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
    assert headings == [
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
