"""
Assignment 3: the agent (`main.py ask "question"` runs `python agent.py "question"`).

LangChain `create_agent` on Gemini, with AGENTS.md as the system prompt and the
two tools of server.py, reached over MCP. What this file adds around the model:

- Approval. add_document only runs after a person types yes at the terminal.
  Without a terminal on both input and output (evaluate.py, check.py) it is denied.
- Limits. At most MAX_SEARCHES searches and MAX_MODEL_CALLS model calls per question.
- First search. The first search of a question is the question as written,
  whatever wording the model chose. Its vector is already saved for any
  question that was evaluated, so it costs no embedding, and it is the search
  whose hit rate evaluate.py measures.
- Citation guardrail. Every document and article the answer cites must be among
  the chunks a search returned for that question. If one is not, the answer is
  replaced by the refusal and what was blocked is logged.
- Structure. The answer text follows a fixed form (AGENTS.md), from which the
  citations, the refusal and the parts not covered are read by code.
- Cache. A result is saved under its question, retrieval setting, model and
  prompt version, so asking again costs nothing.

`ask(question)` returns the record of one question, tool trace included, for
evaluate.py.
"""

import asyncio
import hashlib
import json
import os
import sys
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tools import StructuredTool

import index
import retrieval

ROOT = Path(__file__).resolve().parent
AGENTS_FILE = ROOT / "AGENTS.md"
CACHE_FILE = ROOT / "eval" / "agent_cache.jsonl"

# Free tier, function calling, and the only free model that answered reliably when this was built (2026-11-24):
# gemini-3.1-flash-lite, gemini-3-flash-preview, gemini-3.6-flash, gemini-3.8-flash and gemini-4-hydrogen returned
# "503 high demand" or timed out on most requests.
# TEMPERATURE HAS NO EFFECT ON THIS MODEL. Google fixed the sampling of gemini-3.5-flash-lite, gemini-3.6-flash and
# later models, and langchain-google-genai drops the value with a warning. gemini-3.1-flash-lite does take it: to
# run at a real temperature of 0, set MODEL to it. What keeps answers stable here is the cache, not the temperature.
MODEL = "gemini-3.5-flash-lite"
TEMPERATURE = 0
HARNESS = "2"  # raise it when the code around the model changes what an answer can be, so old cached answers are not reused
MAX_SEARCHES = 3  # per question: each new search text costs one embedding
MAX_MODEL_CALLS = 6  # per question: three searches, the answer and some slack
REQUEST_TIMEOUT = 40  # seconds one request to the model may take; without it an unanswered request waits forever
QUESTION_TIMEOUT = 240  # seconds a whole question may take: check.py gives `main.py ask` 300

# The two fixed pieces of an answer that code looks for. AGENTS.md states both, word for word.
REFUSAL = "No puedo responder a esta pregunta con los documentos disponibles. Consulte a su agente de aduanas."
REFUSAL_CORE = "no puedo responder a esta pregunta con los documentos disponibles"
UNCOVERED_MARKER = "No cubierto por los documentos:"
UNCOVERED_ENDING = "Consulte a su agente de aduanas"

SEARCH_LIMIT_MESSAGE = (
    f"Search limit reached: {MAX_SEARCHES} searches per question. This search was NOT run. "
    "Answer now from the passages you already have."
)
APPROVAL_DENIED_MESSAGE = (
    "add_document was NOT run: adding a document needs the approval of a person at the terminal, "
    "and it was not given."
)
TOOL_ERROR = "TOOL ERROR"

CallTool = Callable[[str, dict], Awaitable[str]]  # (tool name, arguments) -> the tool's text


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------


