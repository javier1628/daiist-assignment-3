"""The evaluation. Retrieval, the agent and the judge are faked here: no test calls the Gemini API."""

import json

import pytest

from agent import REFUSAL
from evaluate import (
    Question,
    agreement,
    check_answer,
    judge,
    judge_all,
    parse_expected,
    read_human_labels,
    read_questions,
    rubric_is_written,
    run_agent,
    score_retrieval,
)

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
        Question("q01", "¿Cuál es la base imponible?", "single", (("ley-168-21.pdf", 80),), "El valor en aduana."),
        Question("q02", "¿Y el envío expreso?", "multi", (("ley-168-21.pdf", 80), ("decreto-755-22.pdf", 176)), "Ambos."),
        Question("q03", "¿Cuánto cuesta un visado?", "unanswerable", (), "No está en los documentos."),
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


# --- the agent's answers: checks done in code --------------------------------

SINGLE = Question("q01", "¿Cuál es la base imponible?", "single", (("ley-168-21.pdf", 80),), "El valor en aduana.")
MULTI = Question("q02", "¿Y el envío expreso?", "multi", (("ley-168-21.pdf", 80), ("decreto-755-22.pdf", 176)), "Ambos.")
UNANSWERABLE = Question("q03", "¿Cuánto cuesta un visado?", "unanswerable", (), "No está en los documentos.")
PASSAGE = "[Ley 168-21, art. 80] Ley 168-21 de Aduanas — Artículo 80 — Base imponible — part 1 — page 74 — ley-168-21.pdf\nArtículo 80.- La base imponible."


def record(answer: str, citations=(), refused=False, retrieved=("[Ley 168-21, art. 80]",), blocked=()) -> dict:
    return {
        "question": "", "answer": answer, "citations": list(citations), "refused": refused, "uncovered": [],
        "blocked": list(blocked), "stopped": "", "retrieved": list(retrieved), "searches": 1, "model_calls": 2,
        "input_tokens": 400, "output_tokens": 50, "latency_seconds": 1.5, "embeddings_sent": 1, "tool_errors": 0,
        "cached": False, "trace": [{"tool": "search", "arguments": {"query": "x"}, "result": PASSAGE, "ran": True}],
    }


def refusal() -> dict:
    return record(REFUSAL, refused=True)


def test_a_cited_answer_to_an_answerable_question_passes_every_check():
    checks = check_answer(SINGLE, record("Es el valor [Ley 168-21, art. 80].", ["[Ley 168-21, art. 80]"]))

    assert checks == {"refusal_ok": True, "citations_valid": True, "expected_cited": True, "all_expected_cited": True}


def test_refusing_is_right_only_for_an_unanswerable_question():
    assert check_answer(UNANSWERABLE, refusal())["refusal_ok"] is True
    assert check_answer(SINGLE, refusal())["refusal_ok"] is False
    assert check_answer(UNANSWERABLE, record("Cuesta 50 dólares [Ley 168-21, art. 80].", ["[Ley 168-21, art. 80]"]))["refusal_ok"] is False


def test_citations_are_invalid_when_missing_blocked_or_never_retrieved():
    assert check_answer(SINGLE, record("Es el valor en aduana."))["citations_valid"] is False  # an answer with no citation
    assert check_answer(SINGLE, record("x [Ley 168-21, art. 91].", ["[Ley 168-21, art. 91]"]))["citations_valid"] is False
    assert check_answer(SINGLE, record(REFUSAL, refused=True, blocked=["[Ley 168-21, art. 91]"]))["citations_valid"] is False
    assert check_answer(UNANSWERABLE, refusal())["citations_valid"] is True  # a refusal needs no citation


def test_the_expected_article_must_be_among_the_citations_one_or_all_of_them():
    one_of_two = record("x [Ley 168-21, art. 80].", ["[Ley 168-21, art. 80]"])
    other_article = record("x [Ley 168-21, art. 5].", ["[Ley 168-21, art. 5]"], retrieved=["[Ley 168-21, art. 5]"])

    assert (check_answer(MULTI, one_of_two)["expected_cited"], check_answer(MULTI, one_of_two)["all_expected_cited"]) == (True, False)
    assert check_answer(SINGLE, other_article)["expected_cited"] is False
    assert check_answer(UNANSWERABLE, refusal())["expected_cited"] is None  # nothing is expected of it


def test_the_agent_runs_on_every_question_and_each_answer_is_saved(tmp_path):
    asked = []

    def ask(question: str) -> dict:
        asked.append(question)
        return refusal() if "visado" in question else record("Es el valor [Ley 168-21, art. 80].", ["[Ley 168-21, art. 80]"])

    rows = run_agent([SINGLE, MULTI, UNANSWERABLE], ask, tmp_path / "answers.jsonl")

    saved = [json.loads(line) for line in (tmp_path / "answers.jsonl").read_text(encoding="utf-8").splitlines()]
    assert asked == [SINGLE.text, MULTI.text, UNANSWERABLE.text]
    assert saved == rows
    assert [(row["id"], row["kind"], row["refused"]) for row in rows] == [
        ("q01", "single", False), ("q02", "multi", False), ("q03", "unanswerable", True),
    ]


