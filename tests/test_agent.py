"""The agent's harness. The chat model and the corpus tools are fakes: no test calls Gemini or starts server.py."""

import asyncio
import builtins
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, SystemMessage
from pydantic import Field

import agent
from agent import (
    APPROVAL_DENIED_MESSAGE,
    MAX_MODEL_CALLS,
    REFUSAL,
    SEARCH_LIMIT_MESSAGE,
    UNCOVERED_MARKER,
    Bridge,
    answer,
    cache_key,
    guard,
    read_answer,
    run_question,
    terminal_approval,
)

ROOT = Path(__file__).resolve().parent.parent
QUESTION = "¿Sobre qué valor se calculan los impuestos de importación?"
SEARCH_RESULT = (
    "[Ley 168-21, art. 80] Ley 168-21 de Aduanas — Artículo 80 — Base imponible y su determinación — part 1"
    " — page 74 — ley-168-21.pdf\n"
    "Artículo 80.- Base imponible y su determinación. La base imponible será la que disponga la legislación nacional.\n\n"
    "[Decreto 755-22, art. 148] Decreto 755-22, Reglamento de aplicación de la Ley 168-21 de Aduanas — Artículo 148"
    " — Contenido de una declaración aduanera — part 3 — page 65 — decreto-755-22.pdf\n"
    "1) Bienes y servicios suministrados al importador."
)
GOOD_ANSWER = "Los impuestos se calculan sobre la base imponible que disponga la legislación nacional [Ley 168-21, art. 80]."
DESCRIPTIONS = {"search": "Search the corpus.", "add_document": "Add a PDF to the corpus."}


class FakeCorpus:
    """Stands in for the MCP server: records every tool call it receives and answers with fixed texts."""

    def __init__(self, search_result: str = SEARCH_RESULT):
        self.calls: list[tuple[str, dict]] = []
        self.search_result = search_result

    async def __call__(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        return self.search_result if name == "search" else "norma-01-2023.pdf indexed: 8 chunks added."


class Scripted(GenericFakeChatModel):
    """A chat model that replies with the messages it was given, in order, and keeps what it was sent."""

    seen: list = Field(default_factory=list)

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, *args, **kwargs):
        self.seen.append(messages)
        return super()._generate(messages, *args, **kwargs)


def scripted(*messages: AIMessage) -> Scripted:
    return Scripted(messages=iter(messages))


def calls(tool: str, number: int = 1, **arguments) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": tool, "args": arguments, "id": f"call-{number}", "type": "tool_call"}],
        usage_metadata={"input_tokens": 100, "output_tokens": 10, "total_tokens": 110},
    )


def says(text: str) -> AIMessage:
    return AIMessage(content=text, usage_metadata={"input_tokens": 300, "output_tokens": 40, "total_tokens": 340})


def deny(path: str) -> bool:
    return False


def run(model, corpus, approve=deny) -> dict:
    return asyncio.run(run_question(QUESTION, model, corpus, DESCRIPTIONS, "REGLAS DEL ASISTENTE", approve))


# --- reading the structure out of an answer ----------------------------------


def test_an_answer_gives_its_citations_and_the_parts_it_says_are_not_covered():
    text = (
        f"{GOOD_ANSWER} También aplica el reglamento [Decreto 755-22, art. 148] y de nuevo [Ley 168-21, art. 80].\n"
        f"{UNCOVERED_MARKER} la tasa aplicable; el plazo de pago. Consulte a su agente de aduanas."
    )

    result = read_answer(text)

    assert result == {
        "answer": text,
        "citations": ["[Ley 168-21, art. 80]", "[Decreto 755-22, art. 148]"],
        "refused": False,
        "uncovered": ["la tasa aplicable", "el plazo de pago"],
    }


def test_the_fixed_refusal_is_detected_and_returned_exactly():
    result = read_answer(f"\n  {REFUSAL}  \n")

    assert result == {"answer": REFUSAL, "citations": [], "refused": True, "uncovered": []}


