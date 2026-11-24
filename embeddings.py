"""
Gemini embeddings, each saved to disk as soon as it arrives, so that no text is
ever sent to the API twice. index.py uses this for the chunks and the questions.

Two facts about `gemini-embedding-2` shape this file. Both come from
https://ai.google.dev/gemini-api/docs/embeddings:

- It rejects the `task_type` field. The task goes in the text instead:
  `title: ... | text: ...` for a document, `task: search result | query: ...`
  for a question.
- Several plain strings in one request come back as a single merged vector.
  Each text has to travel in its own Content to get a vector of its own.
"""

import base64
import hashlib
import json
import os
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

MODEL = "gemini-embedding-2"
DIMENSION = 768  # of the 3,072 the model can return; it normalises the shorter vectors itself

MAX_TEXTS_PER_RUN = 960  # the free tier allows about 1,000 texts a day
SMOKE_TEXTS = 3  # size of the first batch of a run: a cheap check before the rest is sent
BATCH_SIZE = 10
TEXTS_PER_MINUTE = 60  # pacing between batches, set low because the free tier's per-minute limits are not published
TOKENS_PER_MINUTE = 20_000
CHARS_PER_TOKEN = 3  # low on purpose, so that tokens are over-estimated
MINUTE_LIMIT_RETRIES = 3
DEFAULT_RETRY_SECONDS = 60.0
REQUEST_TIMEOUT = 60  # seconds one embedding request may take; without it an unanswered request waits forever

Embed = Callable[[list[str]], list[list[float]]]  # texts -> one vector per text, in the same order


class QuotaStop(Exception):
    """The API refused on quota in a way that waiting a minute does not fix."""


@dataclass
class EmbedRun:
    sent: int  # texts sent to the API by this run
    saved: int  # of the distinct texts asked for, how many have a vector on disk now
    remaining: int  # and how many still have none
    stopped: str = ""  # why the run stopped before the end; empty when it finished


def document_prompt(title: str, text: str) -> str:
    """The text to embed for a document, in the format the model asks for."""
    return f"title: {title or 'none'} | text: {text}"


def query_prompt(question: str) -> str:
    """The text to embed for a question, in the format the model asks for."""
    return f"task: search result | query: {question}"


def cache_key(text: str, model: str = MODEL, dimension: int = DIMENSION) -> str:
    """What a vector is saved under: a hash of the embedded text, the model and the vector size."""
    return hashlib.sha256(f"{model}\n{dimension}\n{text}".encode()).hexdigest()


def load_cache(path: Path) -> dict[str, np.ndarray]:
    """Every vector saved in a cache file, by key. Reads the file only."""
    if not path.is_file():
        return {}
    cache = {}
    with path.open(encoding="utf-8") as file:
        for number, line in enumerate(file, 1):
            try:
                record = json.loads(line)
                cache[record["key"]] = np.frombuffer(base64.b64decode(record["vector"]), dtype="<f4")
            except (ValueError, KeyError) as error:
                raise ValueError(f"{path}, line {number} is not a saved embedding: {error!r}") from error
    return cache