@pytest.mark.parametrize(
    "message",
    ["429 RESOURCE_EXHAUSTED. You exceeded your current quota.", "503 UNAVAILABLE. This model is currently experiencing high demand."],
)
def test_a_quota_or_availability_error_stops_the_run_and_keeps_the_answers_already_saved(tmp_path, message):
    def ask(question: str) -> dict:
        if question == MULTI.text:
            raise RuntimeError(message)
        return record("Es el valor [Ley 168-21, art. 80].", ["[Ley 168-21, art. 80]"])

    rows = run_agent([SINGLE, MULTI, UNANSWERABLE], ask, tmp_path / "answers.jsonl")

    assert [row["id"] for row in rows] == ["q01"]
    assert len((tmp_path / "answers.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_a_question_that_times_out_also_stops_the_run_cleanly(tmp_path):
    def ask(question: str) -> dict:
        raise TimeoutError("The agent did not finish within 240 s.")

    assert run_agent([SINGLE, MULTI], ask, tmp_path / "answers.jsonl") == []


def test_any_other_error_from_the_agent_is_raised(tmp_path):
    def ask(question: str) -> dict:
        raise ValueError("the server did not start")

    with pytest.raises(ValueError, match="did not start"):
        run_agent([SINGLE], ask, tmp_path / "answers.jsonl")


# --- the judge ---------------------------------------------------------------

RUBRIC = "## correct\nUn punto si coincide con la referencia.\n## supported\nUn punto si todo está en los pasajes."


def test_the_rubric_counts_as_written_once_no_todo_is_left():
    assert rubric_is_written(RUBRIC) is True
    assert rubric_is_written("## correct\n\nTODO: when is an answer right?") is False
    assert rubric_is_written("  \n") is False


def test_the_judge_reads_the_rubric_the_question_the_reference_the_answer_and_the_passages():
    prompts = []

    def generate(prompt: str) -> str:
        prompts.append(prompt)
        return '{"correct": 1, "supported": 0, "reason": "Cita el artículo correcto pero añade un plazo."}'

    row = {"id": "q01", "kind": "single"} | record("Es el valor [Ley 168-21, art. 80].", ["[Ley 168-21, art. 80]"])
    verdict = judge(SINGLE, row, RUBRIC, generate)

    assert verdict == {"id": "q01", "correct": 1, "supported": 0, "reason": "Cita el artículo correcto pero añade un plazo."}
    for part in (RUBRIC, SINGLE.text, "El valor en aduana.", "Es el valor [Ley 168-21, art. 80].", "Artículo 80.- La base imponible.", "single"):
        assert part in prompts[0]


@pytest.mark.parametrize("reply", ["no es JSON", '{"correct": 2, "supported": 1, "reason": "x"}', '{"correct": 1, "reason": "x"}'])
def test_a_judge_reply_that_is_not_two_grades_of_0_or_1_is_an_error(reply):
    row = {"id": "q01", "kind": "single"} | record("x")

    with pytest.raises(ValueError, match="q01"):
        judge(SINGLE, row, RUBRIC, lambda prompt: reply)


def test_a_verdict_is_asked_for_once_and_then_read_from_the_cache(tmp_path):
    calls = []

    def generate(prompt: str) -> str:
        calls.append(prompt)
        return '{"correct": 1, "supported": 1, "reason": "ok"}'

    rows = [{"id": "q01", "kind": "single"} | record("Es el valor [Ley 168-21, art. 80].", ["[Ley 168-21, art. 80]"])]
    first = judge_all([SINGLE], rows, RUBRIC, generate, tmp_path / "judge_cache.jsonl", "judge-model")
    again = judge_all([SINGLE], rows, RUBRIC, generate, tmp_path / "judge_cache.jsonl", "judge-model")
    other_rubric = judge_all([SINGLE], rows, RUBRIC + "\nMás estricto.", generate, tmp_path / "judge_cache.jsonl", "judge-model")

    assert first == again == [{"id": "q01", "correct": 1, "supported": 1, "reason": "ok"}]
    assert len(calls) == 2  # one for the first rubric, one for the changed rubric
    assert other_rubric[0]["id"] == "q01"


# --- agreement between the judge and the human labels ------------------------


def test_human_labels_are_read_as_two_grades_per_question(tmp_path):
    path = tmp_path / "human_labels.csv"
    path.write_text("id,correct,supported,notes\nq01,1,1,\nq02,0,1,Plazo equivocado\n,,,\n", encoding="utf-8")

    assert read_human_labels(path) == {"q01": {"correct": 1, "supported": 1}, "q02": {"correct": 0, "supported": 1}}


def test_a_human_grade_that_is_not_0_or_1_is_an_error_naming_the_question(tmp_path):
    path = tmp_path / "human_labels.csv"
    path.write_text("id,correct,supported,notes\nq07,si,1,\n", encoding="utf-8")

    with pytest.raises(ValueError, match="q07"):
        read_human_labels(path)


def test_agreement_is_the_share_of_equal_grades_and_cohens_kappa():
    human = {"q1": {"correct": 1, "supported": 1}, "q2": {"correct": 1, "supported": 1},
             "q3": {"correct": 0, "supported": 1}, "q4": {"correct": 0, "supported": 1}, "q9": {"correct": 1, "supported": 1}}
    verdicts = [{"id": "q1", "correct": 1, "supported": 1}, {"id": "q2", "correct": 0, "supported": 1},
                {"id": "q3", "correct": 0, "supported": 1}, {"id": "q4", "correct": 0, "supported": 1},
                {"id": "q5", "correct": 1, "supported": 1}]

    result = agreement(human, verdicts)

    # correct: 3 of the 4 graded by both agree. Chance agreement 0.5 * 0.25 + 0.5 * 0.75 = 0.5, so kappa = 0.5.
    assert (result["correct"]["n"], result["correct"]["agree"], result["correct"]["kappa"]) == (4, 3, 0.5)
    assert result["correct"]["disagreements"] == ["q2"]
    assert (result["correct"]["human_1_judge_0"], result["correct"]["human_0_judge_1"]) == (1, 0)
    # supported: both said 1 every time, so there is no variation to measure agreement beyond chance
    assert (result["supported"]["n"], result["supported"]["agree"], result["supported"]["kappa"]) == (4, 4, None)
