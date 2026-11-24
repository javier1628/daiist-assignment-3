"""
Assignment 3: evaluation (`main.py evaluate`).

Over eval/questions.csv it reports, in this order:

1. Retrieval: hit rate at 1, 3 and 5, for vector and for hybrid retrieval.
2. The agent's answer to every question, saved in eval/answers.jsonl, with
   what code can check: whether it refused when it should, whether its
   citations are valid, and whether it cites the expected article.
3. An LLM judge that grades each answer with the rubric in eval/rubric.md and
   the retrieved passages as evidence, saved in eval/verdicts.jsonl. It is
   skipped while the rubric is still the template.
4. Agreement between the judge and eval/human_labels.csv.

The printed report is also saved in eval/summary.md. Answers and verdicts
are cached, so a second run costs nothing for what did not change.

How eval/questions.csv is read:

- kind: `single`, `multi` or `unanswerable`.
- expected_source: the file name of the document, as in the chunk metadata
  (`ley-168-21.pdf`). Several are separated by `;`. Empty if unanswerable.
- expected_location: the article, as `Artículo 80` (or just `80`), or the
  ordinal in a document headed by ordinals (`PRIMERO`). Several are separated
  by `;` and paired with the sources in order; a single source serves every
  location. Empty if unanswerable.

Each answerable question costs one embedding the first time it is seen; the
vector is then saved in index/query_embeddings.jsonl.
"""

import csv
import hashlib
import json
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import agent
import embeddings
import index
import retrieval

ROOT = Path(__file__).resolve().parent
QUESTIONS_FILE = ROOT / "eval" / "questions.csv"
ANSWERS_FILE = ROOT / "eval" / "answers.jsonl"  # the agent's record for every question
RUBRIC_FILE = ROOT / "eval" / "rubric.md"
VERDICTS_FILE = ROOT / "eval" / "verdicts.jsonl"  # the judge's grades
JUDGE_CACHE_FILE = ROOT / "eval" / "judge_cache.jsonl"
HUMAN_LABELS_FILE = ROOT / "eval" / "human_labels.csv"
SUMMARY_FILE = ROOT / "eval" / "summary.md"
# The same model as the agent, only because it was the one free model answering reliably when this was built
# (see agent.MODEL). A judge that is a different model is better practice: change this when one is reachable.
# Verdicts are cached by model, so changing it asks for every verdict again.
JUDGE_MODEL = "gemini-3.5-flash-lite"
RUBRIC_NOT_WRITTEN = "TODO"  # while the rubric holds this word, it is still the template
GRADES = ("correct", "supported")  # what the judge and eval/human_labels.csv both grade, as 1 or 0
KINDS = ("single", "multi", "unanswerable")
MODES = ("vector", "hybrid")
KS = (1, 3, 5)
ARTICLE = re.compile(r"(?:art(?:[íi]culo|\.)?\s*)?(\d+)", re.IGNORECASE)

Passage = tuple[str, int]  # (source file, article number)


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    kind: str
    expected: tuple[Passage, ...]  # empty for an unanswerable question
    reference: str = ""  # the reference answer


def parse_location(location: str) -> int:
    """The article number written in an expected_location: "Artículo 80", "80" or an ordinal."""
    match = ARTICLE.fullmatch(location)
    if match:
        return int(match.group(1))
    if location.upper() in index.ORDINALS:
        return index.ORDINALS[location.upper()]
    raise ValueError(f"expected_location {location!r} is not an article such as 'Artículo 80' or an ordinal such as 'PRIMERO'")


def parse_expected(sources: str, locations: str, known_sources: set[str]) -> tuple[Passage, ...]:
    """The passages a question expects, from its expected_source and expected_location cells."""
    source_list = [source.strip() for source in sources.split(";") if source.strip()]
    location_list = [location.strip() for location in locations.split(";") if location.strip()]
    if not source_list or not location_list:
        raise ValueError("an answerable question needs both an expected_source and an expected_location")
    if len(source_list) == 1:
        source_list = source_list * len(location_list)
    if len(source_list) != len(location_list):
        raise ValueError(
            f"{len(source_list)} sources for {len(location_list)} locations; write one source for all, or one each"
        )
    for source in source_list:
        if source not in known_sources:
            raise ValueError(f"expected_source {source!r} is not a document of the index ({', '.join(sorted(known_sources))})")
    return tuple((source, parse_location(location)) for source, location in zip(source_list, location_list))


