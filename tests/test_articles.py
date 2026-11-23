"""Splitting cleaned lines into articles. Inputs are modelled on the real PDFs; most lines are copied from them."""

import pytest

from index import DOCUMENTS, check_numbering, split_articles, split_title

LEY = DOCUMENTS["ley-168-21.pdf"]
DECRETO_755 = DOCUMENTS["decreto-755-22.pdf"]
DECRETO_609 = DOCUMENTS["decreto-609-24.pdf"]
NORMA = DOCUMENTS["norma-01-2023.pdf"]


def on_page(page: int, *texts: str) -> list[tuple[int, str]]:
    return [(page, text) for text in texts]


LEY_START = on_page(
    6,
    "Vista: La Ley núm.8-90, de fecha 15 de enero de 1990, sobre el Fomento",
    "de Zonas Francas.",
) + on_page(
    7,
    "TITULO I",
    "DEL OBJETO, OBJETIVOS, ÁMBITO DE APLICACIÓN Y DEFINICIONES",
    "Artículo 1.- Objeto. Esta ley tiene por objeto regular lo relativo al",
    "régimen aduanero en la República Dominicana.",
) + on_page(
    28,
    "TITULO II",
    "DE ADUANAS Y EL CONTROL ADUANERO",
    "CAPÍTULO I",
    "DEL TERRITORIO ADUANERO",
    "Artículo 5.- Territorio aduanero. El territorio aduanero es todo el",
    "territorio nacional donde la legislación aduanera es plenamente",
) + on_page(
    29,
    "aplicable.",
)


def test_each_article_carries_its_number_title_page_words_and_text():
    first, second = split_articles(LEY, LEY_START).articles

    assert (first.source, first.number, first.title, first.page) == ("ley-168-21.pdf", 1, "Objeto", 7)
    assert first.text == (
        "Artículo 1.- Objeto. Esta ley tiene por objeto regular lo relativo al\n"
        "régimen aduanero en la República Dominicana."
    )
    assert first.words == 18
    assert (second.number, second.title, second.page) == (5, "Territorio aduanero", 28)
    assert second.text.endswith("plenamente\naplicable.")


def test_articles_know_the_titulo_and_capitulo_they_sit_under():
    first, second = split_articles(LEY, LEY_START).articles

    assert first.titulo == "TÍTULO I: DEL OBJETO, OBJETIVOS, ÁMBITO DE APLICACIÓN Y DEFINICIONES"
    assert (first.capitulo, first.seccion) == ("", "")
    assert second.titulo == "TÍTULO II: DE ADUANAS Y EL CONTROL ADUANERO"
    assert second.capitulo == "CAPÍTULO I: DEL TERRITORIO ADUANERO"
    assert second.seccion == ""


def test_heading_lines_are_not_left_inside_the_previous_article():
    first, _ = split_articles(LEY, LEY_START).articles

    assert "TITULO II" not in first.text
    assert "DEL TERRITORIO ADUANERO" not in first.text


def test_text_before_the_first_article_is_counted_as_preamble_and_kept_out():
    split = split_articles(LEY, LEY_START)

    assert split.preamble_words == 17
    assert all("Zonas Francas" not in article.text for article in split.articles)


def test_a_new_capitulo_clears_the_seccion_and_a_new_titulo_clears_both():
    lines = on_page(
        52,
        "TÍTULO III",
        "DE LAS PERSONAS VINCULADAS A LA ACTIVIDAD ADUANERA",
        "CAPITULO II",
        "DE LAS PERSONAS AUTORIZADAS PARA INTERVENIR ANTE LAS ADUANAS",
        "SECCIÓN I",
        "DE LAS PERSONAS AUTORIZADAS",
        "Artículo 35.- Personas autorizadas. Las personas autorizadas",
        "CAPITULO III",
        "DEL RÉGIMEN DE SUSPENSIÓN Y CANCELACIÓN DE LICENCIAS A LOS OPERADORES",
        "ADUANEROS",
        "Artículo 36.- Sanciones. La Dirección General de Aduanas podrá",
        "TÍTULO IV",
        "DE LA OBLIGACIÓN TRIBUTARIA ADUANERA",
        "Artículo 37.- Obligación tributaria aduanera. La obligación",
    )

    a35, a36, a37 = split_articles(LEY, lines).articles

    assert a35.seccion == "SECCIÓN I: DE LAS PERSONAS AUTORIZADAS"
    assert a36.capitulo == "CAPÍTULO III: DEL RÉGIMEN DE SUSPENSIÓN Y CANCELACIÓN DE LICENCIAS A LOS OPERADORES ADUANEROS"
    assert a36.seccion == ""
    assert a36.titulo == "TÍTULO III: DE LAS PERSONAS VINCULADAS A LA ACTIVIDAD ADUANERA"
    assert (a37.titulo, a37.capitulo, a37.seccion) == ("TÍTULO IV: DE LA OBLIGACIÓN TRIBUTARIA ADUANERA", "", "")