def terminal_approval(path: str) -> bool:
    """Ask the person at the terminal whether a document may be added. No terminal means no."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        log(f"add_document({path!r}) denied: there is no terminal to ask for approval.")
        return False
    reply = input(f"\nThe agent wants to add this document to the index:\n  {path}\nType yes to allow it: ")
    return reply.strip().lower() in ("yes", "y", "si", "sí")


def deny_all(path: str) -> bool:
    """The approval of a run nobody watches: always no."""
    log(f"add_document({path!r}) denied: this run does not ask for approval.")
    return False


# ---------------------------------------------------------------------------
# The tools as the model reaches them
# ---------------------------------------------------------------------------


class Bridge:
    """The corpus tools for one question, with their limits and a record of what happened."""

    def __init__(
        self, call_tool: CallTool, approve: Callable[[str], bool], question: str = "", max_searches: int = MAX_SEARCHES
    ):
        self.call_tool = call_tool
        self.approve = approve
        self.question = question  # when given, the first search runs this text instead of the model's
        self.max_searches = max_searches
        self.searches = 0  # searches that reached the server
        self.retrieved: set[str] = set()  # citation tags of every chunk a search returned
        self.trace: list[dict] = []
        self.tool_errors = 0

    def record(self, tool: str, arguments: dict, result: str, ran: bool) -> str:
        self.trace.append({"tool": tool, "arguments": arguments, "result": result, "ran": ran})
        self.tool_errors += result.startswith(TOOL_ERROR)
        return result

    async def search(self, query: str) -> str:
        if self.searches >= self.max_searches:
            return self.record("search", {"query": query}, SEARCH_LIMIT_MESSAGE, ran=False)
        asked = query
        if self.question and self.searches == 0:
            query = self.question
        self.searches += 1
        result = await self.call_tool("search", {"query": query})
        self.retrieved.update(retrieval.result_tags(result))
        self.record("search", {"query": query}, result, ran=True)
        if asked != query:
            self.trace[-1]["replaced_query"] = asked
        return result

    async def add_document(self, path: str) -> str:
        if not self.approve(path):
            return self.record("add_document", {"path": path}, APPROVAL_DENIED_MESSAGE, ran=False)
        result = await self.call_tool("add_document", {"path": path})
        return self.record("add_document", {"path": path}, result, ran=True)

    def tools(self, descriptions: dict[str, str]) -> list[StructuredTool]:
        """The two tools for the model, described with the server's own words."""
        return [
            StructuredTool.from_function(coroutine=self.search, name="search", description=descriptions["search"]),
            StructuredTool.from_function(
                coroutine=self.add_document, name="add_document", description=descriptions["add_document"]
            ),
        ]