def test_an_answer_that_cites_passages_is_not_a_refusal_even_if_it_repeats_the_refusal_sentence():
    assert read_answer(f"{GOOD_ANSWER} {REFUSAL}")["refused"] is False


# --- the guardrail -----------------------------------------------------------


def test_an_answer_whose_citations_were_all_retrieved_passes_the_guardrail():
    result = guard(read_answer(GOOD_ANSWER), {"[Ley 168-21, art. 80]", "[Decreto 755-22, art. 148]"})

    assert (result["answer"], result["blocked"]) == (GOOD_ANSWER, [])


def test_an_answer_that_cites_an_article_no_search_returned_is_replaced_by_the_refusal():
    invented = "El plazo es de treinta días [Ley 168-21, art. 91] y la base es el valor [Ley 168-21, art. 80]."

    result = guard(read_answer(invented), {"[Ley 168-21, art. 80]"})

    assert result["answer"] == REFUSAL
    assert (result["refused"], result["citations"]) == (True, [])
    assert result["blocked"] == ["[Ley 168-21, art. 91]"]
    assert result["blocked_answer"] == invented


# --- the tools as the model reaches them -------------------------------------


def test_a_fourth_search_is_not_run_and_the_model_is_told_to_answer():
    corpus = FakeCorpus()
    bridge = Bridge(corpus, deny)

    async def four_searches():
        return [await bridge.search(f"consulta {number}") for number in range(1, 5)]

    results = asyncio.run(four_searches())

    assert results == [SEARCH_RESULT, SEARCH_RESULT, SEARCH_RESULT, SEARCH_LIMIT_MESSAGE]
    assert corpus.calls == [("search", {"query": f"consulta {number}"}) for number in range(1, 4)]
    assert bridge.searches == 3
    assert bridge.retrieved == {"[Ley 168-21, art. 80]", "[Decreto 755-22, art. 148]"}


def test_the_first_search_of_a_question_is_the_question_as_written_whatever_the_model_asked():
    corpus = FakeCorpus()
    bridge = Bridge(corpus, deny, question=QUESTION)

    async def two_searches():
        await bridge.search("valor se calculan los impuestos de importación")
        await bridge.search("base imponible ad valorem")

    asyncio.run(two_searches())

    assert corpus.calls == [("search", {"query": QUESTION}), ("search", {"query": "base imponible ad valorem"})]
    assert bridge.trace[0]["arguments"] == {"query": QUESTION}
    assert bridge.trace[0]["replaced_query"] == "valor se calculan los impuestos de importación"
    assert "replaced_query" not in bridge.trace[1]


def test_add_document_does_not_reach_the_server_without_approval():
    corpus = FakeCorpus()

    result = asyncio.run(Bridge(corpus, deny).add_document("corpus/norma-01-2023.pdf"))

    assert result == APPROVAL_DENIED_MESSAGE
    assert corpus.calls == []


def test_add_document_runs_once_a_person_approves_that_path():
    corpus, asked = FakeCorpus(), []

    def approve(path: str) -> bool:
        asked.append(path)
        return True

    result = asyncio.run(Bridge(corpus, approve).add_document("corpus/norma-01-2023.pdf"))

    assert asked == ["corpus/norma-01-2023.pdf"]
    assert corpus.calls == [("add_document", {"path": "corpus/norma-01-2023.pdf"})]
    assert result == "norma-01-2023.pdf indexed: 8 chunks added."


def test_without_a_terminal_approval_is_denied_and_nobody_is_asked(monkeypatch):
    def no_prompt(*args):
        raise AssertionError("a person was asked")

    monkeypatch.setattr(builtins, "input", no_prompt)

    assert terminal_approval("corpus/norma-01-2023.pdf") is False  # pytest's stdin and stdout are not a terminal


# --- one question, end to end, with the scripted model -----------------------


