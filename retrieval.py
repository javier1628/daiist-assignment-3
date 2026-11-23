"""
Retrieval over the saved search index: by vector alone, or by vector and
keywords fused. server.py and evaluate.py both use it.

Nothing in this file calls the API: the vector of the question is passed in,
and the keyword side is computed here from the stored chunk texts.
"""

import math
import os
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import index

# The one retrieval setting: "<mode>:<k>". The mode is how chunks are ranked
# (vector, or hybrid = vector and keywords fused) and k how many are returned.
# Set the CORPUS_RETRIEVAL environment variable to override it for one run.
DEFAULT_SETTING = "vector:5"
SETTING_VARIABLE = "CORPUS_RETRIEVAL"

CANDIDATES = 50  # how deep each ranking goes before the two are fused
RRF_K = 60  # the usual constant of reciprocal rank fusion
BM25_K1, BM25_B = 1.5, 0.75  # the usual BM25 settings

# Spanish words that say nothing about the topic, without accents because tokens are folded.
STOP_WORDS = frozenset(
    """
    a al algo alguna algunas alguno algunos ante antes aquel aquella aquellas aquellos asi aun aunque cada como con
    contra cual cuales cuando de del desde donde durante e el ella ellas ello ellos en entre era eran es esa esas ese
    eso esos esta estan estas este esto estos fue fueron ha han hasta hay la las le les lo los mas me mi mientras muy
    ni no nos o os otra otras otro otros para pero por porque que quien quienes se sea sean segun ser si sido sin
    sobre son su sus tambien tanto te tiene tienen toda todas todo todos tu tus u un una unas uno unos y ya
    """.split()
)


@dataclass(frozen=True)
class Setting:
    mode: str  # "vector" or "hybrid"
    k: int  # chunks returned


def read_setting(value: str | None) -> Setting:
    """Parse a setting such as "hybrid:5". None means the default."""
    match = re.fullmatch(r"(vector|hybrid):([1-9]\d*)", (DEFAULT_SETTING if value is None else value).strip())
    if match is None:
        raise ValueError(
            f"{SETTING_VARIABLE} must be a mode and a number of chunks, such as vector:5 or hybrid:5, not {value!r}."
        )
    return Setting(match.group(1), int(match.group(2)))


def current_setting() -> Setting:
    """The setting in force: the environment variable if it is set, the default otherwise."""
    return read_setting(os.environ.get(SETTING_VARIABLE))


def tokens(text: str) -> list[str]:
    """Words for keyword search: lower case, accents folded, stop words and single letters dropped."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    folded = "".join(character for character in decomposed if unicodedata.category(character) != "Mn")
    return [
        token
        for token in re.findall(r"[a-z0-9]+", folded)
        if token not in STOP_WORDS and (len(token) > 1 or token.isdigit())
    ]


class BM25:
    """Okapi BM25 over documents given as lists of tokens."""

    def __init__(self, documents: list[list[str]]):
        self.frequencies = [Counter(document) for document in documents]
        self.lengths = [len(document) for document in documents]
        self.average_length = sum(self.lengths) / len(documents)
        containing = Counter(token for frequencies in self.frequencies for token in frequencies)
        self.idf = {
            token: math.log(1 + (len(documents) - count + 0.5) / (count + 0.5)) for token, count in containing.items()
        }

    def score(self, query: list[str], position: int) -> float:
        frequencies = self.frequencies[position]
        norm = BM25_K1 * (1 - BM25_B + BM25_B * self.lengths[position] / self.average_length)
        return sum(
            self.idf[token] * frequencies[token] * (BM25_K1 + 1) / (frequencies[token] + norm)
            for token in set(query)
            if token in frequencies
        )

    def rank(self, query: list[str]) -> list[int]:
        """Positions of the documents that share a token with the query, best first."""
        scores = [(self.score(query, position), position) for position in range(len(self.lengths))]
        return [position for score, position in sorted(scores, key=lambda item: (-item[0], item[1])) if score > 0]


def fuse(rankings: list[list[str]]) -> list[str]:
    """Reciprocal rank fusion: each ranking gives an item 1 / (RRF_K + its rank); the sums decide the order."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            scores[item] = scores.get(item, 0.0) + 1 / (RRF_K + rank)
    return sorted(scores, key=lambda item: -scores[item])  # ties keep the order of the first ranking


class Retriever:
    """The chunks of a saved index, ready to be ranked for a question."""

    def __init__(self, collection):
        self.collection = collection
        stored = collection.get(include=["documents", "metadatas"])
        self.ids = list(stored["ids"])
        self.records = {
            chunk_id: {"id": chunk_id, "text": text, **metadata}
            for chunk_id, text, metadata in zip(stored["ids"], stored["documents"], stored["metadatas"])
        }
        # Keywords are matched against the same text the vectors were made from: heading and chunk.
        self.bm25 = BM25([tokens(self.records[chunk_id]["embedded_text"]) for chunk_id in self.ids])

    def by_vector(self, vector: Sequence[float], count: int) -> list[str]:
        found = index.nearest(self.collection, vector, min(count, len(self.ids)))
        return [result["id"] for result in found]

    def by_keywords(self, question: str, count: int) -> list[str]:
        return [self.ids[position] for position in self.bm25.rank(tokens(question))[:count]]

    def search(self, question: str, vector: Sequence[float], setting: Setting) -> list[dict]:
        """The setting's k best chunks for a question whose vector is given, best first."""
        if setting.mode == "vector":
            ids = self.by_vector(vector, setting.k)
        else:
            ids = fuse([self.by_vector(vector, CANDIDATES), self.by_keywords(question, CANDIDATES)])[: setting.k]
        return [self.records[chunk_id] for chunk_id in ids]


def format_results(results: list[dict]) -> str:
    """Each chunk as a numbered citation line followed by its text."""
    return "\n\n".join(
        f"[{number}] {index.citation(result)}\n{result['text']}" for number, result in enumerate(results, 1)
    )