@asynccontextmanager
async def corpus_server(setting: str):
    """Start server.py over stdio. Yields a function that calls its tools, and the tools' descriptions."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    environment = {retrieval.SETTING_VARIABLE: setting}
    if os.environ.get("GEMINI_API_KEY"):  # a stdio server does not inherit the environment
        environment["GEMINI_API_KEY"] = os.environ["GEMINI_API_KEY"]
    parameters = StdioServerParameters(
        command=sys.executable, args=[str(ROOT / "server.py")], cwd=str(ROOT), env=environment
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = (await session.list_tools()).tools

            async def call_tool(name: str, arguments: dict) -> str:
                result = await session.call_tool(name, arguments)
                text = "\n".join(getattr(part, "text", "") for part in result.content).strip()
                failed = getattr(result, "is_error", False) or getattr(result, "isError", False)
                return f"{TOOL_ERROR}: {text}" if failed else text

            yield call_tool, {tool.name: tool.description or "" for tool in listed}


# ---------------------------------------------------------------------------
# From the model's text to a structured, checked answer
# ---------------------------------------------------------------------------


def read_answer(text: str) -> dict:
    """The structure of an answer written in the fixed form: citations, refusal and parts not covered."""
    citations = list(dict.fromkeys(retrieval.CITATION_TAG.findall(text)))
    refused = REFUSAL_CORE in " ".join(text.split()).lower() and not citations
    uncovered: list[str] = []
    for line in text.splitlines():
        if UNCOVERED_MARKER in line:
            listed = line.split(UNCOVERED_MARKER, 1)[1].split(UNCOVERED_ENDING)[0]
            uncovered += [part.strip(" .") for part in listed.split(";") if part.strip(" .")]
    return {
        "answer": REFUSAL if refused else text.strip(),
        "citations": citations,
        "refused": refused,
        "uncovered": [] if refused else uncovered,
    }


def guard(result: dict, retrieved: set[str]) -> dict:
    """Block an answer that cites a document and article no search returned for this question."""
    blocked = [tag for tag in result["citations"] if tag not in retrieved]
    if not blocked:
        return result | {"blocked": []}
    log(
        f"BLOCKED by the citation guardrail: the answer cited {', '.join(blocked)}, which no search returned "
        f"for this question. Retrieved: {', '.join(sorted(retrieved)) or 'nothing'}.\n"
        f"The blocked answer was:\n{result['answer']}"
    )
    return {
        "answer": REFUSAL,
        "citations": [],
        "refused": True,
        "uncovered": [],
        "blocked": blocked,
        "blocked_answer": result["answer"],
    }


class Usage(BaseCallbackHandler):
    """Counts the model calls of a run and adds up their tokens, whether or not the run ends well."""

    def __init__(self) -> None:
        self.model_calls = self.input_tokens = self.output_tokens = 0

    def on_chat_model_start(self, serialized, messages, **kwargs) -> None:
        self.model_calls += 1

    def on_llm_end(self, response, **kwargs) -> None:
        for generations in response.generations:
            for generation in generations:
                usage = getattr(getattr(generation, "message", None), "usage_metadata", None) or {}
                self.input_tokens += usage.get("input_tokens", 0)
                self.output_tokens += usage.get("output_tokens", 0)


async def run_question(
    question: str,
    chat_model,
    call_tool: CallTool,
    descriptions: dict[str, str],
    system_prompt: str,
    approve: Callable[[str], bool],
) -> dict:
    """Let the model answer one question with the corpus tools, then structure and check what it wrote."""
    bridge, usage = Bridge(call_tool, approve, question=question), Usage()
    agent = create_agent(
        model=chat_model,
        tools=bridge.tools(descriptions),
        system_prompt=system_prompt,
        middleware=[ModelCallLimitMiddleware(run_limit=MAX_MODEL_CALLS, exit_behavior="error")],
    )
    started, stopped = time.perf_counter(), ""
    try:
        state = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}, config={"callbacks": [usage]}
        )
        text = state["messages"][-1].text
    except ModelCallLimitExceededError:
        text, stopped = REFUSAL, f"stopped after {MAX_MODEL_CALLS} model calls without a final answer"
        log(f"STOPPED: {stopped}.")
    result = guard(read_answer(text), bridge.retrieved)
    return {
        "question": question,
        **result,
        "stopped": stopped,
        "searches": bridge.searches,
        "model_calls": usage.model_calls,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "latency_seconds": round(time.perf_counter() - started, 2),
        "tool_errors": bridge.tool_errors,
        "retrieved": sorted(bridge.retrieved),
        "trace": bridge.trace,
    }


# ---------------------------------------------------------------------------
# The cache, and the function evaluate.py calls
# ---------------------------------------------------------------------------


def prompt_version(prompt: str) -> str:
    """A short name for a prompt text: it changes whenever AGENTS.md does."""
    return hashlib.sha256(prompt.encode()).hexdigest()[:12]


def cache_key(question: str, setting: str, model: str, prompt: str) -> str:
    return hashlib.sha256(json.dumps([question, setting, model, prompt]).encode()).hexdigest()


def load_cache(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as file:
        return {entry["key"]: entry["record"] for entry in map(json.loads, file)}


def save_to_cache(path: Path, key: str, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps({"key": key, "record": record}, ensure_ascii=False) + "\n")


def gemini(model: str = MODEL):
    """The real chat model."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    from api_key import load_api_key

    # The retries are for the model's passing troubles: a per-minute limit, or "503 high demand".
    return ChatGoogleGenerativeAI(
        model=model, temperature=TEMPERATURE, google_api_key=load_api_key(), max_retries=3, timeout=REQUEST_TIMEOUT
    )