def test_a_question_is_answered_from_a_search_and_its_cost_is_recorded():
    corpus, model = FakeCorpus(), scripted(calls("search", query=QUESTION), says(GOOD_ANSWER))

    record = run(model, corpus)

    assert record["answer"] == GOOD_ANSWER
    assert (record["citations"], record["refused"], record["uncovered"], record["blocked"]) == (
        ["[Ley 168-21, art. 80]"], False, [], [],
    )
    assert (record["searches"], record["model_calls"], record["input_tokens"], record["output_tokens"]) == (1, 2, 400, 50)
    assert record["retrieved"] == ["[Decreto 755-22, art. 148]", "[Ley 168-21, art. 80]"]
    assert record["trace"] == [{"tool": "search", "arguments": {"query": QUESTION}, "result": SEARCH_RESULT, "ran": True}]
    assert record["latency_seconds"] >= 0
    assert isinstance(model.seen[0][0], SystemMessage) and model.seen[0][0].content == "REGLAS DEL ASISTENTE"


def test_an_answer_citing_an_article_that_was_never_retrieved_is_blocked_in_the_run():
    model = scripted(calls("search", query=QUESTION), says("El plazo es de treinta días [Ley 168-21, art. 91]."))

    record = run(model, FakeCorpus())

    assert (record["answer"], record["refused"]) == (REFUSAL, True)
    assert record["blocked"] == ["[Ley 168-21, art. 91]"]
    assert record["blocked_answer"] == "El plazo es de treinta días [Ley 168-21, art. 91]."


def test_the_model_asking_to_add_a_document_is_denied_when_nobody_can_approve():
    corpus = FakeCorpus()
    model = scripted(calls("add_document", path="corpus/norma-01-2023.pdf"), says(REFUSAL))

    record = run(model, corpus)

    assert corpus.calls == []
    assert record["trace"] == [
        {"tool": "add_document", "arguments": {"path": "corpus/norma-01-2023.pdf"}, "result": APPROVAL_DENIED_MESSAGE, "ran": False}
    ]
    assert record["refused"] is True


def test_a_model_that_never_stops_calling_tools_is_cut_off_and_the_question_refused():
    corpus = FakeCorpus()
    model = scripted(*[calls("search", number, query=f"consulta {number}") for number in range(1, MAX_MODEL_CALLS + 3)])

    record = run(model, corpus)

    assert (record["answer"], record["refused"]) == (REFUSAL, True)
    assert f"{MAX_MODEL_CALLS} model calls" in record["stopped"]
    assert record["model_calls"] == MAX_MODEL_CALLS
    assert len(corpus.calls) == 3  # the search limit held too


# --- the cache ----------------------------------------------------------------


def test_the_model_paraphrasing_its_first_search_still_searches_the_question_itself():
    corpus = FakeCorpus()
    model = scripted(calls("search", query="impuestos de importación valor"), says(GOOD_ANSWER))

    record = run(model, corpus)

    assert corpus.calls == [("search", {"query": QUESTION})]
    assert record["trace"][0]["replaced_query"] == "impuestos de importación valor"


def test_the_cache_key_changes_with_the_question_the_setting_the_model_and_the_prompt():
    base = cache_key(QUESTION, "vector:5", "gemini-x", "abc123")

    assert cache_key(QUESTION, "vector:5", "gemini-x", "abc123") == base
    assert len({
        base,
        cache_key("¿Otra pregunta?", "vector:5", "gemini-x", "abc123"),
        cache_key(QUESTION, "hybrid:5", "gemini-x", "abc123"),
        cache_key(QUESTION, "vector:5", "gemini-y", "abc123"),
        cache_key(QUESTION, "vector:5", "gemini-x", "def456"),
    }) == 5


def fake_server(corpus: FakeCorpus):
    @asynccontextmanager
    async def server(setting: str):
        yield corpus, DESCRIPTIONS

    return server


def ask(tmp_path, model, corpus, setting="vector:5") -> dict:
    return asyncio.run(answer(
        QUESTION, setting=setting, approve=deny, cache_path=tmp_path / "agent_cache.jsonl",
        chat_model=model, server=fake_server(corpus),
    ))