def read_questions(path: Path, known_sources: set[str]) -> list[Question]:
    """The questions of the test set. A row that breaks the format is an error naming its id."""
    questions = []
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            text = (row.get("question") or "").strip()
            if not text:
                continue
            identifier, kind = row["id"].strip(), row["kind"].strip().lower()
            sources, locations = row["expected_source"].strip(), row["expected_location"].strip()
            try:
                if kind not in KINDS:
                    raise ValueError(f"kind {kind!r} is not one of {', '.join(KINDS)}")
                if kind == "unanswerable":
                    if sources or locations:
                        raise ValueError("an unanswerable question must leave expected_source and expected_location empty")
                    expected: tuple[Passage, ...] = ()
                else:
                    expected = parse_expected(sources, locations, known_sources)
            except ValueError as error:
                raise ValueError(f"{path.name}, question {identifier}: {error}.") from error
            questions.append(Question(identifier, text, kind, expected, (row.get("reference_answer") or "").strip()))
    return questions


def score_retrieval(questions: list[Question], retrieve: Callable[[str, str], list[dict]]) -> dict:
    """Count hits at each k for each mode. `retrieve(question, mode)` returns the top chunks, best first.

    A passage is found at k when one of the top k chunks comes from its document
    and article. A question is a hit when at least one of its passages is found.
    Unanswerable questions are skipped.
    """
    answerable = [question for question in questions if question.kind != "unanswerable"]
    groups = {name: Counter() for name in ["all", *dict.fromkeys(question.kind for question in answerable)]}
    several: Counter = Counter()  # questions that expect two or more passages
    for question in answerable:
        for name in ("all", question.kind):
            groups[name]["n"] += 1
        if len(question.expected) > 1:
            several["n"] += 1
        for mode in MODES:
            results = retrieve(question.text, mode)
            for k in KS:
                top = {(result["source"], result["article"]) for result in results[:k]}
                found = [passage in top for passage in question.expected]
                for name in ("all", question.kind):
                    groups[name][mode, k] += any(found)
                if len(question.expected) > 1:
                    several[mode, k, "any"] += any(found)
                    several[mode, k, "all"] += all(found)
    return {"skipped": len(questions) - len(answerable), "groups": groups, "several": several}


def share(hits: int, total: int) -> str:
    return f"{hits}/{total} ({hits / total:.0%})"


def render(scores: dict) -> list[str]:
    """The hit rates as text tables."""
    total = scores["groups"]["all"]["n"]
    lines = [
        f"Retrieval hit rate over {total} answerable questions ({scores['skipped']} unanswerable skipped).",
        "A question is a hit at k when a chunk of an expected document and article is among the top k.",
        "",
        f"{'questions':<12}{'n':>4}  " + "  ".join(f"{f'{mode} @{k}':>14}" for mode in MODES for k in KS),
    ]
    for name, counts in scores["groups"].items():
        lines.append(
            f"{name:<12}{counts['n']:>4}  "
            + "  ".join(f"{share(counts[mode, k], counts['n']):>14}" for mode in MODES for k in KS)
        )
    several = scores["several"]
    lines += ["", f"Questions that expect two or more passages: {several['n']}."]
    if several["n"]:
        lines.append(f"{'mode':<8}{'k':>3}  {'at least one found':>20}  {'all found':>14}")
        for mode in MODES:
            for k in KS:
                lines.append(
                    f"{mode:<8}{k:>3}  {share(several[mode, k, 'any'], several['n']):>20}  "
                    f"{share(several[mode, k, 'all'], several['n']):>14}"
                )
    return lines


# ---------------------------------------------------------------------------
# The agent's answers, and what code can check about them
# ---------------------------------------------------------------------------


