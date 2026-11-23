"""Embedding with a cache on disk. The embedder and the API client here are fakes: no test calls the Gemini API."""

import pytest
from google.genai import errors, types

import embeddings
from embeddings import (
    QuotaStop,
    cache_key,
    document_prompt,
    embed_missing,
    embed_query,
    gemini_embedder,
    load_cache,
    pause_seconds,
    query_prompt,
)

DIM = 4
PER_DAY = "EmbedContentRequestsPerDayPerUserPerProjectPerModel-FreeTier"
PER_MINUTE = "EmbedContentRequestsPerMinutePerUserPerProjectPerModel-FreeTier"


class FakeEmbedder:
    """Returns one vector per text and records every batch it is sent."""

    def __init__(self, stop_on_call: int | None = None, dimension: int = DIM):
        self.batches: list[list[str]] = []
        self.stop_on_call = stop_on_call
        self.dimension = dimension

    def __call__(self, texts: list[str]) -> list[list[float]]:
        if self.stop_on_call == len(self.batches) + 1:
            raise QuotaStop("daily quota reached")
        self.batches.append(list(texts))
        return [[float(len(text)), 0.5, -1.5, 2.0][: self.dimension] for text in texts]

    @property
    def sent(self) -> list[str]:
        return [text for batch in self.batches for text in batch]


def run(texts, path, embedder, **options):
    return embed_missing(texts, path, embedder, dimension=DIM, sleep=lambda seconds: None, **options)


def numbered(count: int) -> list[str]:
    return [f"texto {n}" for n in range(count)]


def test_document_and_query_texts_follow_the_format_the_model_asks_for():
    assert (
        document_prompt("Ley 168-21 de Aduanas — Artículo 5", "Artículo 5.- Territorio aduanero.")
        == "title: Ley 168-21 de Aduanas — Artículo 5 | text: Artículo 5.- Territorio aduanero."
    )
    assert document_prompt("", "Texto.") == "title: none | text: Texto."
    assert query_prompt("¿Qué es el aforo?") == "task: search result | query: ¿Qué es el aforo?"


def test_every_text_is_embedded_once_and_a_rerun_sends_nothing(tmp_path):
    path, texts = tmp_path / "embeddings.jsonl", numbered(8)

    first = FakeEmbedder()
    result = run(texts, path, first)
    second = FakeEmbedder()
    again = run(texts, path, second)

    assert sorted(first.sent) == sorted(texts)
    assert (result.sent, result.saved, result.remaining, result.stopped) == (8, 8, 0, "")
    assert second.batches == []
    assert (again.sent, again.saved, again.remaining, again.stopped) == (0, 8, 0, "")


def test_only_texts_without_a_saved_vector_are_sent(tmp_path):
    path = tmp_path / "embeddings.jsonl"
    run(["a", "b"], path, FakeEmbedder())

    embedder = FakeEmbedder()
    run(["a", "b", "c"], path, embedder)

    assert embedder.batches == [["c"]]


def test_a_text_that_appears_twice_is_sent_once(tmp_path):
    embedder = FakeEmbedder()

    result = run(["a", "b", "a"], tmp_path / "embeddings.jsonl", embedder)

    assert embedder.batches == [["a", "b"]]
    assert (result.sent, result.saved, result.remaining) == (2, 2, 0)


def test_the_first_batch_is_three_texts_and_each_batch_is_on_disk_before_the_next_is_sent(tmp_path):
    path = tmp_path / "embeddings.jsonl"
    saved_before_each_call = []

    class Watching(FakeEmbedder):
        def __call__(self, texts):
            saved_before_each_call.append(len(load_cache(path)))
            return super().__call__(texts)

    embedder = Watching()
    run(numbered(8), path, embedder, batch_size=4)

    assert [len(batch) for batch in embedder.batches] == [3, 4, 1]
    assert saved_before_each_call == [0, 3, 7]


def test_a_quota_stop_keeps_what_was_saved_and_reports_what_remains(tmp_path):
    path, texts = tmp_path / "embeddings.jsonl", numbered(8)

    result = run(texts, path, FakeEmbedder(stop_on_call=2), batch_size=4)
    resumed = FakeEmbedder()
    after = run(texts, path, resumed, batch_size=4)

    assert (result.sent, result.saved, result.remaining) == (3, 3, 5)
    assert result.stopped == "daily quota reached"
    assert sorted(resumed.sent) == sorted(texts[3:])
    assert (after.sent, after.saved, after.remaining) == (5, 8, 0)


def test_a_run_never_sends_more_texts_than_its_cap(tmp_path):
    embedder = FakeEmbedder()

    result = run(numbered(8), tmp_path / "embeddings.jsonl", embedder, batch_size=4, max_texts=5)

    assert [len(batch) for batch in embedder.batches] == [3, 2]
    assert (result.sent, result.saved, result.remaining) == (5, 5, 3)
    assert "limit of 5 texts" in result.stopped


def test_vectors_of_the_wrong_size_are_an_error_and_are_not_saved(tmp_path):
    path = tmp_path / "embeddings.jsonl"

    with pytest.raises(ValueError, match="3 values"):
        run(["a", "b"], path, FakeEmbedder(dimension=3))

    assert load_cache(path) == {}


def test_fewer_vectors_than_texts_is_an_error_and_nothing_is_saved(tmp_path):
    path = tmp_path / "embeddings.jsonl"

    def merged(texts):  # what the model answers when several texts are sent as one input
        return [[1.0, 2.0, 3.0, 4.0]]

    with pytest.raises(ValueError, match="1 vectors for 2 texts"):
        run(["a", "b"], path, merged)

    assert load_cache(path) == {}