def save_to_cache(path: Path, vectors: Mapping[str, Sequence[float]], model: str, dimension: int) -> None:
    """Append vectors to a cache file and force them onto the disk before returning."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "key": key,
                "model": model,
                "dimension": dimension,
                "vector": base64.b64encode(np.asarray(vector, dtype="<f4").tobytes()).decode("ascii"),
            }
        )
        + "\n"
        for key, vector in vectors.items()
    ]
    with path.open("a", encoding="utf-8") as file:
        file.write("".join(lines))
        file.flush()
        os.fsync(file.fileno())


def find_all(node, name: str) -> list:
    """Every value stored under `name`, at any depth of a parsed JSON body."""
    if isinstance(node, dict):
        return [value for key, value in node.items() if key == name] + [
            found for value in node.values() for found in find_all(value, name)
        ]
    if isinstance(node, list):
        return [found for item in node for found in find_all(item, name)]
    return []


def gemini_embedder(model: str = MODEL, dimension: int = DIMENSION, client=None, sleep=time.sleep) -> Embed:
    """The real embedder. Its client is created on the first call, so no API key is needed until a text is sent.

    A per-minute limit is waited out and the request sent again. Any other quota
    error, the daily limit above all, raises QuotaStop without another try.
    """
    from google.genai import errors, types

    def embed(texts: list[str]) -> list[list[float]]:
        nonlocal client
        if client is None:
            from google import genai

            from api_key import load_api_key

            client = genai.Client(
                api_key=load_api_key(), http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT * 1000)  # milliseconds
            )
        contents = [types.Content(parts=[types.Part.from_text(text=text)]) for text in texts]
        config = types.EmbedContentConfig(output_dimensionality=dimension)
        waits = 0
        while True:
            try:
                response = client.models.embed_content(model=model, contents=contents, config=config)
            except errors.ClientError as error:
                if error.code != 429:
                    raise
                quotas = [str(quota) for quota in find_all(error.details, "quotaId")]
                per_minute = bool(quotas) and all("PerMinute" in quota for quota in quotas)
                if not per_minute or waits == MINUTE_LIMIT_RETRIES:
                    raise QuotaStop(error.message) from error
                delays = find_all(error.details, "retryDelay")
                wait = float(str(delays[0]).rstrip("s")) if delays else DEFAULT_RETRY_SECONDS
                print(f"  per-minute limit reached; waiting {wait:.0f}s", file=sys.stderr, flush=True)
                sleep(wait)
                waits += 1
            else:
                return [list(embedding.values) for embedding in response.embeddings]

    return embed


def pause_seconds(texts: list[str]) -> float:
    """How long to wait after sending these texts to stay under both per-minute limits."""
    tokens = sum(len(text) for text in texts) / CHARS_PER_TOKEN
    return max(60 * len(texts) / TEXTS_PER_MINUTE, 60 * tokens / TOKENS_PER_MINUTE)


def embed_missing(
    texts: list[str],
    cache_path: Path,
    embed: Embed,
    *,
    model: str = MODEL,
    dimension: int = DIMENSION,
    max_texts: int = MAX_TEXTS_PER_RUN,
    batch_size: int = BATCH_SIZE,
    sleep: Callable[[float], None] = time.sleep,
) -> EmbedRun:
    """Embed every text that has no saved vector yet, saving each batch before the next is sent.

    The first batch is SMOKE_TEXTS texts. A batch whose answer has the wrong
    number of vectors or the wrong vector size is an error and is not saved. The
    run stops early, without an error, on a QuotaStop or after `max_texts` texts.
    """
    distinct = list(dict.fromkeys(texts))
    cache = load_cache(cache_path)
    pending = [text for text in distinct if cache_key(text, model, dimension) not in cache]
    total = len(pending)
    run = EmbedRun(sent=0, saved=len(distinct) - total, remaining=total)
    size = SMOKE_TEXTS
    while pending:
        room = max_texts - run.sent
        if room <= 0:
            run.stopped = f"this run reached its limit of {max_texts} texts"
            break
        batch = pending[: min(size, room)]
        try:
            vectors = embed(batch)
        except QuotaStop as stop:
            run.stopped = str(stop)
            break
        if len(vectors) != len(batch):
            raise ValueError(
                f"The model returned {len(vectors)} vectors for {len(batch)} texts. Nothing from this batch was saved."
            )
        wrong = [len(vector) for vector in vectors if len(vector) != dimension]
        if wrong:
            raise ValueError(
                f"The model returned a vector of {wrong[0]} values, not the {dimension} asked for. "
                "Nothing from this batch was saved."
            )
        save_to_cache(
            cache_path,
            {cache_key(text, model, dimension): vector for text, vector in zip(batch, vectors)},
            model,
            dimension,
        )
        pending = pending[len(batch) :]
        run.sent += len(batch)
        run.saved += len(batch)
        run.remaining -= len(batch)
        print(f"  sent {run.sent} of {total} texts", file=sys.stderr, flush=True)
        size = batch_size
        if pending and run.sent < max_texts:
            sleep(pause_seconds(batch))
    return run


def embed_query(
    question: str, cache_path: Path, embed: Embed, *, model: str = MODEL, dimension: int = DIMENSION
) -> np.ndarray:
    """The vector of a question. Only a question never asked before reaches the API."""
    text = query_prompt(question)
    run = embed_missing([text], cache_path, embed, model=model, dimension=dimension)
    if run.remaining:
        raise QuotaStop(run.stopped)
    return load_cache(cache_path)[cache_key(text, model, dimension)]