def is_quota_error(error: Exception) -> bool:
    """A quota limit, or the model being unavailable or silent for now: reasons to stop and try again later, not bugs."""
    return isinstance(error, TimeoutError) or any(
        sign in str(error) for sign in ("RESOURCE_EXHAUSTED", "429", "UNAVAILABLE", "503")
    )


def run_agent(questions: list[Question], ask: Callable[[str], dict], answers_path: Path) -> list[dict]:
    """Ask the agent every question, saving the answers so far after each one.

    A quota error, or the model being unavailable, stops the run without an
    error: what was answered is saved and cached, and the next run only asks
    the rest. Any other error is raised.
    """
    rows: list[dict] = []
    for position, question in enumerate(questions, 1):
        try:
            record = ask(question.text)
        except Exception as error:
            if not is_quota_error(error):
                raise
            print(
                f"STOPPED BEFORE THE END: the model refused or was unavailable at question {question.id}.\n{error}\n"
                f"{len(rows)} of {len(questions)} questions are answered and saved. Run the evaluation again to ask the rest."
            )
            break
        rows.append({"id": question.id, "kind": question.kind, **record})
        answers_path.parent.mkdir(parents=True, exist_ok=True)
        answers_path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
        )
        print(
            f"  {position}/{len(questions)} {question.id}: {'refused' if record['refused'] else 'answered'}, "
            f"{record['model_calls']} model calls, {record['searches']} searches"
            + (" (cached)" if record.get("cached") else ""),
            flush=True,
        )
    return rows


def check_answer(question: Question, record: dict) -> dict:
    """What code can tell about one answer.

    - refusal_ok: an unanswerable question was refused, any other was not.
    - citations_valid: nothing was blocked, every citation was among the
      retrieved chunks, and an answer that is not a refusal cites something.
    - expected_cited / all_expected_cited: one / every expected article is
      among the citations. None for an unanswerable question.
    """
    expected = [index.citation_tag(source, number) for source, number in question.expected]
    found = [tag in record["citations"] for tag in expected]
    return {
        "refusal_ok": record["refused"] == (question.kind == "unanswerable"),
        "citations_valid": (
            not record["blocked"]
            and all(tag in record["retrieved"] for tag in record["citations"])
            and (record["refused"] or bool(record["citations"]))
        ),
        "expected_cited": any(found) if expected else None,
        "all_expected_cited": all(found) if expected else None,
    }


def render_answers(questions: list[Question], rows: list[dict]) -> list[str]:
    """The code checks and the cost of the agent's answers, as text."""
    by_id = {question.id: question for question in questions}
    checks = {row["id"]: check_answer(by_id[row["id"]], row) for row in rows}
    lines = [f"Agent answers: {len(rows)} of {len(questions)} questions, saved in {ANSWERS_FILE.relative_to(ROOT)}.", ""]
    for name, groups in (
        ("refused when it should, and only then", ("unanswerable", "single", "multi")),
        ("citations valid", ("unanswerable", "single", "multi")),
        ("cites an expected article", ("single", "multi")),
        ("cites every expected article", ("multi",)),
    ):
        key = {
            "refused when it should, and only then": "refusal_ok",
            "citations valid": "citations_valid",
            "cites an expected article": "expected_cited",
            "cites every expected article": "all_expected_cited",
        }[name]
        chosen = [row for row in rows if row["kind"] in groups]
        if not chosen:
            continue
        parts = [f"all {share(sum(bool(checks[row['id']][key]) for row in chosen), len(chosen))}"]
        for kind in groups:
            of_kind = [row for row in chosen if row["kind"] == kind]
            if of_kind and len(groups) > 1:
                parts.append(f"{kind} {share(sum(bool(checks[row['id']][key]) for row in of_kind), len(of_kind))}")
        lines.append(f"{name + ':':<40}" + ", ".join(parts))
    failed = [
        f"{row['id']} ({', '.join(name for name, passed in checks[row['id']].items() if passed is False)})"
        for row in rows
        if any(passed is False for passed in checks[row["id"]].values())
    ]
    blocked = [row["id"] for row in rows if row["blocked"]]
    fresh = [row for row in rows if not row.get("cached")]
    lines += [
        f"Questions failing a check: {', '.join(failed) or 'none'}",
        f"Answers blocked by the citation guardrail: {', '.join(blocked) or 'none'}",
        "",
        f"Cost of the {len(rows)} answers: {sum(row['model_calls'] for row in rows)} model calls, "
        f"{sum(row['input_tokens'] for row in rows):,} input and {sum(row['output_tokens'] for row in rows):,} output "
        f"tokens, {sum(row['searches'] for row in rows)} searches, "
        f"{sum(row['embeddings_sent'] for row in rows)} search embeddings sent.",
        f"Per question: {sum(row['input_tokens'] + row['output_tokens'] for row in rows) / len(rows):,.0f} tokens and "
        f"{sum(row['latency_seconds'] for row in rows) / len(rows):.1f} s on average."
        if rows
        else "No answers.",
        f"Spent in this run: {sum(row['model_calls'] for row in fresh)} model calls for {len(fresh)} questions; "
        f"the other {len(rows) - len(fresh)} came from the cache.",
    ]
    return lines