def test_headings_misread_by_ocr_are_recognised_and_spelled_the_standard_way():
    lines = on_page(
        39,
        "CAPITULO v",
        "DEL CONTROL ADUANERO",
        "Artículo 19.- Control aduanero. El control aduanero es el conjunto de",
        "SECCIÓN IV C/>",
        "DE LOS REQUISITOS PARA OTORGAMIENTO Y MANTENIMIENTO DE LICENCIA",
        "Artículo 43.- Validación. Los agentes y apoderados especiales de",
    )

    a19, a43 = split_articles(LEY, lines).articles

    assert a19.capitulo == "CAPÍTULO V: DEL CONTROL ADUANERO"
    assert a43.seccion == "SECCIÓN IV: DE LOS REQUISITOS PARA OTORGAMIENTO Y MANTENIMIENTO DE LICENCIA"


def test_a_titulo_with_a_stray_digit_or_a_misread_numeral_is_still_recognised():
    lines = on_page(
        98,
        "TÍTULO V 5",
        "DE LA ENTRADA Y SALIDA DE MEDIOS DE TRANSPORTE, MERCANCÍAS Y PERSONAS",
        "Artículo 137.- Ingreso o salida de personas, mercancías y medios de",
    ) + on_page(
        146,
        "TÍTULO Vil",
        "DE LOS REGÍMENES Y OPERACIONES ADUANERAS",
        "Artículo 240.- Regímenes aduaneros. Las mercancías que ingresen",
    )

    a137, a240 = split_articles(LEY, lines).articles

    assert a137.titulo == "TÍTULO V: DE LA ENTRADA Y SALIDA DE MEDIOS DE TRANSPORTE, MERCANCÍAS Y PERSONAS"
    assert a240.titulo == "TÍTULO VII: DE LOS REGÍMENES Y OPERACIONES ADUANERAS"


def test_seccion_unica_is_a_heading_even_without_a_roman_numeral():
    lines = on_page(
        220,
        "CAPÍTULO I",
        "DE LA FACILITACIÓN DEL COMERCIO",
        "Artículo 398.- Facilitación de intercambios comerciales del país. La",
        "comerciales del país.",
    ) + on_page(
        221,
        "SECCIÓN ÚNICA",
        "DEL COMITÉ NACIONAL DE FACILITACIÓN DEL COMERCIO (CNFC)",
        "Artículo 399.- Objeto y conformación (CNFC). Se crea el Comité",
    )

    a398, a399 = split_articles(LEY, lines).articles

    assert a398.text.endswith("comerciales del país.")
    assert a399.capitulo == "CAPÍTULO I: DE LA FACILITACIÓN DEL COMERCIO"
    assert a399.seccion == "SECCIÓN ÚNICA: DEL COMITÉ NACIONAL DE FACILITACIÓN DEL COMERCIO (CNFC)"