def test_the_same_question_asked_again_comes_from_the_cache_at_no_cost(tmp_path):
    corpus = FakeCorpus()
    first = ask(tmp_path, scripted(calls("search", query=QUESTION), says(GOOD_ANSWER)), corpus)

    again = ask(tmp_path, scripted(), corpus)  # a model with nothing to say: it must not be consulted

    assert (first["cached"], again["cached"]) == (False, True)
    assert again["answer"] == first["answer"] == GOOD_ANSWER
    assert len(corpus.calls) == 1
    assert (first["model"], first["setting"], first["embeddings_sent"]) == (agent.MODEL, "vector:5", 0)


def test_another_retrieval_setting_is_a_different_question_for_the_cache(tmp_path):
    corpus = FakeCorpus()
    ask(tmp_path, scripted(calls("search", query=QUESTION), says(GOOD_ANSWER)), corpus)

    other = ask(tmp_path, scripted(calls("search", query=QUESTION), says(GOOD_ANSWER)), corpus, setting="hybrid:5")

    assert other["cached"] is False
    assert len(corpus.calls) == 2


def test_a_run_in_which_a_tool_failed_is_not_cached(tmp_path):
    failing = FakeCorpus(search_result="TOOL ERROR: The question could not be embedded, so nothing was searched.")
    first = ask(tmp_path, scripted(calls("search", query=QUESTION), says(REFUSAL)), failing)

    second = ask(tmp_path, scripted(calls("search", query=QUESTION), says(GOOD_ANSWER)), FakeCorpus())

    assert (first["tool_errors"], first["cached"]) == (1, False)
    assert (second["cached"], second["answer"]) == (False, GOOD_ANSWER)


# --- the written rules carry what the code looks for --------------------------


def test_agents_md_states_the_fixed_refusal_the_marker_and_the_citation_form():
    rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert REFUSAL in rules
    assert UNCOVERED_MARKER in rules
    assert "[Ley 168-21, art. 80]" in rules


def test_the_subagent_has_only_the_search_tool_and_the_same_refusal():
    text = (ROOT / ".claude" / "agents" / "corpus-researcher.md").read_text(encoding="utf-8")
    front_matter = text.split("---")[1]

    assert "tools: mcp__corpus__search\n" in front_matter
    assert "TODO" not in text
    assert REFUSAL in text and UNCOVERED_MARKER in text


# --- failures of the model reach the caller as themselves ---------------------


class Unavailable(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, *args, **kwargs):
        raise RuntimeError("503 UNAVAILABLE. This model is currently experiencing high demand.")


def test_a_model_error_wrapped_by_the_server_connection_is_raised_as_the_error_it_is(tmp_path):
    @asynccontextmanager
    async def wrapping_server(setting: str):  # the MCP client wraps whatever fails inside it in exception groups
        try:
            yield FakeCorpus(), DESCRIPTIONS
        except Exception as error:
            raise ExceptionGroup("unhandled errors in a TaskGroup", [ExceptionGroup("inner", [error])]) from error

    with pytest.raises(RuntimeError, match="503 UNAVAILABLE"):
        asyncio.run(answer(
            QUESTION, setting="vector:5", cache_path=tmp_path / "agent_cache.jsonl",
            chat_model=Unavailable(messages=iter([])), server=wrapping_server,
        ))

    assert not (tmp_path / "agent_cache.jsonl").exists()  # a failed run leaves nothing in the cache


class NeverAnswers(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

    async def _agenerate(self, messages, *args, **kwargs):
        await asyncio.sleep(30)


def test_a_question_the_model_never_answers_ends_with_a_timeout_instead_of_hanging(tmp_path):
    with pytest.raises(TimeoutError, match="did not finish within 0.05 s"):
        asyncio.run(answer(
            QUESTION, setting="vector:5", cache_path=tmp_path / "agent_cache.jsonl",
            chat_model=NeverAnswers(messages=iter([])), server=fake_server(FakeCorpus()), timeout=0.05,
        ))

    assert not (tmp_path / "agent_cache.jsonl").exists()