# ---------------------------------------------------------------------------
# The LLM judge
# ---------------------------------------------------------------------------


def rubric_is_written(rubric: str) -> bool:
    """False for an empty rubric and for the template, which still says TODO."""
    return bool(rubric.strip()) and RUBRIC_NOT_WRITTEN not in rubric


def judge_prompt(rubric: str, question: Question, row: dict) -> str:
    """Everything the judge reads for one answer."""
    passages = "\n\n".join(step["result"] for step in row["trace"] if step["tool"] == "search" and step["ran"])
    return "\n".join([
        "You are grading one answer of an assistant that answers questions about the customs legislation of the",
        "Dominican Republic using only passages it retrieved. Grade it with the rubric. Judge from the rubric, the",
        "reference answer and the retrieved passages alone, not from what you know about the law.",
        "",
        "# Rubric",
        rubric.strip(),
        "",
        f"# Kind of question\n{question.kind}",
        "",
        f"# Question\n{question.text}",
        "",
        f"# Reference answer\n{question.reference}",
        "",
        f"# The assistant's answer\n{row['answer']}",
        "",
        f"# Passages the assistant retrieved\n{passages or '(it retrieved nothing)'}",
        "",
        "# What to return",
        'A JSON object with exactly these fields: "correct" (1 or 0), "supported" (1 or 0) and "reason" (one or two',
        "sentences explaining both grades).",
    ])


def judge(question: Question, row: dict, rubric: str, generate: Callable[[str], str]) -> dict:
    """One answer graded by the judge. `generate` sends a prompt to the judge model and returns its text."""
    reply = generate(judge_prompt(rubric, question, row))
    try:
        data = json.loads(reply)
        grades = {name: data[name] for name in GRADES}
        if any(grade not in (0, 1) or isinstance(grade, bool) for grade in grades.values()):
            raise ValueError("a grade is not 0 or 1")
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(
            f"The judge's reply for question {row['id']} is not two grades of 0 or 1 ({error!r}): {reply[:300]!r}"
        ) from error
    return {"id": row["id"], **grades, "reason": str(data.get("reason", ""))}


def gemini_judge(model: str = JUDGE_MODEL) -> Callable[[str], str]:
    """The real judge: one request per answer, temperature 0, a JSON reply."""
    from google import genai
    from google.genai import types

    from api_key import load_api_key

    # The retries are for the model's passing troubles: a per-minute limit, or "503 high demand".
    retries = types.HttpRetryOptions(attempts=3, http_status_codes=[429, 503])
    options = types.HttpOptions(retry_options=retries, timeout=agent.REQUEST_TIMEOUT * 1000)  # milliseconds
    client = genai.Client(api_key=load_api_key(), http_options=options)
    config = types.GenerateContentConfig(
        temperature=0,
        response_mime_type="application/json",
        response_schema={
            "type": "OBJECT",
            "properties": {
                "correct": {"type": "INTEGER"},
                "supported": {"type": "INTEGER"},
                "reason": {"type": "STRING"},
            },
            "required": ["correct", "supported", "reason"],
        },
    )

    def generate(prompt: str) -> str:
        return client.models.generate_content(model=model, contents=prompt, config=config).text

    return generate


