"""Page-furniture rules and hand fixes. Inputs are modelled on the real PDFs; most lines are copied from them."""

import pytest

from index import DOCUMENTS, apply_fixes, clean_pages

LEY = DOCUMENTS["ley-168-21.pdf"]
DECRETO_755 = DOCUMENTS["decreto-755-22.pdf"]
DECRETO_609 = DOCUMENTS["decreto-609-24.pdf"]
NORMA = DOCUMENTS["norma-01-2023.pdf"]


def page(*lines: str) -> str:
    return "\n".join(lines)


def test_ley_header_block_and_garbled_page_number_are_removed():
    cleaned = clean_pages(LEY, [page(
        "CONGRESO NACIONAL",
        "ASUNTO: Ley de Aduanas de la República Dominicana.",
        "PAG.",
        "4-06-",
        "Párrafo: La metodología para la estimación de averías se establecerá",
        "mediante reglamento.",
    )])

    assert cleaned.lines == [
        (1, "Párrafo: La metodología para la estimación de averías se establecerá"),
        (1, "mediante reglamento."),
    ]
    assert cleaned.removed == {
        "header: CONGRESO NACIONAL": 1,
        "header: ASUNTO: Ley de Aduanas de la República Dominicana.": 1,
        "header: PAG.": 1,
        "page number after PAG.": 1,
    }


def test_ley_header_misread_by_ocr_is_still_removed():
    cleaned = clean_pages(LEY, [page(
        "ONGRESO NACIONAL",
        "AbUNIU. Lgy de Aduanas de la República Dominicana.",
        "PAG. fi9",
        "Artículo 5.- Territorio aduanero. El territorio aduanero es todo el",
    )])

    assert cleaned.lines == [(1, "Artículo 5.- Territorio aduanero. El territorio aduanero es todo el")]
    assert cleaned.removed == {
        "header: CONGRESO NACIONAL": 1,
        "header: ASUNTO: Ley de Aduanas de la República Dominicana.": 1,
        "header: PAG.": 1,
    }


def test_ley_header_split_over_two_lines_is_removed():
    cleaned = clean_pages(LEY, [page(
        "CONGRESO NACIONAL",
        "ASUNTO:",
        "Ley de Aduanas de la República Dominicana.",
        "PAG. 230",
        "Dada en la Sala de Sesiones de la Cámara de Diputados, Palacio del",
    )])

    assert cleaned.lines == [(1, "Dada en la Sala de Sesiones de la Cámara de Diputados, Palacio del")]
    assert cleaned.removed["header: ASUNTO: Ley de Aduanas de la República Dominicana."] == 2


def test_short_real_line_after_pag_is_kept():
    cleaned = clean_pages(LEY, [page(
        "CONGRESO NACIONAL",
        "ASUNTO: Ley de Aduanas de la República Dominicana.",
        "PAG.",
        "ley.",
        "Artículo 6.- Zona de jurisdicción aduanera. La zona de jurisdicción",
    )])

    assert cleaned.lines == [
        (1, "ley."),
        (1, "Artículo 6.- Zona de jurisdicción aduanera. La zona de jurisdicción"),
    ]
    assert "page number after PAG." not in cleaned.removed


def test_header_wording_in_the_body_of_a_page_is_kept():
    body = [f"línea {n} del cuerpo de la página con texto corriente" for n in range(1, 7)]
    cleaned = clean_pages(LEY, [page(*body, "CONGRESO NACIONAL", "PAG.")])

    assert [text for _, text in cleaned.lines][-2:] == ["CONGRESO NACIONAL", "PAG."]
    assert cleaned.removed == {}


def test_decree_letterhead_is_removed_with_or_without_the_accent():
    cleaned = clean_pages(DECRETO_755, [
        page("LUIS ABINADER", "PRESIDENTE DE LA REPUBLICA DOMINICANA", "b) Nivel comercial de importador, mayorista o minorista."),
        page("LUIS ABINADER", "PRESIDENTE DE LA REPÚBLICA DOMINICANA", "c) Condiciones de la venta."),
    ])

    assert cleaned.lines == [
        (1, "b) Nivel comercial de importador, mayorista o minorista."),
        (2, "c) Condiciones de la venta."),
    ]
    assert cleaned.removed == {
        "header: LUIS ABINADER": 2,
        "header: PRESIDENTE DE LA REPÚBLICA DOMINICANA": 2,
    }


def test_only_the_number_of_the_page_itself_counts_as_a_page_number():
    second_page = page("texto de la segunda página que sigue al anterior", "15", "2")
    cleaned = clean_pages(DECRETO_755, ["primera página con texto corriente", second_page])

    assert cleaned.lines == [
        (1, "primera página con texto corriente"),
        (2, "texto de la segunda página que sigue al anterior"),
        (2, "15"),
    ]
    assert cleaned.removed == {"page number": 1}


def test_page_number_with_one_stray_character_is_removed():
    second_page = page("PÁRRAFO II. Los operadores aduaneros que hayan solicitado", "t  2", "de 2")
    cleaned = clean_pages(DECRETO_755, ["primera página con texto corriente", second_page])

    assert cleaned.lines == [
        (1, "primera página con texto corriente"),
        (2, "PÁRRAFO II. Los operadores aduaneros que hayan solicitado"),
        (2, "de 2"),
    ]
    assert cleaned.removed == {"page number with a stray character": 1}