def test_mixed_case_seccion_of_the_decree_and_a_seccion_without_a_name():
    lines = on_page(
        12,
        "CAPITULO IV",
        "DE LA FISCALIZACIÓN ADUANERA Y EL PROCEDIMIENTO ADMINISTRATIVO",
        "DE FISCALIZACIÓN",
        "Sección I",
        "Disposiciones generales",
        "ARTÍCULO 27. Objeto y ámbito de aplicación. Este capítulo regula la potestad",
        "Sección II",
        "ARTÍCULO 69. Sobre la certificación previa a la orden de embargo. La certificación aduanera",
    )

    a27, a69 = split_articles(DECRETO_755, lines).articles

    assert a27.capitulo == "CAPÍTULO IV: DE LA FISCALIZACIÓN ADUANERA Y EL PROCEDIMIENTO ADMINISTRATIVO DE FISCALIZACIÓN"
    assert a27.seccion == "SECCIÓN I: Disposiciones generales"
    assert a69.seccion == "SECCIÓN II"


def test_a_sentence_that_merely_starts_with_capitulo_stays_in_the_article():
    lines = on_page(
        29,
        "ARTÍCULO 46. Los depositarios de mercancías deberán cumplir con lo dispuesto en el",
        "Capítulo III del presente Reglamento.",
        "ARTÍCULO 47. Las instalaciones deberán contar con las condiciones de seguridad",
    )

    a46, a47 = split_articles(DECRETO_609, lines).articles

    assert a46.text.endswith("Capítulo III del presente Reglamento.")
    assert a47.capitulo == ""


def test_a_junk_line_between_a_heading_and_its_name_is_dropped_and_counted():
    lines = on_page(
        34,
        "CAPÍTULO IV",
        "V.",
        "DE LA POTESTAD Y ATRIBUCIONES ADUANERAS",
        "Artículo 17.- Potestad aduanera. La potestad aduanera es el conjunto",
    )

    split = split_articles(LEY, lines)

    assert split.articles[0].capitulo == "CAPÍTULO IV: DE LA POTESTAD Y ATRIBUCIONES ADUANERAS"
    assert split.removed == {"junk line inside a heading name": 1}


def test_ocr_debris_is_stripped_from_heading_names_written_in_capitals():
    lines = on_page(
        64,
        "SECCIÓN X",
        "DE LOS CONSOLIDADORES INTERNACIONALES DE CARGA CYtf>",
        "Artículo 66.- Consolidador internacional de carga. El consolidador",
    ) + on_page(
        81,
        "CAPÍTULO V",
        "DE LOS MODOS DE EXTINCIÓN DE LA OBLIGACIÓN TRIBUTARIA ADUANERA L ytf",
        "Artículo 97.- Modos de extinción. La obligación tributaria aduanera se",
    ) + on_page(
        195,
        "CAPITULO III",
        "Lyti",
        "DE LAS FALTAS",
        "Artículo 352.- Clasificación de las faltas. Las faltas se clasifican en",
    )

    split = split_articles(LEY, lines)
    a66, a97, a352 = split.articles

    assert a66.seccion == "SECCIÓN X: DE LOS CONSOLIDADORES INTERNACIONALES DE CARGA"
    assert a97.capitulo == "CAPÍTULO V: DE LOS MODOS DE EXTINCIÓN DE LA OBLIGACIÓN TRIBUTARIA ADUANERA"
    assert a352.capitulo == "CAPÍTULO III: DE LAS FALTAS"
    assert split.removed == {"junk line inside a heading name": 1}
    assert split.heading_tokens_deleted == 3


def test_a_cross_reference_wrapped_to_the_start_of_a_line_does_not_start_an_article():
    lines = on_page(
        35,
        "Artículo 49.- Exenciones. Estarán exentas del pago las mercancías señaladas en el",
        "artículo 50 de esta ley.",
        "Artículo 50.- Franquicias. Las franquicias se concederán conforme a la ley.",
    )

    a49, a50 = split_articles(LEY, lines).articles

    assert (a49.number, a50.number) == (49, 50)
    assert a49.text.endswith("artículo 50 de esta ley.")


def test_the_closing_formula_after_the_last_article_is_cut_and_counted():
    lines = on_page(
        135,
        "ARTÍCULO 317. Entrada en vigor. El presente Reglamento entrará en vigencia a partir de su",
        "publicación.",
        "ARTÍCULO 318. Envíese a las instituciones correspondientes, para su conocimiento y ejecución.",
        "DADO en la ciudad de Santo Domingo de Guzmán, Distrito Nacional, capital de la República",
        "Dominicana, a los veintitrés ( 23 ) dias del mes de diciembre del año dos mil",
        "IS ABINADER",
    )

    split = split_articles(DECRETO_755, lines)

    assert split.articles[-1].text == (
        "ARTÍCULO 318. Envíese a las instituciones correspondientes, para su conocimiento y ejecución."
    )
    assert split.closing_words == 33