def judge_all(
    questions: list[Question], rows: list[dict], rubric: str, generate: Callable[[str], str], cache_path: Path, model: str
) -> list[dict]:
    """A verdict for every answer. One already given for the same model, rubric, answer and passages is reused."""
    by_id = {question.id: question for question in questions}
    cache = agent.load_cache(cache_path)
    verdicts = []
    for row in rows:
        question = by_id[row["id"]]
        key = hashlib.sha256(f"{model}\n{judge_prompt(rubric, question, row)}".encode()).hexdigest()
        if key not in cache:
            cache[key] = judge(question, row, rubric, generate)
            agent.save_to_cache(cache_path, key, cache[key])
        verdicts.append(cache[key])
    return verdicts


# ---------------------------------------------------------------------------
# Agreement with the human labels
# ---------------------------------------------------------------------------


def read_human_labels(path: Path) -> dict[str, dict]:
    """The grades in eval/human_labels.csv: question id -> {"correct": 0 or 1, "supported": 0 or 1}."""
    labels = {}
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            identifier = (row.get("id") or "").strip()
            if not identifier:
                continue
            values = {name: (row.get(name) or "").strip() for name in GRADES}
            if any(value not in ("0", "1") for value in values.values()):
                raise ValueError(f"{path.name}, question {identifier}: correct and supported must each be 0 or 1, not {values}.")
            labels[identifier] = {name: int(value) for name, value in values.items()}
    return labels


def agreement(human: dict[str, dict], verdicts: list[dict]) -> dict:
    """For each grade, how often the judge and the human agree on the questions both graded, and Cohen's kappa.

    Kappa is agreement beyond what chance would give; it is None when chance
    alone already explains all of it (both always gave the same grade).
    """
    result = {}
    for name in GRADES:
        pairs = [(verdict["id"], human[verdict["id"]][name], verdict[name]) for verdict in verdicts if verdict["id"] in human]
        count = len(pairs)
        agree = sum(mine == theirs for _, mine, theirs in pairs)
        entry = {
            "n": count,
            "agree": agree,
            "kappa": None,
            "human_1_judge_0": sum(mine == 1 and theirs == 0 for _, mine, theirs in pairs),
            "human_0_judge_1": sum(mine == 0 and theirs == 1 for _, mine, theirs in pairs),
            "disagreements": sorted(identifier for identifier, mine, theirs in pairs if mine != theirs),
        }
        if count:
            human_ones = sum(mine for _, mine, _ in pairs) / count
            judge_ones = sum(theirs for _, _, theirs in pairs) / count
            chance = human_ones * judge_ones + (1 - human_ones) * (1 - judge_ones)
            if chance < 1:
                entry["kappa"] = round((agree / count - chance) / (1 - chance), 3)
        result[name] = entry
    return result


def render_agreement(result: dict) -> list[str]:
    lines = ["Agreement between the judge and eval/human_labels.csv, on the questions both graded:"]
    for name, entry in result.items():
        if not entry["n"]:
            lines.append(f"  {name}: no question graded by both.")
            continue
        kappa = "not defined (no variation)" if entry["kappa"] is None else f"{entry['kappa']:.3f}"
        lines.append(
            f"  {name}: {share(entry['agree'], entry['n'])} agree, Cohen's kappa {kappa}. "
            f"Human 1 and judge 0: {entry['human_1_judge_0']}; human 0 and judge 1: {entry['human_0_judge_1']}. "
            f"Disagreements: {', '.join(entry['disagreements']) or 'none'}."
        )
    return lines


# ---------------------------------------------------------------------------
# The stage
# ---------------------------------------------------------------------------


