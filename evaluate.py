"""
Assignment 3: evaluation (`main.py evaluate`).

Only the retrieval part is written: hit rate at 1, 3 and 5 over
eval/questions.csv, for vector and for hybrid retrieval. Agent answers, code
checks, the LLM judge and agreement with eval/human_labels.csv are not
written yet.

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
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import embeddings
import index
import retrieval

ROOT = Path(__file__).resolve().parent
QUESTIONS_FILE = ROOT / "eval" / "questions.csv"
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
            questions.append(Question(identifier, text, kind, expected))
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


def main() -> None:
    retriever = retrieval.Retriever(index.open_snapshot())
    known_sources = {record["source"] for record in retriever.records.values()} | set(index.DOCUMENTS)
    questions = read_questions(QUESTIONS_FILE, known_sources)
    answerable = [question for question in questions if question.kind != "unanswerable"]
    if not answerable:
        print(f"{QUESTIONS_FILE.relative_to(ROOT)} has no answerable questions yet, so there is no retrieval to evaluate.")
        return

    prompts = [embeddings.query_prompt(question.text) for question in answerable]
    run = embeddings.embed_missing(prompts, index.QUERY_EMBEDDINGS_FILE, embeddings.gemini_embedder())
    print(
        f"Question embeddings: {run.sent} sent to the API in this run, "
        f"{run.saved - run.sent} already saved, {run.remaining} remaining."
    )
    if run.remaining:
        print(f"STOPPED BEFORE THE END: {run.stopped}\nRun `uv run python main.py evaluate` again to send the rest.")
        return

    vectors = embeddings.load_cache(index.QUERY_EMBEDDINGS_FILE)

    def retrieve(question: str, mode: str) -> list[dict]:
        vector = vectors[embeddings.cache_key(embeddings.query_prompt(question))]
        return retriever.search(question, vector, retrieval.Setting(mode, max(KS)))

    print()
    print("\n".join(render(score_retrieval(questions, retrieve))))


if __name__ == "__main__":
    main()