def test_dado_que_inside_an_earlier_article_is_not_the_closing_formula():
    lines = on_page(
        103,
        "ARTÍCULO 237. Tramitación separada del procedimiento administrativo sancionador.",
        "Dado que las sanciones por la comisión de faltas aduaneras y faltas tributarias aduaneras, asi como",
        "ARTÍCULO 238. Principios. El procedimiento se regirá por los principios de legalidad.",
    )

    a237, a238 = split_articles(DECRETO_755, lines).articles

    assert a237.text.endswith("faltas tributarias aduaneras, asi como")
    assert a238.number == 238


def test_the_norma_splits_on_ordinals_and_keeps_every_fee_row_on_its_own_line():
    lines = on_page(
        5,
        "DICTA LA SIGUIENTE:",
    ) + on_page(
        6,
        "PRIMERO: En cumplimiento de lo que disponen el artículo 13 párrafo II y el",
        "NOMBRE DE SERVICIO MONEDA COSTO",
        "ADQUISICIÓN CERTIFICADO DIGITAL RD$ 4,000.00",
        "CAMBIO DE VINCULACIÓN DE USUARIO SUSCRITO RD$ 750.00",
    ) + on_page(
        9,
        "VERIFICACIÓNES A DESTINO PARA MERCANCÍAS SUELTAS EN CONTENEDORES DE 20' CON DISTANCIA DE >200 KM RD$ 4,500.00",
        "SEGUNDO: Dado que la inflación ha estado por encima del rango meta",
        "TERCERO: De conformidad con lo dispuesto en el artículo 13 párrafo II y el",
    ) + on_page(
        10,
        "CUARTO: Se ordena que la entrada en vigor de estas nuevas tasas sea a partir",
        "del día dos (2) enero del año dos mil veinticuatro (2024)",
        "Dada en la ciudad de Santo Domingo, Distrito Nacional, a los once días (11) días",
        "Eduardo Sanz Lovatón",
    )

    split = split_articles(NORMA, lines)

    assert [(a.number, a.page, a.title) for a in split.articles] == [(1, 6, ""), (2, 9, ""), (3, 9, ""), (4, 10, "")]
    assert split.articles[0].text.splitlines()[2:] == [
        "ADQUISICIÓN CERTIFICADO DIGITAL RD$ 4,000.00",
        "CAMBIO DE VINCULACIÓN DE USUARIO SUSCRITO RD$ 750.00",
        "VERIFICACIÓNES A DESTINO PARA MERCANCÍAS SUELTAS EN CONTENEDORES DE 20' CON DISTANCIA DE >200 KM RD$ 4,500.00",
    ]
    assert split.articles[3].text.endswith("veinticuatro (2024)")
    assert split.preamble_words == 3


def test_a_document_without_any_article_heading_is_an_error():
    with pytest.raises(ValueError, match="no article heading"):
        split_articles(LEY, on_page(1, "Considerando primero: Que la Constitución de la República Dominicana,"))