def main() -> None:
    retriever = retrieval.Retriever(index.open_snapshot())
    known_sources = {record["source"] for record in retriever.records.values()} | set(index.DOCUMENTS)
    questions = read_questions(QUESTIONS_FILE, known_sources)
    if not questions:
        print(f"{QUESTIONS_FILE.relative_to(ROOT)} has no questions yet, so there is nothing to evaluate.")
        return
    report: list[str] = []

    def say(*lines: str) -> None:
        report.extend(lines)
        print("\n".join(lines), flush=True)

    def finish() -> None:
        SUMMARY_FILE.write_text("# Evaluation summary\n\n```text\n" + "\n".join(report) + "\n```\n", encoding="utf-8")
        print(f"\nWrote {SUMMARY_FILE.relative_to(ROOT)}")

    # 1. Retrieval
    answerable = [question for question in questions if question.kind != "unanswerable"]
    if answerable:
        prompts = [embeddings.query_prompt(question.text) for question in answerable]
        run = embeddings.embed_missing(prompts, index.QUERY_EMBEDDINGS_FILE, embeddings.gemini_embedder())
        say(
            f"Question embeddings: {run.sent} sent to the API in this run, "
            f"{run.saved - run.sent} already saved, {run.remaining} remaining."
        )
        if run.remaining:
            say(f"STOPPED BEFORE THE END: {run.stopped}", "Run `uv run python main.py evaluate` again to send the rest.")
            finish()
            return
        vectors = embeddings.load_cache(index.QUERY_EMBEDDINGS_FILE)

        def retrieve(question: str, mode: str) -> list[dict]:
            vector = vectors[embeddings.cache_key(embeddings.query_prompt(question))]
            return retriever.search(question, vector, retrieval.Setting(mode, max(KS)))

        say("", *render(score_retrieval(questions, retrieve)))

    # 2. The agent on every question, and the checks code can do
    say("", f"Asking the agent ({agent.MODEL}, retrieval {retrieval.current_setting().mode}:{retrieval.current_setting().k}) ...")
    rows = run_agent(questions, lambda text: agent.ask(text, approve=agent.deny_all), ANSWERS_FILE)
    if rows:
        say("", *render_answers(questions, rows))
    if len(rows) < len(questions):
        say("", f"The agent answered {len(rows)} of {len(questions)} questions, so the judge was not run.")
        finish()
        return

    # 3. The judge, and 4. its agreement with the human labels
    rubric = RUBRIC_FILE.read_text(encoding="utf-8") if RUBRIC_FILE.is_file() else ""
    if not rubric_is_written(rubric):
        say("", f"LLM judge: skipped. {RUBRIC_FILE.relative_to(ROOT)} is still the template; write the rubric to run it.")
        finish()
        return
    try:
        verdicts = judge_all(questions, rows, rubric, gemini_judge(), JUDGE_CACHE_FILE, JUDGE_MODEL)
    except Exception as error:
        if not is_quota_error(error):
            raise
        say(
            "",
            f"LLM judge ({JUDGE_MODEL}): STOPPED BEFORE THE END, the model refused or was unavailable.",
            str(error),
            "The verdicts already given are cached. Run the evaluation again to ask for the rest.",
        )
        finish()
        return
    VERDICTS_FILE.write_text("".join(json.dumps(verdict, ensure_ascii=False) + "\n" for verdict in verdicts), encoding="utf-8")
    say(
        "",
        f"LLM judge ({JUDGE_MODEL}), saved in {VERDICTS_FILE.relative_to(ROOT)}:",
        *[f"  {name}: {share(sum(verdict[name] for verdict in verdicts), len(verdicts))}" for name in GRADES],
    )
    labels = read_human_labels(HUMAN_LABELS_FILE) if HUMAN_LABELS_FILE.is_file() else {}
    if labels:
        say("", *render_agreement(agreement(labels, verdicts)))
    else:
        say("", f"Agreement: {HUMAN_LABELS_FILE.relative_to(ROOT)} has no grades yet.")
    finish()


if __name__ == "__main__":
    main()