def causes(error: BaseException) -> list[BaseException]:
    """The errors inside an exception group, however deeply it is nested. The MCP client wraps failures this way."""
    if isinstance(error, BaseExceptionGroup):
        return [cause for inner in error.exceptions for cause in causes(inner)]
    return [error]


def saved_question_vectors() -> int:
    """How many question vectors are saved. One more after a run means one embedding was sent."""
    if not index.QUERY_EMBEDDINGS_FILE.is_file():
        return 0
    with index.QUERY_EMBEDDINGS_FILE.open(encoding="utf-8") as file:
        return sum(1 for _ in file)


async def answer(
    question: str,
    *,
    setting: str | None = None,
    model: str = MODEL,
    approve: Callable[[str], bool] = deny_all,
    cache_path: Path = CACHE_FILE,
    chat_model=None,
    server=corpus_server,
    timeout: float = QUESTION_TIMEOUT,
) -> dict:
    """The record of one question: from the cache if it was asked before, from the model otherwise.

    `chat_model` and `server` are there for tests; by default they are Gemini and server.py.
    """
    chosen = retrieval.read_setting(setting or os.environ.get(retrieval.SETTING_VARIABLE))
    setting = f"{chosen.mode}:{chosen.k}"
    prompt = AGENTS_FILE.read_text(encoding="utf-8")
    version = prompt_version(prompt)
    key = cache_key(question, setting, model, f"{HARNESS}:{version}")
    cached = load_cache(cache_path).get(key)
    if cached is not None:
        return cached | {"cached": True}

    chat_model = chat_model or gemini(model)
    before = saved_question_vectors()
    try:
        async with asyncio.timeout(timeout):
            async with server(setting) as (call_tool, descriptions):
                record = await run_question(question, chat_model, call_tool, descriptions, prompt, approve)
    except TimeoutError as error:
        raise TimeoutError(
            f"The agent did not finish within {timeout} s: the model or the corpus server stopped answering."
        ) from error
    except BaseExceptionGroup as group:  # raise what actually failed, so callers can tell a quota stop from a bug
        raise causes(group)[0] from group
    record |= {
        "model": model,
        "setting": setting,
        "prompt_version": version,
        "embeddings_sent": saved_question_vectors() - before,
    }
    if not record["tool_errors"]:  # a failed tool call (a quota stop, say) must be tried again, not remembered
        save_to_cache(cache_path, key, record)
    return record | {"cached": False}


def ask(question: str, **options) -> dict:
    """`answer`, for callers that are not async (evaluate.py)."""
    return asyncio.run(answer(question, **options))


# ---------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------


def render(record: dict) -> str:
    """One question's result for a person: the answer, its structure, and what it cost."""
    lines = [
        record["answer"],
        "",
        f"Citations: {', '.join(record['citations']) or 'none'}",
        f"Refused: {'yes' if record['refused'] else 'no'}",
        f"Not covered: {'; '.join(record['uncovered']) or 'nothing reported'}",
    ]
    if record["blocked"]:
        lines.append(f"Blocked by the citation guardrail (never retrieved): {', '.join(record['blocked'])}")
    if record["stopped"]:
        lines.append(f"Stopped: {record['stopped']}")
    lines += [
        "",
        f"Cost: {record['model_calls']} model calls, {record['input_tokens']:,} input and "
        f"{record['output_tokens']:,} output tokens, {record['searches']} searches, "
        f"{record['embeddings_sent']} embeddings sent, {record['latency_seconds']} s"
        + (" (from the cache: nothing was spent now)" if record["cached"] else ""),
        f"Model {record['model']}, retrieval {record['setting']}, prompt {record['prompt_version']}",
    ]
    return "\n".join(lines)


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        raise SystemExit('Give the question: uv run python main.py ask "your question"')
    try:
        record = ask(question, approve=terminal_approval)
    except Exception as error:  # still a failure (exit status 1), said in one line instead of a nested traceback
        raise SystemExit(f"The agent could not answer: {type(error).__name__}: {error}") from error
    print(render(record))


if __name__ == "__main__":
    main()