def test_single_stray_characters_are_removed_and_longer_lines_kept():
    cleaned = clean_pages(DECRETO_609, [page(
        "i",
        "^",
        "3",
        "rm",
        "a) Certificación de la Dirección General de Impuestos Internos.",
        "y,",
    )])

    assert cleaned.lines == [
        (1, "rm"),
        (1, "a) Certificación de la Dirección General de Impuestos Internos."),
        (1, "y,"),
    ]
    assert cleaned.removed == {"single stray character": 3}


def test_glyph_placeholders_are_deleted_without_losing_the_line():
    cleaned = clean_pages(LEY, [page(
        "propias del servicio de Aduanas y a las disposiciones establecidas en(cid:127)",
        "(cid:127)(cid:127)",
        "esta ley y sus reglamentos.",
    )])

    assert cleaned.lines == [
        (1, "propias del servicio de Aduanas y a las disposiciones establecidas en"),
        (1, "esta ley y sus reglamentos."),
    ]
    assert cleaned.placeholders == 3
    assert cleaned.removed == {"only glyph placeholders": 1}


def test_fee_table_rows_pass_through_untouched_and_the_page_number_between_them_goes():
    rows_page_1 = [
        "NOMBRE DE SERVICIO MONEDA COSTO",
        "ADQUISICIÓN CERTIFICADO DIGITAL RD$ 4,000.00",
        "CIRCULACION DE MERCANCÍA (EUR 1) // GOODS CIRCULATION (1 EURO) RD$ 450.00",
        "CUSTODIA TRÁNSITO DE MERCANCÍAS CON DISTANCIA DE 101-150 KM RD$ 1,365.00",
    ]
    rows_page_2 = [
        "CUSTODIA TRÁNSITO DE MERCANCÍAS CON DISTANCIA DE 151-200 KM RD$ 1,755.00",
        "CUSTODIO ESPECIAL-12 HORAS RD$ 2,580.00",
    ]
    cleaned = clean_pages(NORMA, [page(*rows_page_1, "1"), page(*rows_page_2, "2")])

    assert [text for _, text in cleaned.lines] == rows_page_1 + rows_page_2
    assert cleaned.removed == {"page number": 2}


def test_blank_lines_and_edge_spaces_are_dropped_without_counting_as_a_rule():
    cleaned = clean_pages(DECRETO_609, ["  ARTÍCULO 1. Objeto. El presente Reglamento tiene por objeto  \n\n   \nregular"])

    assert cleaned.lines == [
        (1, "ARTÍCULO 1. Objeto. El presente Reglamento tiene por objeto"),
        (1, "regular"),
    ]
    assert cleaned.removed == {}


def test_the_hand_fix_turns_articulo_22_9_into_229():
    lines = [
        (140, "Artículo 228.- Verificación, aforo o inspección inmediata. La"),
        (140, "Artículo 22 9.- Verificación, aforo o inspección documental. La"),
    ]

    assert apply_fixes(LEY, lines) == [
        (140, "Artículo 228.- Verificación, aforo o inspección inmediata. La"),
        (140, "Artículo 229.- Verificación, aforo o inspección documental. La"),
    ]


def test_a_hand_fix_that_no_longer_matches_is_an_error_not_a_silent_skip():
    with pytest.raises(ValueError, match="Artículo 22 9"):
        apply_fixes(LEY, [(140, "Artículo 228.- Verificación, aforo o inspección inmediata. La")])


def test_documents_without_hand_fixes_come_back_unchanged():
    lines = [(3, "ARTÍCULO 1. Objeto. El presente Reglamento tiene por objeto regular")]

    assert apply_fixes(DECRETO_609, lines) == lines


@pytest.mark.parametrize(
    "header_lines",
    [
        ["CONGI L", "AbUNIO. Lgy ¿g Aduanas de la República Dominicana.", "PAG- 17C"],
        ["iSO NACIONAL", "AbUINlCJ. Ley de Aduanas de la República Dominicana.", "PAG- o.", "-1-8-7-"],
        ["CONGRÍ a í : ci AL", "ASUNTU. Ley dg Aduanas de la República Dominicana.", "PAG.", "??Q"],
        ['"1M NAL', "AbUNIU. Lgy <-je Aduanas de la República Dominicana.", "PAG- ,™"],
        ["CON U^/¡", "GRESO ONAL", "NAL"],
    ],
)
def test_badly_garbled_ley_headers_are_removed(header_lines):
    body = "Artículo 180.- Declaración de mercancías. La declaración de mercancías"

    cleaned = clean_pages(LEY, [page(*header_lines, body)])

    assert cleaned.lines == [(1, body)]


def test_real_lines_that_resemble_the_ley_header_are_kept():
    lines = [
        "EL CONGRESO NACIONAL",
        "EN NOMBRE DE LA REPÚBLICA",
        "comercio exterior de la República Dominicana.",
        "la Dirección General de Aduanas de la República Dominicana.",
        "CONTROL ADUANERO",
        "DERECHO PENAL",
    ]

    cleaned = clean_pages(LEY, [page(*lines)])

    assert [text for _, text in cleaned.lines] == lines
