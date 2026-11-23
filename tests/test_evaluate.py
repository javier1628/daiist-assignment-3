"""The retrieval part of the evaluation. Retrieval is faked here: no test calls the Gemini API."""

import pytest

from evaluate import Question, parse_expected, read_questions, score_retrieval

HEADER = "id,question,kind,expected_source,expected_location,reference_answer\n"
KNOWN = {"ley-168-21.pdf", "decreto-755-22.pdf", "norma-01-2023.pdf"}


def test_one_source_and_one_location_is_one_expected_passage():
    assert parse_expected("ley-168-21.pdf", "Artículo 80", KNOWN) == (("ley-168-21.pdf", 80),)
    assert parse_expected("ley-168-21.pdf", "80", KNOWN) == (("ley-168-21.pdf", 80),)


def test_several_sources_and_locations_are_paired_in_order():
    assert parse_expected("ley-168-21.pdf; decreto-755-22.pdf", "Artículo 80; Artículo 176", KNOWN) == (
        ("ley-168-21.pdf", 80),
        ("decreto-755-22.pdf", 176),
    )


def test_one_source_serves_every_location_when_it_is_the_only_one():
    assert parse_expected("ley-168-21.pdf", "Artículo 80; Artículo 81", KNOWN) == (
        ("ley-168-21.pdf", 80),
        ("ley-168-21.pdf", 81),
    )


def test_an_ordinal_location_is_the_number_of_that_provision():
    assert parse_expected("norma-01-2023.pdf", "PRIMERO", KNOWN) == (("norma-01-2023.pdf", 1),)


@pytest.mark.parametrize(
    ("sources", "locations"),
    [
        ("ley-168-21.pdf; decreto-755-22.pdf", "Artículo 80; Artículo 81; Artículo 82"),  # 2 sources, 3 locations
        ("ley-168-21.pdf", "página 74"),  # not an article
        ("ley-168-21", "Artículo 80"),  # not a file name of the index
        ("ley-168-21.pdf", ""),
    ],
)
def test_anything_else_is_an_error(sources, locations):
    with pytest.raises(ValueError):
        parse_expected(sources, locations, KNOWN)


def test_questions_are_read_with_their_kind_and_expected_passages(tmp_path):
    path = tmp_path / "questions.csv"
    path.write_text(
        HEADER
        + 'q01,¿Cuál es la base imponible?,single,ley-168-21.pdf,Artículo 80,"El valor en aduana."\n'
        + "q02,¿Y el envío expreso?,multi,ley-168-21.pdf; decreto-755-22.pdf,Artículo 80; Artículo 176,Ambos.\n"
        + "q03,¿Cuánto cuesta un visado?,unanswerable,,,No está en los documentos.\n",
        encoding="utf-8",
    )

    questions = read_questions(path, KNOWN)

    assert questions == [
        Question("q01", "¿Cuál es la base imponible?", "single", (("ley-168-21.pdf", 80),)),
        Question("q02", "¿Y el envío expreso?", "multi", (("ley-168-21.pdf", 80), ("decreto-755-22.pdf", 176))),
        Question("q03", "¿Cuánto cuesta un visado?", "unanswerable", ()),
    ]


@pytest.mark.parametrize(
    "row",
    [
        "q01,¿Pregunta?,simple,ley-168-21.pdf,Artículo 80,Respuesta.\n",  # unknown kind
        "q01,¿Pregunta?,unanswerable,ley-168-21.pdf,Artículo 80,Respuesta.\n",  # unanswerable with a source
        "q01,¿Pregunta?,single,,,Respuesta.\n",  # answerable without a source
    ],
)
def test_a_row_that_breaks_the_format_is_an_error_that_names_its_id(tmp_path, row):
    path = tmp_path / "questions.csv"
    path.write_text(HEADER + row, encoding="utf-8")

    with pytest.raises(ValueError, match="q01"):
        read_questions(path, KNOWN)


def hit(source: str, article: int) -> dict:
    return {"source": source, "article": article}


def test_hit_rates_count_a_question_when_an_expected_passage_is_in_the_top_k():
    questions = [
        Question("q01", "uno", "single", (("ley-168-21.pdf", 80),)),
        Question("q02", "dos", "single", (("ley-168-21.pdf", 5),)),
        Question("q03", "tres", "multi", (("ley-168-21.pdf", 80), ("decreto-755-22.pdf", 176))),
        Question("q04", "cuatro", "unanswerable", ()),
    ]
    ranked = {
        # the expected article first / fourth / one of the two second and the other fifth
        "uno": [hit("ley-168-21.pdf", 80), hit("ley-168-21.pdf", 1), hit("ley-168-21.pdf", 2), hit("ley-168-21.pdf", 3), hit("ley-168-21.pdf", 4)],
        "dos": [hit("decreto-755-22.pdf", 5), hit("ley-168-21.pdf", 1), hit("ley-168-21.pdf", 2), hit("ley-168-21.pdf", 5), hit("ley-168-21.pdf", 4)],
        "tres": [hit("ley-168-21.pdf", 1), hit("decreto-755-22.pdf", 176), hit("ley-168-21.pdf", 2), hit("ley-168-21.pdf", 3), hit("ley-168-21.pdf", 80)],
    }
    asked = []

    def retrieve(question: str, mode: str) -> list[dict]:
        asked.append((question, mode))
        return ranked[question] if mode == "vector" else []

    scores = score_retrieval(questions, retrieve)

    assert ("cuatro", "vector") not in asked  # unanswerable questions are skipped
    assert scores["skipped"] == 1
    assert scores["groups"]["all"]["n"] == 3
    assert [scores["groups"]["all"]["vector", k] for k in (1, 3, 5)] == [1, 2, 3]
    assert [scores["groups"]["single"]["vector", k] for k in (1, 3, 5)] == [1, 1, 2]
    assert [scores["groups"]["multi"]["vector", k] for k in (1, 3, 5)] == [0, 1, 1]
    assert [scores["groups"]["all"]["hybrid", k] for k in (1, 3, 5)] == [0, 0, 0]
    assert scores["several"]["n"] == 1  # questions that expect two or more passages
    assert [scores["several"]["vector", k, "any"] for k in (1, 3, 5)] == [0, 1, 1]
    assert [scores["several"]["vector", k, "all"] for k in (1, 3, 5)] == [0, 0, 1]