@pytest.mark.parametrize(
    ("text", "title"),
    [
        (
            "Artículo 177.- Mercancías dañadas. Las mercancías y los bultos con\nseñales de daño o deterioro, se colocarán en sitio aparte.",
            "Mercancías dañadas",
        ),
        (
            "Artículo 69.- Causas de amonestación escrita comunes a todos los\noperadores aduaneros. Será motivo de sanción amonestación escrita,",
            "Causas de amonestación escrita comunes a todos los operadores aduaneros",
        ),
        (
            "Artículo 418.- Derogaciones parciales Ley núm.226. Quedan derogados\nlos artículos 1, 2, 3, 4, 6, 7, 9, 13, 14, 19, 20, 21 y 22 de la Ley",
            "Derogaciones parciales Ley núm.226",
        ),
        (
            "Artículo 378 .-Responsabilidad por sanciones a los empleados dependientes\no representantes. Las personas físicas o jurídicas, sociedades,",
            "Responsabilidad por sanciones a los empleados dependientes o representantes",
        ),
        (
            "ARTÍCULO 231. Registro Courier (RUA). Se crea un registro de usuarios de servicios de",
            "Registro Courier (RUA)",
        ),
        (
            "ARTÍCULO 70: Determinación de oficio de la Obligación Tributaria Aduanera. La Aduana\ndeterminará oficiosamente la obligación tributaria aduanera en los casos siguientes:",
            "Determinación de oficio de la Obligación Tributaria Aduanera",
        ),
        (
            "ARTICULO 201, De la selección y verificación de los envíos por las autoridades aduaneras.\nRecibidos los manifiestos de carga expresa de manera electrónica, el Sistema de Análisis de Riesgo",
            "De la selección y verificación de los envíos por las autoridades aduaneras",
        ),
        (
            "ARTÍCULO 237. Tramitación separada del procedimiento administrativo sancionador.\nDado que las sanciones por la comisión de faltas aduaneras",
            "Tramitación separada del procedimiento administrativo sancionador",
        ),
        (
            "Artículo 393.- Contenido de la sentencia condenatoria.\n1) Cuando la sentencia sea condenatoria, el Tribunal impondrá, según",
            "Contenido de la sentencia condenatoria",
        ),
        (
            "ARTÍCULO 5. Aplicación de la Ley núm. 168-21. Las disposiciones de la ley se aplicarán",
            "Aplicación de la Ley núm. 168-21",
        ),
    ],
)
def test_the_title_is_the_short_phrase_between_the_number_and_the_first_sentence_end(text, title):
    assert split_title(text) == title


@pytest.mark.parametrize(
    "text",
    [
        # One long sentence: the article has no epigraph.
        "ARTÍCULO 15. La DGA, de conformidad con lo establecido en los artículos 25, 26 y el párrafo\n"
        "II del artículo 28 de la Ley de Aduanas, como organismo coordinador de la gestión de riesgo,\n"
        "facilitará la interconexión, para que todas las instituciones que ejerzan un rol de control en zona\n"
        "primaria aduanera sobre la seguridad, el ingreso o salida de personas, mercancías o medios de\n"
        "transporte puedan gestionar los riesgos en el ámbito de sus competencias. Asimismo, la DGA\n"
        "establecerá los requisitos mínimos tecnológicos que deberá tener cada institución para garantizar\n"
        "su correcto funcionamiento.",
        # The whole article is a single short sentence: that sentence is the article, not its title.
        "ARTÍCULO 318. Envíese a las instituciones correspondientes, para su conocimiento y ejecución.",
        # A sentence that opens a list: the colon shows it is not an epigraph.
        "ARTÍCULO 177. Los envios de entrega rápida se clasificarán conforme a las siguientes\n"
        "categorías:\n"
        "a) Categoría A. Correspondencias y documentos. En esta se contemplan las correspondencias",
        # The norma's provisions have no epigraph at all.
        "PRIMERO: En cumplimiento de lo que disponen el artículo 13 párrafo II y el\nartículo 61, se ajustan las tasas. Servicios a ser Ajustados",
    ],
)
def test_an_article_without_an_epigraph_has_an_empty_title(text):
    assert split_title(text) == ""


def test_numbering_that_runs_from_one_without_gaps_passes():
    articles = split_articles(DECRETO_609, on_page(
        3,
        "ARTÍCULO 1. Objeto. El presente Reglamento tiene por objeto regular",
        "ARTÍCULO 2. Ámbito de aplicación. Este Reglamento constituye un marco",
    )).articles

    check_numbering(articles)


def test_a_missing_or_repeated_article_number_stops_the_build():
    articles = split_articles(DECRETO_609, on_page(
        3,
        "ARTÍCULO 1. Objeto. El presente Reglamento tiene por objeto regular",
        "ARTÍCULO 3. Autoridad. La Dirección General de Aduanas",
        "ARTÍCULO 3. Autoridad. La Dirección General de Aduanas",
    )).articles

    with pytest.raises(ValueError, match=r"missing \[2\].*repeated \[3\]"):
        check_numbering(articles)