def test_a_saved_vector_comes_back_under_a_key_of_its_text_model_and_dimension(tmp_path):
    path = tmp_path / "embeddings.jsonl"
    run(["abc"], path, FakeEmbedder())

    cache = load_cache(path)

    assert list(cache) == [cache_key("abc", embeddings.MODEL, DIM)]
    assert cache[cache_key("abc", embeddings.MODEL, DIM)].tolist() == [3.0, 0.5, -1.5, 2.0]
    assert cache_key("abc", "another-model", DIM) != cache_key("abc", embeddings.MODEL, DIM)
    assert cache_key("abc", embeddings.MODEL, 8) != cache_key("abc", embeddings.MODEL, DIM)


def test_the_run_pauses_between_batches_but_not_after_the_last(tmp_path):
    pauses = []

    embed_missing(
        numbered(8), tmp_path / "embeddings.jsonl", FakeEmbedder(), dimension=DIM, batch_size=4, sleep=pauses.append
    )

    assert pauses == [3.0, 4.0]  # 3 and 4 short texts at 60 texts a minute


def test_the_pause_after_a_batch_keeps_texts_and_tokens_under_the_per_minute_limits():
    assert pause_seconds(["x" * 30] * 10) == 10.0  # 10 texts at 60 a minute; their 100 estimated tokens need less
    assert pause_seconds(["x" * 6000] * 2) == 12.0  # 4,000 estimated tokens at 20,000 a minute


def test_a_question_is_embedded_with_the_query_format_and_only_the_first_time(tmp_path):
    path, embedder = tmp_path / "query_embeddings.jsonl", FakeEmbedder()

    first = embed_query("¿Qué es el aforo?", path, embedder, dimension=DIM)
    second = embed_query("¿Qué es el aforo?", path, embedder, dimension=DIM)

    assert embedder.batches == [["task: search result | query: ¿Qué es el aforo?"]]
    assert first.tolist() == second.tolist() == [46.0, 0.5, -1.5, 2.0]


def test_a_question_that_cannot_be_embedded_is_an_error(tmp_path):
    with pytest.raises(QuotaStop, match="daily quota reached"):
        embed_query("¿Qué es el aforo?", tmp_path / "q.jsonl", FakeEmbedder(stop_on_call=1), dimension=DIM)


# --- the real embedder, against a fake API client ---------------------------


class FakeClient:
    """Stands in for genai.Client: answers embed_content with the outcomes it was given, in order."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests = []
        self.models = self

    def embed_content(self, *, model, contents, config):
        self.requests.append((model, contents, config))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return types.EmbedContentResponse(embeddings=[types.ContentEmbedding(values=values) for values in outcome])


def quota_error(quota_id: str) -> errors.ClientError:
    """A 429 shaped like the Gemini API's, naming the quota that was exceeded."""
    return errors.ClientError(
        429,
        {
            "error": {
                "code": 429,
                "message": "You exceeded your current quota, please check your plan and billing details.",
                "status": "RESOURCE_EXHAUSTED",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                        "violations": [{"quotaId": quota_id, "quotaValue": "1000"}],
                    },
                    {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "34s"},
                ],
            }
        },
    )


def no_waiting(seconds):
    raise AssertionError(f"waited {seconds}s")


def test_each_text_goes_in_its_own_content_so_the_model_returns_one_vector_per_text():
    client = FakeClient([[1.0, 0.0], [0.0, 1.0]])

    vectors = gemini_embedder(dimension=2, client=client)(["uno", "dos"])

    model, contents, config = client.requests[0]
    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert model == "gemini-embedding-2"
    assert [[part.text for part in content.parts] for content in contents] == [["uno"], ["dos"]]
    assert config.output_dimensionality == 2
    assert config.task_type is None  # this model rejects task_type; the task goes in the text


def test_a_per_minute_limit_waits_as_long_as_the_api_asks_and_tries_again():
    client = FakeClient(quota_error(PER_MINUTE), [[1.0, 0.0]])
    waits = []

    vectors = gemini_embedder(dimension=2, client=client, sleep=waits.append)(["uno"])

    assert vectors == [[1.0, 0.0]]
    assert waits == [34.0]
    assert len(client.requests) == 2


def test_a_daily_quota_error_stops_without_trying_again():
    client = FakeClient(quota_error(PER_DAY))

    with pytest.raises(QuotaStop, match="exceeded your current quota"):
        gemini_embedder(dimension=2, client=client, sleep=no_waiting)(["uno"])

    assert len(client.requests) == 1


def test_a_quota_error_that_names_no_period_stops_too():
    body = {"error": {"code": 429, "message": "Resource has been exhausted.", "status": "RESOURCE_EXHAUSTED"}}
    client = FakeClient(errors.ClientError(429, body))

    with pytest.raises(QuotaStop, match="Resource has been exhausted"):
        gemini_embedder(dimension=2, client=client, sleep=no_waiting)(["uno"])

    assert len(client.requests) == 1


def test_any_other_api_error_is_raised_as_it_is():
    body = {"error": {"code": 400, "message": "Invalid argument.", "status": "INVALID_ARGUMENT"}}
    client = FakeClient(errors.ClientError(400, body))

    with pytest.raises(errors.ClientError, match="INVALID_ARGUMENT"):
        gemini_embedder(dimension=2, client=client, sleep=no_waiting)(["uno"])
